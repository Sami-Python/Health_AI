"""
Firestore manager functions for Garmin daily metrics (per-user storage).
Part of CSV migration (Phase 10.3 - Multi-User Data Isolation).
"""

from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
# Use shared Firestore client via get_db() to ensure initialization
import firestore_manager


def save_daily_metric(user_id: str, date_str: str, metric_data: dict) -> bool:
    """
    Save or update a daily health metric to Firestore.
    
    Schema: garmin_metrics/{user_id}/daily_metrics/{date}
    
    Args:
        user_id: Firebase UID
        date_str: Date in YYYY-MM-DD format
        metric_data: Dict containing daily metrics (HRV, stress, sleep, etc.)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure user_id is set
        metric_data['user_id'] = user_id
        metric_data['date'] = date_str
        metric_data['updated_at'] = firestore_manager.firestore.SERVER_TIMESTAMP
        
        # If this is first save, add created_at
        doc_ref = firestore_manager.get_db().collection('garmin_metrics').document(user_id)\
                    .collection('daily_metrics').document(date_str)
        
        if not doc_ref.get().exists:
            metric_data['created_at'] = firestore_manager.firestore.SERVER_TIMESTAMP
        
        doc_ref.set(metric_data, merge=True)
        return True
        
    except Exception as e:
        print(f"Firestore Error (save_daily_metric): {e}")
        return False


def get_user_daily_metrics(user_id: str, days: int = 30) -> List[Dict]:
    """
    Get last N days of metrics for a specific user.
    
    Args:
        user_id: Firebase UID
        days: Number of days to retrieve (default 30)
    
    Returns:
        List of metric dictionaries, ordered by date (oldest first)
    """
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        docs = firestore_manager.get_db().collection('garmin_metrics').document(user_id)\
                 .collection('daily_metrics')\
                 .where('date', '>=', start_date.isoformat())\
                 .where('date', '<=', end_date.isoformat())\
                 .order_by('date').stream()
        
        metrics = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            metrics.append(data)
        
        return metrics
        
    except Exception as e:
        print(f"Firestore Error (get_user_daily_metrics): {e}")
        return []


def get_metrics_in_range(user_id: str, start_date: str, end_date: str) -> List[Dict]:
    """
    Get metrics within a specific date range.
    
    Args:
        user_id: Firebase UID
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        List of metric dictionaries within the specified range
    """
    try:
        docs = firestore_manager.get_db().collection('garmin_metrics').document(user_id)\
                 .collection('daily_metrics')\
                 .where('date', '>=', start_date)\
                 .where('date', '<=', end_date)\
                 .order_by('date').stream()
        
        metrics = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            metrics.append(data)
        
        return metrics
        
    except Exception as e:
        print(f"Firestore Error (get_metrics_in_range): {e}")
        return []


def get_user_metrics_count(user_id: str) -> int:
    """
    Get total number of daily metric documents for a user.
    
    Args:
        user_id: Firebase UID
    
    Returns:
        Count of metric documents
    """
    try:
        docs = firestore_manager.get_db().collection('garmin_metrics').document(user_id)\
                 .collection('daily_metrics').stream()
        
        count = sum(1 for _ in docs)
        return count
        
    except Exception as e:
        print(f"Firestore Error (get_user_metrics_count): {e}")
        return 0


def get_latest_metric(user_id: str) -> Optional[Dict]:
    """
    Get the most recent daily metric for a user.
    
    Args:
        user_id: Firebase UID
    
    Returns:
        Latest metric dictionary or None if no metrics found
    """
    try:
        docs = firestore_manager.get_db().collection('garmin_metrics').document(user_id)\
                 .collection('daily_metrics')\
                 .order_by('date', direction=firestore_manager.firestore.Query.DESCENDING)\
                 .limit(1).stream()
        
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        
        return None
        
    except Exception as e:
        print(f"Firestore Error (get_latest_metric): {e}")
        return None


def delete_user_metrics(user_id: str) -> bool:
    """
    Delete all metrics for a user (GDPR compliance).
    
    Args:
        user_id: Firebase UID
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get all metric documents
        docs = firestore_manager.get_db().collection('garmin_metrics').document(user_id)\
                 .collection('daily_metrics').stream()
        
        # Batch delete
        batch = firestore_manager.get_db().batch()
        count = 0
        
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
            
            # Commit in batches of 400 (Firestore limit is 500)
            if count >= 400:
                batch.commit()
                batch = firestore_manager.get_db().batch()
                count = 0
        
        # Final commit
        if count > 0:
            batch.commit()
        
        # Delete parent document
        firestore_manager.get_db().collection('garmin_metrics').document(user_id).delete()
        
        print(f"Deleted {count} metric documents for user {user_id}")
        return True
        
    except Exception as e:
        print(f"Firestore Error (delete_user_metrics): {e}")
        return False


def batch_save_metrics(user_id: str, metrics_list: List[Dict]) -> bool:
    """
    Batch save multiple metrics efficiently.
    
    Args:
        user_id: Firebase UID
        metrics_list: List of metric dictionaries (each must have 'date' field)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        batch = firestore_manager.get_db().batch()
        count = 0
        
        for metric in metrics_list:
            date_str = metric.get('date')
            if not date_str:
                continue
            
            metric['user_id'] = user_id
            metric['updated_at'] = firestore_manager.firestore.SERVER_TIMESTAMP
            
            doc_ref = firestore_manager.get_db().collection('garmin_metrics').document(user_id)\
                        .collection('daily_metrics').document(date_str)
            
            batch.set(doc_ref, metric, merge=True)
            count += 1
            
            # Commit in batches of 400
            if count >= 400:
                batch.commit()
                batch = firestore_manager.get_db().batch()
                count = 0
        
        # Final commit
        if count > 0:
            batch.commit()
        
        print(f"Batch saved {len(metrics_list)} metrics for user {user_id}")
        return True
        
    except Exception as e:
        print(f"Firestore Error (batch_save_metrics): {e}")
        return False


def get_user_trend_data(user_id: str) -> dict:
    """
    Get 14-day trend data for injury risk prediction.
    Calculates change in Acute Training Load (ATL) and Sleep duration
    comparing the last 7 days vs the previous 7 days.
    """
    try:
        # Hae data viimeiseltä 14 päivältä
        metrics = get_user_daily_metrics(user_id, days=14)
        
        if len(metrics) < 7:
            # Ei tarpeeksi dataa trendien laskemiseen luotettavasti
            return {"atl_change_pct": 0, "sleep_change_hours": 0}

        # Jaa kahteen ajanjaksoon
        mid_point = len(metrics) // 2
        
        week1 = metrics[:mid_point]
        week2 = metrics[mid_point:]
        
        # Keskiarvo ATL
        atl_w1 = sum([m.get('ATL', 0) for m in week1]) / max(len(week1), 1)
        atl_w2 = sum([m.get('ATL', 0) for m in week2]) / max(len(week2), 1)
        
        # Keskiarvo uni tunteina
        sleep_w1 = sum([m.get('totalSleep_minutes', 0) for m in week1]) / max(len(week1), 1) / 60
        sleep_w2 = sum([m.get('totalSleep_minutes', 0) for m in week2]) / max(len(week2), 1) / 60
        
        # Muutokset
        atl_change_pct = ((atl_w2 - atl_w1) / atl_w1 * 100) if atl_w1 > 0 else 0
        sleep_change_hours = sleep_w2 - sleep_w1
        
        return {
            "atl_change_pct": round(atl_change_pct, 1),
            "sleep_change_hours": round(sleep_change_hours, 1)
        }
        
    except Exception as e:
        print(f"Firestore Error (get_user_trend_data): {e}")
        return {"atl_change_pct": 0, "sleep_change_hours": 0}



def save_model_performance(user_id: str, metrics: dict, feature_importance: dict) -> bool:
    """
    Save AI model performance metrics and feature importance.
    
    Schema: garmin_metrics/{user_id}/model_performance/latest
    """
    try:
        doc_data = {
            "metrics": metrics, # {r2, mae, last_trained}
            "feature_importance": feature_importance,
            "updated_at": firestore_manager.firestore.SERVER_TIMESTAMP
        }
        
        firestore_manager.get_db().collection('garmin_metrics').document(user_id)\
          .collection('model_performance').document('latest')\
          .set(doc_data, merge=True)
          
        return True
    except Exception as e:
        print(f"Firestore Error (save_model_performance): {e}")
        return False

def get_model_performance(user_id: str) -> Optional[Dict]:
    """
    Retrieve latest AI model performance metrics.
    """
    try:
        doc = firestore_manager.get_db().collection('garmin_metrics').document(user_id)\
                .collection('model_performance').document('latest').get()
        
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        print(f"Firestore Error (get_model_performance): {e}")
        return None
