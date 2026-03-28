import sys
import os
import time
import threading

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

# Mock dependencies before importing main
from unittest import mock
import sys
sys.modules['secret_loader'] = mock.Mock()
sys.modules['firestore_manager'] = mock.Mock()
sys.modules['db_manager'] = mock.Mock()
sys.modules['config'] = mock.Mock()
sys.modules['logger'] = mock.Mock()

from main import execute_refresh_task, _garmin_throttle_cache, refresh_statuses

def test_throttle_sync():
    print("Testing 429 Throttle Synchronization...")
    uid = "test_user_123"
    
    # Mock the fetch_garmin_data module
    mock_fetch = mock.Mock()
    mock_fetch.main.side_effect = Exception("Garmin Error: 429 Too Many Requests")
    sys.modules['scripts'] = mock.Mock()
    sys.modules['scripts.fetch_garmin_data'] = mock_fetch
    sys.modules['process_garmin_data'] = mock.Mock()

    try:
        execute_refresh_task(uid, mode="incremental")
    except Exception as e:
        print(f"Caught expected exception: {e}")

    # Check if throttle is set
    expiry = _garmin_throttle_cache.get(uid, 0)
    now = time.time()
    if expiry > now:
        print(f"✅ SUCCESS: Throttle cache set! Expires in {int(expiry - now)}s")
    else:
        print("❌ FAILURE: Throttle cache NOT set")
        sys.exit(1)

    # Check status message
    status = refresh_statuses.get(uid)
    if status and "rate-limited" in status.get("error", ""):
        print(f"✅ SUCCESS: Status error message correct: {status['error']}")
    else:
        print(f"❌ FAILURE: Status error message incorrect: {status}")
        sys.exit(1)

if __name__ == "__main__":
    test_throttle_sync()
