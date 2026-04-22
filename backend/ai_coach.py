import os
from google import genai
from dotenv import load_dotenv
import firestore_manager as db_manager
import secret_loader

# Load API Key
# Prioritizes Env Var, then Secret Manager
api_key = secret_loader.get_secret("GEMINI_API_KEY")

# Initialize the Gemini Client ONCE at startup (Singleton)
ai_client = genai.Client(api_key=api_key) if api_key else None

def construct_prompt(ctx, compliance_history="", preference_feedback="", active_goals="", rejected_context=None):
    rejection_text = ""
    if rejected_context:
        rejection_text = f"""
        HUOMIO: Urheilija HYLKÄSI edellisen ehdotuksen.
        Hylätty treeni: {rejected_context.get('activity')} - {rejected_context.get('description')}
        Syy/Muutospyyntö: Urheilija halusi uuden vaihtoehdon. Varmista, että tämä ehdotus on erilainen.
        """
    
    # Interpret Body Battery level
    bb_value = ctx['predicted_charge']
    if bb_value >= 75:
        bb_interpretation = "🟢 ERINOMAINEN - Täysin palautunut, valmis kovaan treeniin"
    elif bb_value >= 60:
        bb_interpretation = "🟡 HYVÄ - Kohtalainen palautuminen, sopii kohtalaiseen treeniin"
    elif bb_value >= 40:
        bb_interpretation = "🟠 MATALA - Heikko palautuminen, suosittele KEVYT/LEPO"
    else:
        bb_interpretation = "🔴 KRIITTINEN - Erittäin huono palautuminen, suosittele LEPO"

    # Evaluate Injury Risk
    atl_change = ctx.get('atl_change_pct', 0)
    sleep_change = ctx.get('sleep_change_hours', 0)
    
    injury_risk_text = ""
    if atl_change > 30 and sleep_change < -0.5:
        injury_risk_text = f"""
    ⚠️ LOUKKAANTUMISRISKIVAROITUS (CRITICAL):
    Urheilijan akuutti rasitus (ATL) on noussut vaarallisen nopeasti (+{atl_change}%) verrattuna viime viikkoon, ja samanaikaisesti unen määrä on vähentynyt ({sleep_change} h/yö).
    → SINUN ON PAKKO antaa eksplisiittinen varoitus kohonneesta rasitusvamman riskistä treenin 'description'- tai 'tips'-kentässä.
    → Suosittele ehdottomasti vain LEPOA tai erittäin kevyttä huoltavaa harjoittelua (mobility, walking). Älä anna tehotreenejä.
        """
    elif atl_change > 40:
        injury_risk_text = f"""
    ⚠️ VAROITUS:
    Urheilijan akuutti rasitus (ATL) on noussut erittäin nopeasti (+{atl_change}%) verrattuna viime viikkoon.
    → Harkitse tarkkaan ohjelmoinnin keventämistä välttääksesi rasitusvammat.
        """


    # XGBoost Predictive Context
    xgboost_instruction = ""
    if 'xgboost_predicted_charge' in ctx:
        xgb_val = ctx['xgboost_predicted_charge']
        xgboost_instruction = f"""
    🤖 XGBOOST ENNUSTE: Koneoppimismalli ennustaa huomisen palautumistason (Body Battery) olevan {xgb_val:.1f}/100.
    → SÄÄNTÖ: Jos luku on matala (<45), vältä raskaita harjoituksia ja painota palautumista. Jos luku on korkea (>75), urheilija on todennäköisesti valmis kovaan tehotreeniin huomenna.
        """

    return f"""
    Olet huippu-urheiluun erikoistunut valmentaja.
    {xgboost_instruction}
    
    Urheilijan tilanne tänään ({ctx['date']}):
    - Body Battery (Palautuminen): {ctx['predicted_charge']:.0f}/100 → {bb_interpretation}
    - Unen kesto: {ctx['sleep_hours']:.1f} tuntia
    - Viimeaikainen kuormitus (7pv keskiarvo): {ctx['recent_load']:.0f}
    - Viime aikojen toteutus: {compliance_history}
    - Palautteet: {preference_feedback}
    - AKTIIVISET TAVOITTEET: {active_goals}
    - TRENDI: Akuutti rasitus (ATL) on muuttunut {atl_change}% ja uni {sleep_change}h viimeisen viikon aikana.

    {injury_risk_text}
    {rejection_text}
    
    ⚠️ KRIITTINEN OHJE - Body Battery Tulkinta:
    • 75-100: Erinomainen palautuminen → Suosittele tehokasta treeniä (intervals, kova tempo, pitkä kesto)
    • 60-74: Hyvä palautuminen → Suosittele kohtalaista treeniä (peruskestävyys, kevyt tempo)
    • 40-59: Matala palautuminen → Suosittele KEVYT aktiivinen palautuminen (VR-lenkki, mobility) TAI lepo
    • 0-39: Kriittinen väsymys → Suosittele PAKOLLINEN lepopäivä (Rest Day)
    
    Jos urheilija on subjektiivisesti väsynyt (huono uni, matala BB), ÄLÄ KOSKAAN suosittele kovaa treeniä!
    
    Tehtävä:
    Luo tarkka ja ammattimainen treenisuunnitelma tälle päivälle JSON-muodossa.
    
    TÄRKEÄÄ: Jos 'AKTIIVISET TAVOITTEET' mainitsee tietyn lajin (esim. Juoksu, Pyöräily), painota ohjelmassa kyseistä lajia.

    [
        {{
            "day": 1,
            "activity": "Laji (esim. Juoksu, Pyöräily)",
            "description": "Treenin tavoite",
            "duration_min": 45,
            "load_estimate": 60,
            "structure_summary": "ERITTÄIN LYHYT kaava (Max 15 sanaa). Esim: '10min VR + 40min PK + 5min VR'",
            "detailed_steps": [
                "Alkulämmittely: 10min ...",
                "Työosuus: 40min ...",
                "Loppuverryttely: 5min ..."
            ],
            "garmin_workout": {{
                "workoutName": "AI Coach - {ctx['date']}",
                "sport": "RUNNING",
                "steps": [
                    {{
                        "type": "WorkoutStep",
                        "stepOrder": 1,
                        "intensity": "WARMUP",
                        "description": "Warm up",
                        "durationType": "TIME",
                        "durationValue": 600,
                        "targetType": "HEART_RATE",
                        "targetValueOne": 120,
                        "targetValueTwo": 140
                    }},
                    {{
                        "type": "WorkoutStep",
                        "stepOrder": 2,
                        "intensity": "INTERVAL",
                        "description": "Run Hard",
                        "durationType": "DISTANCE",
                        "durationValue": 1000,
                        "targetType": "PACE",
                        "targetValueOne": 240, 
                        "targetValueTwo": 260
                    }}
                ]
            }},
            "tips": "Vinkki"
        }}
    ]

    * garmin_workout säännöt:
        - "durationType": Vain "TIME" (sekunteja) tai "DISTANCE" (metrejä)
        - "targetType": "HEART_RATE" (bpm, käytä targetValueOne/Two), "PACE" (s/km, käytä targetValueOne/Two), "NO_TARGET" (ei targetValueOne/Two kenttiä)
        - "intensity": Vain "WARMUP", "INTERVAL", "RECOVERY", "REST", tai "COOLDOWN"
    
    * load_estimate: Arvioitu kuormitus 0-100 (TSS-tyyppinen).
    
    Kieli: Suomi.
    """

def construct_multi_day_prompt(ctx, n_days, compliance_history="", preference_feedback="", active_goals=""):
    # XGBoost Predictive Context
    xgboost_instruction = ""
    if 'xgboost_predicted_charge' in ctx:
        xgb_val = ctx['xgboost_predicted_charge']
        xgboost_instruction = f"""
    🤖 XGBOOST ENNUSTE: Koneoppimismalli ennustaa huomisen palautumistason (Body Battery) asettuvan tasoon {xgb_val:.1f}/100.
    → SÄÄNTÖ: Ota tämä matemaattinen arvio välittömästi huomioon seuraavien 1-2 päivän ohjelmoinnissa! 
        """
        
    return f"""
    Olet huippu-urheiluun erikoistunut valmentaja.
    {xgboost_instruction}
    
    Urheilijan lähtötilanne:
    - Body Battery: {ctx['predicted_charge']:.0f}/100
    - Kuormitus: {ctx['recent_load']:.0f}
    - Viime aikojen toteutus: {compliance_history}
    - Palautteet: {preference_feedback}
    - AKTIIVISET TAVOITTEET: {active_goals}
    
    Tehtävä:
    Luo progressiivinen ja YKSITYISKOHTAINEN treenisuunnitelma {n_days} päivälle JSON-muodossa.
    
    TÄRKEÄÄ: Jos 'AKTIIVISET TAVOITTEET' mainitsee tietyn lajin (esim. Juoksu, Pyöräily), painota ohjelmassa kyseistä lajia.

    Format (JSON):
    [
        {{
            "day": 1,
            "activity": "Laji",
            "description": "Lyhyt kuvaus tavoitteesta",
            "duration_min": 60,
            "load_estimate": 70,
            "structure_summary": "ERITTÄIN LYHYT kaava (Max 15 sanaa). Esim: '4x4min VK2'",
            "detailed_steps": [
                "Alkulämmittely: ...",
                "Työosuus: ...",
                "Loppuverryttely: ..."
            ],
            "garmin_workout": {{
                "workoutName": "AI Coach - Päivä {{day}}",
                "sport": "RUNNING",
                "steps": [
                    {{
                        "type": "WorkoutStep",
                        "stepOrder": 1,
                        "intensity": "WARMUP",
                        "description": "Warm up",
                        "durationType": "TIME",
                        "durationValue": 600,
                        "targetType": "HEART_RATE",
                        "targetValueOne": 120,
                        "targetValueTwo": 140
                    }},
                     {{
                        "type": "WorkoutStep",
                        "stepOrder": 2,
                        "intensity": "INTERVAL",
                        "description": "Run Hard",
                        "durationType": "DISTANCE",
                        "durationValue": 1000,
                        "targetType": "PACE",
                        "targetValueOne": 240, 
                        "targetValueTwo": 260
                    }}
                ]
            }},
            "tips": "Vinkki"
        }},
        {{
            "day": 2,
            ...
        }}
    ]
    
    * garmin_workout säännöt:
        - "durationType": Vain "TIME" (sekunteja) tai "DISTANCE" (metrejä)
        - "targetType": "HEART_RATE" (bpm, käytä targetValueOne/Two), "PACE" (s/km, käytä targetValueOne/Two), "NO_TARGET" (ei targetValueOne/Two kenttiä)
        - "intensity": Vain "WARMUP", "INTERVAL", "RECOVERY", "REST", tai "COOLDOWN"
    
    * load_estimate: Arvioitu kuormitus 0-100 (TSS-tyyppinen).
    
    Kieli: Suomi.
    """

def generate_coach_advice(user_id, context, n_days=1, compliance_history="", preference_feedback="", rejected_context=None):
    """Generates advice using Gemini."""
    if not api_key:
        return "Error: No API Key found in .env file."

    print(f"Calling Gemini Coach (Days: {n_days})...")
    
    try:
        # Fetch Execution Score compliance
        avg_score = db_manager.get_average_execution_score(user_id, days=7)
        if avg_score is not None:
            compliance_history += f"\n- Treenien toteutus-% viimeiseltä 7 päivältä on {avg_score:.0f}%. (100% = täydellinen, tavoite/oikea kesto ja rasitus. <70% = heikko). Mukauta suosituksia toteutumaan."
            
        # Fetch Active Goals
        goals_list = db_manager.get_active_goals(user_id)
        
        # Sort Race first
        goals_list.sort(key=lambda x: x.get('period_type') != 'race')
        
        goals_text = ""
        if goals_list:
            lines = []
            for g in goals_list:
                activity = g.get('activity_type', 'Unknown')
                value = g.get('target_value', 0)
                unit = g.get('target_unit', '')
                period = g.get('period_type', g.get('frequency', 'weekly'))
                date_str = f"- Date: {g.get('target_date')}" if g.get('target_date') else ""
                desc = f"({g.get('description', '')})" if g.get('description') else ""
                
                if period == 'race':
                    # Special Format
                    lines.append(f"*** KISATAVOITE: {activity} - {desc or 'Kisa'} *** {date_str}. Tavoite: {value} {unit}.")
                else:
                    lines.append(f"- {activity}: {value} {unit} ({period}) {date_str} {desc}")
            goals_text = "\n".join(lines)
        else:
            goals_text = "Ei asetettuja tavoitteita."

        if n_days > 1:
            prompt = construct_multi_day_prompt(context, n_days, compliance_history, preference_feedback=preference_feedback, active_goals=goals_text)
        else:
            prompt = construct_prompt(context, compliance_history, preference_feedback=preference_feedback, active_goals=goals_text, rejected_context=rejected_context)
        
        response = ai_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config={
                'response_mime_type': 'application/json'
            }
        )
        return response.text
    except Exception as e:
        error_str = str(e)
        if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
            print(f"Gemini Policy Error: {e}")
            # Raise a specific error string that main.py can catch
            raise Exception(f"QUOTA_EXCEEDED: {error_str}")
        return f"Error contacting AI Coach: {e}"

def generate_trend_analysis(df_recent):
    """Analyzes the last 30 days of history."""
    if not api_key:
        return "Error: No API Key found."
    
    print("Thinking (Trend Analysis)...")
    
    try:
        # Prepare data summary
        csv_data = df_recent[['date', 'bodyBatteryChargedValue', 'totalSleep_minutes', 'averageStressLevel', 'workout_calories']].to_csv(index=False)
        
        prompt = f"""
        You are an expert data analyst in sports physiology.
        Here is the last 30 days of data for an athlete (CSV format):
        
        {csv_data}
        
        Task:
        Analyze the trends in Recovery (BodyBattery), Sleep, and Activity.
        1. Identify the strongest correlation (e.g. "Does stress hurt recovery more than lack of sleep?").
        2. Check the weekend vs weekday pattern if visible.
        3. Give a summary of the "Activity Impact" - are high load days followed by poor recovery?
        
        Output in Finnish language. Keep it concise (bullet points).
        """
        
        response = ai_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error analyzing trends: {e}"

def generate_daily_insight(ctx):
    """
    Generates a short, daily coaching insight (1-2 sentences) based on metrics.
    """
    if not api_key:
        return "API Key missing. Cannot generate insight."
        
    prompt = f"""
    Olet huippu-urheiluun erikoistunut valmentaja.
    
    Analysoi seuraavat mittarit ja anna YKSI TAI KAKSI tiivistä, motivoivaa lausetta siitä, miten urheilijan tulisi tänään toimia (levätä, treenata kovaa, palautella?).
    
    Mittarit:
    - TSB (Training Stress Balance / Vireystila): {ctx.get('tsb', 0)} (Positiivinen = Tuore, Negatiivinen = Rasittunut)
    - Body Battery (Lataus): {ctx.get('readiness', 0)}/100
    - Uni: {ctx.get('sleep_min', 0) / 60:.1f} tuntia
    - Krooninen kuormitus (CTL): {ctx.get('ctl', 0)}
    
    Ohje:
    - Pidä vastaus erittäin lyhyenä (max 30 sanaa).
    - Ole suora ja selkeä.
    - Kieli: Suomi.
    """
    
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        return response.text.replace('"', '').strip() # Clean quotes
    except Exception as e:
        print(f"Insight Error: {e}")
        return "Tänään on hyvä päivä kuunnella kehoa."

def generate_rescheduling_suggestion(user_id, missed_workout, current_metrics):
    """
    Generates a suggestion for rescheduling a missed workout.
    """
    if not api_key:
        return None

    prompt = f"""
    Olet huippu-urheiluun erikoistunut valmentaja.
    
    Urheilija SKIPPASI seuraavan treenin:
    - Treeni: {missed_workout.get('activity')}
    - Kuvaus: {missed_workout.get('description')}
    - Alkuperäinen päivä: {missed_workout.get('date')}
    
    Nykyinen tilanne ({current_metrics.get('date')}):
    - Body Battery: {current_metrics.get('readiness', 0)}/100
    - TSB (Vireystila): {current_metrics.get('tsb', 0)}
    
    Tehtävä:
    Ehdotus uudelle ajankohdalle tälle treenille. 
    Palauta JSON-muodossa:
    {{
        "new_date": "YYYY-MM-DD",
        "reasoning": "Lyhyt selitys suomeksi, miksi tämä päivä on hyvä (max 20 sanaa).",
        "push_message": "Lyhyt, tsemppaava viesti push-ilmoitukseen suomeksi (esim. 'Huomenna on loistava päivä korvata eilinen veto!')."
    }}
    
    Sääntö koon suhteen: Suosittele uutta päivää aikavälille {current_metrics.get('date')} - 3 päivää eteenpäin.
    """
    
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        import json
        return json.loads(response.text)
    except Exception as e:
        print(f"Rescheduling AI Error: {e}")
        return None


def generate_morning_briefing(ctx: dict) -> dict:
    """
    Generates a short, motivating morning briefing for push notification.
    Returns dict with 'title' and 'body' (max 60 chars each).
    """
    if not api_key:
        return {"title": "Hyvää huomenta!", "body": "Tarkista valmistautumistilasi."}

    bb = ctx.get('readiness', 0)
    tsb = ctx.get('tsb', 0)
    next_workout = ctx.get('next_workout', '')
    sleep_h = ctx.get('sleep_min', 0) / 60

    prompt = f"""
    Olet henkilökohtainen urheiluvalmentaja. Kirjoita LYHYT aamutervehdys push-ilmoitukseen.

    Urheilijan tilanne:
    - Body Battery: {bb}/100
    - TSB (Vireystila): {tsb} (positiivinen = levännyt)
    - Uni viime yönä: {sleep_h:.1f} h
    - Seuraava treeni: {next_workout or 'Ei suunniteltua'}

    Palauta JSON-muodossa:
    {{
        "title": "Otsikko (max 40 merkkiä, emoji OK)",
        "body": "Viesti (max 80 merkkiä, konkreettinen neuvot)"
    }}

    Säännöt:
    - Body Battery < 40 → Suosittele lepoa
    - Body Battery 40-59 → Kevyt treeni
    - Body Battery 60-74 → Kohtalainen treini
    - Body Battery >= 75 → Kova treeni suositellaan
    - Mainitse seuraava treeni jos sellainen on
    - Pysy lyhyenä ja motivoivana
    - Kieli: Suomi
    """

    try:
        response = ai_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        import json
        result = json.loads(response.text)
        # Truncate safety
        return {
            "title": result.get('title', 'Hyvää huomenta!')[:60],
            "body": result.get('body', 'Tarkista treenisi.')[:120]
        }
    except Exception as e:
        print(f"Morning Briefing Error: {e}")
        # Fallback based on body battery
        if bb >= 75:
            return {"title": f"🟢 Päivä alkaa! BB: {bb}/100", "body": "Olet täynnä energiaa – täydellinen päivä kovaan treeniin!"}
        elif bb >= 60:
            return {"title": f"🟡 Hyvää huomenta! BB: {bb}/100", "body": "Kohtalainen palautuminen – sopii kohtuulliseen treeniin."}
        elif bb >= 40:
            return {"title": f"🟠 Huominen! BB: {bb}/100", "body": "Palautuminen matala – suosi kevyttä liikettä tai lepoa."}
        else:
            return {"title": f"🔴 Lepopäivä! BB: {bb}/100", "body": "Keho tarvitsee lepoa – pidä tänään vapaapäivä."}


def generate_weekly_summary(user_id: str, metrics_last_7: list, goals: list) -> str:
    """
    Generates a weekly training summary (3-5 sentences).
    """
    if not api_key:
        return "Viikkoyhteenveto ei saatavilla (API avain puuttuu)."

    if not metrics_last_7:
        return "Ei tarpeeksi dataa viikkoyhteenvetoon."

    # Compute averages
    avg_bb = sum(m.get('readiness', 0) for m in metrics_last_7) / len(metrics_last_7)
    avg_sleep = sum(m.get('sleep_min', 0) for m in metrics_last_7) / len(metrics_last_7) / 60
    total_load = sum(m.get('load', 0) for m in metrics_last_7)
    avg_tsb = sum(m.get('tsb', 0) for m in metrics_last_7) / len(metrics_last_7)
    latest_ctl = metrics_last_7[-1].get('ctl', 0) if metrics_last_7 else 0

    # Build goals text
    goals_text = ", ".join(
        f"{g.get('activity_type','?')} {g.get('target_value','?')} {g.get('target_unit','')}/{g.get('frequency','vko')}"
        for g in (goals or [])[:3]
    ) if goals else "Ei asetettuja tavoitteita"

    prompt = f"""
    Olet henkilökohtainen urheiluvalmentaja. Kirjoita LYHYT viikkoyhteenveto urheilijalle.

    Viikon (7 pv) tilastot:
    - Keskimääräinen Body Battery: {avg_bb:.0f}/100
    - Keskimääräinen uni: {avg_sleep:.1f} h/yö
    - Viikon kokonaiskuormitus: {total_load:.0f}
    - Keskimääräinen TSB (vireystila): {avg_tsb:.1f}
    - Nykyinen kuntotaso (CTL): {latest_ctl:.1f}
    - Aktiiviset tavoitteet: {goals_text}

    Kirjoita 3-4 lausetta suomeksi:
    1. Viikon yleisarvio (positiivinen mutta rehellinen)
    2. Merkittävin havainto (uni, kuormitus tai palautuminen)
    3. Suositus ensi viikolle

    Pidä se motivoivana ja konkreettisena. Max 80 sanaa.
    """

    try:
        response = ai_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Weekly Summary Error: {e}")
        return f"Viikkoyhteenveto: Keskimääräinen palautuminen {avg_bb:.0f}%, uni {avg_sleep:.1f}h/yö, kuormitus {total_load:.0f}."

