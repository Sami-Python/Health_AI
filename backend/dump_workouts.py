import sys
import os
import json

# Add backend dir to path
sys.path.insert(0, os.path.abspath('c:/Users/samih/code/health_ai/backend'))
sys.path.insert(0, os.path.abspath('c:/Users/samih/code/health_ai/backend/scripts'))

try:
    import firestore_manager
    from fetch_garmin_data import get_garmin_client
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(1)

def dump_workouts():
    try:
        db = firestore_manager.get_db()
        # Find the first user
        users = list(db.collection('users').limit(5).stream())
        print(f"Found {len(users)} users.")
        
        for user in users:
            uid = user.id
            creds = firestore_manager.get_garmin_credentials(uid)
            if creds:
                print(f"Found credentials for {uid}")
                try:
                    client = get_garmin_client(uid)
                    print("Garmin client created.")
                    workouts = client.get_workouts()
                    print(f"Fetched {len(workouts) if workouts else 0} workouts.")
                    
                    if workouts:
                        with open('c:/Users/samih/code/health_ai/backend/garmin_workouts_dump.json', 'w') as f:
                            json.dump(workouts, f, indent=2)
                        print("Saved to garmin_workouts_dump.json")
                        return
                except Exception as e:
                    print(f"Failed for {uid}: {e}")
    except Exception as e:
        print(f"DB Error: {e}")

if __name__ == "__main__":
    dump_workouts()
