from fastapi import APIRouter, HTTPException, Request, Depends, Query
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, timedelta, datetime
import json
import os

from auth_middleware import verify_token
import firestore_manager as db_manager
import firestore_garmin_metrics
import ai_coach
from ai_chat_manager import chat_manager
import scripts.predict_readiness as predictor
from logger import logger

router = APIRouter(prefix="", tags=["AI"])

limiter = Limiter(key_func=get_remote_address)


class PlanGenerationRequest(BaseModel):
    days: int = 1
    rejected_plan_details: Optional[dict] = None


class ChatRequest(BaseModel):
    message: str
    history: List[dict]  # [{"role": "user", "content": "..."}, ...]


async def _get_metrics_history_internal(uid: str, days: int = 90):
    """Internal helper to fetch metrics history for a user."""
    try:
        metrics = firestore_garmin_metrics.get_user_daily_metrics(uid, days=days)

        result = []
        for row in metrics:
            load_val = row.get('load_estimate')
            if load_val is None:
                load_val = row.get('workout_calories', 0)
                if load_val > 200:
                    load_val = load_val * 0.1

            result.append({
                "date": row.get('date'),
                "ctl": round(row.get('CTL', 0), 1),
                "atl": round(row.get('ATL', 0), 1),
                "tsb": round(row.get('TSB', 0), 1),
                "load": int(load_val),
                "readiness": int(row.get('bodyBatteryHighestValue', 0)),
                "sleep_min": int(row.get('totalSleep_minutes', 0)),
                "hrv": round(float(row.get('avgOvernightHrv', 0) or 0), 1),
            })

        return result

    except Exception as e:
        logger.error(f"Metrics Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/history", tags=["Analytics"])
async def get_metrics_history(user: dict = Depends(verify_token), days: int = 90):
    """
    Get historical recovery and training metrics.

    Returns time-series data for:
    - Sleep quality and duration
    - Body Battery / Readiness scores
    - Heart Rate Variability (HRV)
    - Training load and stress

    **Note:** Limited to last 90 days of data for performance.
    """
    return await _get_metrics_history_internal(user['uid'], days)


@router.get("/ai/insight")
@limiter.limit("10/minute")
async def get_ai_insight(request: Request, user: dict = Depends(verify_token)):
    """
    Generate AI-powered daily training insight.

    Analyzes user's recovery metrics and provides personalized recommendations using Google Gemini.

    **Caching:** Results cached for 24 hours (per user, per day)

    **Rate Limit:** 10 requests/minute

    **Fallback:** Returns generic advice if AI generation fails
    """
    try:
        metrics = await _get_metrics_history_internal(user['uid'], days=1)
        if not metrics or len(metrics) == 0:
            return {"insight": "Ei tarpeeksi dataa analyysiin."}

        latest = metrics[0]

        # 1. OPTIMIZATION: Check Cache
        today_str = datetime.now().strftime('%Y-%m-%d')
        cached_insight = db_manager.get_daily_insight(user['uid'], today_str)

        if cached_insight:
            return {"insight": cached_insight}

        # Prepare context for AI
        ctx = {
            "tsb": latest['tsb'],
            "readiness": latest['readiness'],
            "sleep_min": latest['sleep_min'],
            "ctl": latest['ctl']
        }

        insight = ai_coach.generate_daily_insight(ctx)

        # 2. OPTIMIZATION: Save to Cache
        if insight and "Error" not in insight:
            db_manager.save_daily_insight(user['uid'], today_str, insight)

        return {"insight": insight}

    except Exception as e:
        logger.error(f"Insight Endpoint Error: {e}")
        return {"insight": "Tänään kannattaa kuunnella kehoa."}  # Fallback


@router.get("/ai/weekly-summary")
@limiter.limit("5/minute")
async def get_weekly_summary(request: Request, user: dict = Depends(verify_token)):
    """
    Generate a weekly training summary using AI.

    Cached in Firestore under `weekly_summaries/{monday_date}` (regenerated each Monday).
    """
    uid = user['uid']
    try:
        today = datetime.now().date()
        days_since_monday = today.weekday()
        monday_str = (today - timedelta(days=days_since_monday)).isoformat()

        # 1. Check cache
        cache_doc = db_manager.get_db().collection('users').document(uid) \
            .collection('weekly_summaries').document(monday_str).get()
        if cache_doc.exists:
            cached = cache_doc.to_dict()
            return {"summary": cached.get('summary'), "week_start": monday_str, "cached": True}

        # 2. Fetch last 7 days metrics
        metrics_7 = await _get_metrics_history_internal(uid, days=7)
        if not metrics_7:
            return {"summary": "Ei tarpeeksi dataa viikkoyhteenvetoon.", "week_start": monday_str, "cached": False}

        # 3. Fetch active goals for context
        goals = db_manager.get_active_goals(uid)

        # 4. Generate summary
        summary = ai_coach.generate_weekly_summary(uid, metrics_7, goals)

        # 5. Cache result
        from google.cloud.firestore_v1 import SERVER_TIMESTAMP
        db_manager.get_db().collection('users').document(uid) \
            .collection('weekly_summaries').document(monday_str) \
            .set({'summary': summary, 'created_at': SERVER_TIMESTAMP})

        return {"summary": summary, "week_start": monday_str, "cached": False}

    except Exception as e:
        logger.error(f"Weekly Summary Error for uid={uid}: {e}")
        return {"summary": "Viikkoyhteenveto ei juuri nyt saatavilla.", "week_start": "", "cached": False}


@router.post("/ai/morning-briefing")
@limiter.limit("10/minute")
async def trigger_morning_briefing(request: Request, user: dict = Depends(verify_token)):
    """
    Generate and send a morning briefing push notification for the authenticated user.
    """
    uid = user['uid']
    try:
        from notification_service import notification_service

        metrics = await _get_metrics_history_internal(uid, days=1)
        ctx = {}
        if metrics:
            latest = metrics[-1]
            ctx = {
                'readiness': latest.get('readiness', 0),
                'tsb': latest.get('tsb', 0),
                'sleep_min': latest.get('sleep_min', 0),
                'ctl': latest.get('ctl', 0),
            }

        next_wk = db_manager.get_next_workout(uid)
        if next_wk:
            ctx['next_workout'] = next_wk.get('content', {}).get('activity', '')

        briefing = ai_coach.generate_morning_briefing(ctx)

        sent = notification_service.send_push_notification(
            uid,
            title=briefing['title'],
            body=briefing['body'],
            data={'type': 'morning_briefing'}
        )

        return {"title": briefing['title'], "body": briefing['body'], "push_sent": sent}

    except Exception as e:
        logger.error(f"Morning Briefing Error for uid={uid}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/chat")
@limiter.limit("10/minute")
async def chat_endpoint(request_body: ChatRequest, request: Request, user: dict = Depends(verify_token)):
    """
    Interactive AI Coach Chat (Gemini Flash).
    """
    try:
        reply = chat_manager.generate_reply(user['uid'], request_body.message, request_body.history)
        return {"reply": reply}
    except Exception as e:
        logger.error(f"Chat Endpoint Error: {e}")
        raise HTTPException(status_code=500, detail="Chat failed")


@router.get("/ai/model-metrics")
async def get_model_metrics(user: dict = Depends(verify_token)):
    """Get ML model performance metrics (R², MAE, feature importance)."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level since we're in routers/
        base_dir = os.path.dirname(base_dir)
        uid = user['uid']

        if os.path.exists("/app/data"):
            data_dir = "/app/data"
            outputs_dir = "/app/outputs"
        else:
            data_dir = os.path.join(base_dir, "data")
            outputs_dir = os.path.join(base_dir, "outputs")

        metrics_path = os.path.join(data_dir, uid, "model_metrics.json")
        fi_path = os.path.join(outputs_dir, uid, "feature_importance.json")

        if not os.path.exists(metrics_path):
            metrics_path = os.path.join(data_dir, "model_metrics.json")

        if not os.path.exists(fi_path):
            fi_path = os.path.join(outputs_dir, "feature_importance.json")
            if not os.path.exists(fi_path):
                fi_path = os.path.join(base_dir, "..", "feature_importance.json")

        data = {"r2": 0, "mae": 0, "last_trained": "Never", "top_features": {}, "data_points": 0}

        data['data_points'] = firestore_garmin_metrics.get_user_metrics_count(uid)

        firestore_data = firestore_garmin_metrics.get_model_performance(uid)

        if firestore_data:
            if 'metrics' in firestore_data:
                data.update(firestore_data['metrics'])
            if 'feature_importance' in firestore_data:
                data['top_features'] = firestore_data['feature_importance']
            return data

        try:
            if os.path.exists(metrics_path):
                with open(metrics_path, "r") as f:
                    data.update(json.load(f))
        except Exception as e:
            logger.warning(f"Error loading metrics: {e}")

        try:
            if os.path.exists(fi_path):
                with open(fi_path, "r") as f:
                    fi_data = json.load(f)
                    sorted_fi = dict(sorted(fi_data.items(), key=lambda item: item[1], reverse=True)[:10])
                    data['top_features'] = sorted_fi
        except Exception as e:
            logger.warning(f"Error loading feature importance: {e}")

        return data
    except Exception as e:
        logger.error(f"Error fetching model metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plans/generate")
@limiter.limit("5/minute")
async def generate_plan_endpoint(request: Request, req: PlanGenerationRequest, user: dict = Depends(verify_token)):
    """Generate an AI training plan for 1-7 days."""
    if not db_manager.check_daily_generation_limit(user['uid']):
        raise HTTPException(status_code=429, detail="Daily plan generation limit (5) reached.")
    try:
        metrics = await _get_metrics_history_internal(user['uid'], days=1)
        if not metrics or len(metrics) == 0:
            latest = {"tsb": 0, "readiness": 50, "sleep_min": 420, "ctl": 0, "load": 0}
        else:
            latest = metrics[0]

        ctx = {
            "date": date.today().isoformat(),
            "predicted_charge": latest.get('readiness', 50),
            "sleep_hours": latest.get('sleep_min', 0) / 60,
            "recent_load": latest.get('load', 0),
            "ctl": latest.get('ctl', 0),
            "tsb": latest.get('tsb', 0)
        }

        trend_data = firestore_garmin_metrics.get_user_trend_data(user['uid'])
        ctx.update(trend_data)

        xgb_prediction = predictor.predict_tomorrow_readiness(user['uid'])
        if xgb_prediction is not None:
            ctx['xgboost_predicted_charge'] = xgb_prediction

        response_json = ai_coach.generate_coach_advice(
            user_id=user['uid'],
            context=ctx,
            n_days=req.days,
            rejected_context=req.rejected_plan_details
        )

        try:
            cleaned = response_json.replace('```json', '').replace('```', '').strip()
            plans = json.loads(cleaned)

            today = date.today()

            today_str = today.isoformat()
            workouts_today = db_manager.get_workouts_in_range(user['uid'], today_str, today_str)
            has_completed_today = any(w.get('status') == 'DONE' for w in workouts_today)

            start_date = today + timedelta(days=1) if has_completed_today else today

            max_day = 1
            for p in plans:
                max_day = max(max_day, p.get('day', 1))

            end_date_obj = start_date + timedelta(days=max_day - 1)

            db_manager.delete_pending_workouts(
                user['uid'],
                start_date.isoformat(),
                end_date_obj.isoformat()
            )

            saved_count = 0
            for p in plans:
                day_offset = p.get('day', 1) - 1
                workout_date = start_date + timedelta(days=day_offset)

                workout_doc = {
                    "date": workout_date.isoformat(),
                    "activity": p.get('activity', 'Rest'),
                    "description": p.get('description', ''),
                    "duration_min": p.get('duration_min', 0),
                    "load_estimate": p.get('load_estimate', 0),
                    "structure": p.get('structure_summary', ''),
                    "details": p.get('detailed_steps', []),
                    "tips": p.get('tips', ''),
                    "status": "PENDING",
                    "source": "AI_GENERATED",
                    "garmin_workout": p.get('garmin_workout')
                }

                db_manager.save_workout(user['uid'], workout_doc)
                saved_count += 1

            activity_counts = {}
            for p in plans:
                act = p.get('activity', 'Other')
                activity_counts[act] = activity_counts.get(act, 0) + 1

            summary_text = f"Plan ({req.days} days): " + ", ".join(
                [f"{count}x {act}" for act, count in activity_counts.items()]
            )

            db_manager.save_generated_plan(
                user['uid'],
                {"raw_json": plans},
                summary_text,
                ctx['predicted_charge']
            )

            return {"status": "success", "count": saved_count, "plans": plans}

        except Exception as parse_error:
            logger.error(f"AI Parse Error: {parse_error} \nResponse: {response_json}")
            if "QUOTA_EXCEEDED" in str(response_json):
                raise HTTPException(status_code=429, detail="AI Quota Exceeded. Please try again later.")
            raise HTTPException(status_code=500, detail="Failed to parse AI response")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Plan Gen Error: {e}")
        if "QUOTA_EXCEEDED" in str(e):
            raise HTTPException(status_code=429, detail="AI Quota Exceeded. Please try again later.")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans/history")
async def get_plan_history(limit: int = 5, user: dict = Depends(verify_token)):
    """Get recent AI-generated plans."""
    return db_manager.get_recent_plans(user['uid'], limit=limit)


@router.get("/readiness")
@limiter.limit("20/minute")
def get_readiness(request: Request, user: dict = Depends(verify_token)):
    """Get latest readiness/recovery score."""
    try:
        res = db_manager.get_latest_readiness(user['uid'])
        if not res:
            return {"readiness": "--", "date": ""}
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gamification/summary", tags=["Analytics"])
async def get_gamification_status(user: dict = Depends(verify_token)):
    """
    Get the gamification metrics and badges for the current user.

    Returns:
    - `consistency_score`: 14-day execution score average
    - `streak`: Consecutive workouts with >=80 execution score
    - `badges`: List of unlocked badges (e.g., Bronze, Silver, Gold, Fire)
    """
    try:
        summary = db_manager.get_gamification_summary(user['uid'])
        return summary
    except Exception as e:
        logger.error(f"Gamification Summary Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
