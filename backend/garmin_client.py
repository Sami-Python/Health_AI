from garminconnect import Garmin
from logger import logger
import firestore_manager
import os
from typing import Dict, Any, Optional
import json

class GarminClient:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.client = None

    def connect(self):
        """
        Authenticate with Garmin Connect.
        
        Priority:
        1. Saved garth OAuth2 tokens (Firestore, encrypted) – silent re-auth
        2. Fresh login with prompt_mfa callback that raises a clear error
           if 2FA is demanded (user must reconnect via the app settings).
        
        Raises:
            ValueError: If no credentials found or login fails.
            GarminMFARequiredError (from fetch_garmin_data): If 2FA required.
        """
        try:
            # Use the shared get_garmin_client() which already handles the
            # token-first → fresh-login flow with proper MFA error handling.
            import sys, os
            scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
            if scripts_dir not in sys.path:
                sys.path.insert(0, scripts_dir)
            from fetch_garmin_data import get_garmin_client
            self.client = get_garmin_client(self.user_id)
            logger.info(f"✅ Garmin login successful for user {self.user_id}")
            
        except Exception as e:
            logger.error(f"❌ Garmin auth failed: {e}")
            raise ValueError(f"Garmin authentication failed: {str(e)}")


    def upload_workout(self, workout_json: Dict[str, Any]) -> Optional[str]:
        """
        Uploads a workout to Garmin Connect. Returns workout_id if successful.
        """
        if not self.client:
            self.connect()

        try:
            logger.info(f"Uploading workout for user {self.user_id}...")
            
            # --- TRANSFORM PAYLOAD FOR GARMIN API ---
            # Based on Valid JSON from Debug Output (Step 1164)
            
            # Mappings
            STEP_TYPES = {
                "warmup": { "stepTypeId": 1, "stepTypeKey": "warmup", "displayOrder": 1 },
                "cooldown": { "stepTypeId": 2, "stepTypeKey": "cooldown", "displayOrder": 2 },
                "interval": { "stepTypeId": 3, "stepTypeKey": "interval", "displayOrder": 3 },
                "recovery": { "stepTypeId": 4, "stepTypeKey": "recovery", "displayOrder": 4 },
                "rest": { "stepTypeId": 4, "stepTypeKey": "recovery", "displayOrder": 4 },
                "run": { "stepTypeId": 3, "stepTypeKey": "interval", "displayOrder": 3 },
                "other": { "stepTypeId": 7, "stepTypeKey": "other", "displayOrder": 7 }
            }
            
            CONDITION_TYPES = {
                "lap.button": { "conditionTypeId": 1, "conditionTypeKey": "lap.button", "displayOrder": 1, "displayable": True },
                "time": { "conditionTypeId": 2, "conditionTypeKey": "time", "displayOrder": 2, "displayable": True },
                "distance": { "conditionTypeId": 3, "conditionTypeKey": "distance", "displayOrder": 3, "displayable": True }
            }
            
            TARGET_TYPES = {
                "no.target": { "workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target", "displayOrder": 1 },
                "power.zone": { "workoutTargetTypeId": 2, "workoutTargetTypeKey": "power.zone", "displayOrder": 2 },
                "cadence.zone": { "workoutTargetTypeId": 3, "workoutTargetTypeKey": "cadence.zone", "displayOrder": 3 },
                "heart.rate.zone": { "workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone", "displayOrder": 4 },
                "pace.zone": { "workoutTargetTypeId": 6, "workoutTargetTypeKey": "pace.zone", "displayOrder": 6 } 
            }

            # 1. Sport Type
            sport = workout_json.get('sport', 'RUNNING').upper()
            sport_type_id = 1 
            sport_type_key = "running"
            if "CYCLING" in sport:
                sport_type_id = 2
                sport_type_key = "cycling"

            # 2. Build Steps
            garmin_steps = []
            steps = workout_json.get('steps', [])
            
            for i, step in enumerate(steps):
                # Type
                s_type_raw = step.get('intensity', step.get('type', 'interval')).lower()
                if "workoutstep" in s_type_raw: s_type_raw = "interval"
                step_type_obj = STEP_TYPES.get(s_type_raw, STEP_TYPES['interval'])
                
                # End Condition
                cond_raw = step.get('durationType', step.get('endCondition', 'lap.button')).lower()
                if "time" in cond_raw: cond_obj = CONDITION_TYPES['time']
                elif "dist" in cond_raw: cond_obj = CONDITION_TYPES['distance']
                else: cond_obj = CONDITION_TYPES['lap.button']
                
                end_val = None
                if cond_obj['conditionTypeKey'] == 'time':
                    try: end_val = float(step.get('durationValue', 0))
                    except: end_val = 0.0
                elif cond_obj['conditionTypeKey'] == 'distance':
                    val = step.get('distanceValue', step.get('durationValue', 0))
                    try: end_val = float(val)
                    except: end_val = 0.0

                # Target Logic
                target = step.get('targetType', 'no.target').lower()
                
                # Defaults (Matches "No Target" Debug JSON)
                target_obj = TARGET_TYPES['no.target']
                target_val_one = None
                target_val_two = None
                zone_number = None

                # Heart Rate Handling
                if "heart" in target or "hr" in target:
                    try: 
                        val1 = float(step.get('targetValueOne', 0))
                    except: 
                        val1 = 0
                        
                    if val1 > 0 and val1 < 10:
                        # ZONE TARGET (Correct usage based on Debug JSON)
                        target_obj = TARGET_TYPES['heart.rate.zone']
                        zone_number = int(val1) # Zone goes here!
                        target_val_one = None # Must be null for Zone
                        target_val_two = None
                        
                    elif val1 >= 10:
                        # BPM TARGET
                        # We don't have a confirmed "BPM" structure from debug (User didn't provide).
                        # Using ID 1 "no.target" is SAFE.
                        # We append info to description.
                        target_obj = TARGET_TYPES['no.target']
                        zone_number = None
                        step['description'] = f"{step.get('description','')} (Target HR: {int(val1)})"

                elif "pace" in target:
                    target_obj = TARGET_TYPES['pace.zone']
                    # Placeholder if we implement Pace Zones later

                # Construct Step DTO (Exact Field Matching Debug JSON)
                garmin_step = {
                    "type": "ExecutableStepDTO",
                    "stepOrder": i + 1,
                    "stepType": step_type_obj,
                    "childStepId": None,
                    "description": step.get('description', ''),
                    "endCondition": cond_obj,
                    "endConditionValue": end_val,
                    "preferredEndConditionUnit": None, # NEW
                    "endConditionCompare": None, # NEW
                    "targetType": target_obj,
                    "targetValueOne": target_val_one,
                    "targetValueTwo": target_val_two,
                    "targetValueUnit": None, # NEW
                    "zoneNumber": zone_number, 
                    "secondaryTargetType": None,
                    "secondaryTargetValueOne": None,
                    "secondaryTargetValueTwo": None,
                    "secondaryTargetValueUnit": None, # NEW
                    "secondaryZoneNumber": None,
                    "endConditionZone": None, # NEW
                    "strokeType": { "strokeTypeId": 0, "strokeTypeKey": None, "displayOrder": 0 }, # NEW
                    "equipmentType": { "equipmentTypeId": 0, "equipmentTypeKey": None, "displayOrder": 0 }, # NEW
                    "category": None, # NEW
                    "exerciseName": None, # NEW
                    "workoutProvider": None, # NEW
                    "providerExerciseSourceId": None, # NEW
                    "weightValue": None, # NEW
                    "weightUnit": None # NEW
                }
                garmin_steps.append(garmin_step)

            # Construct Sport Type Object
            sport_type_obj = {
                "sportTypeId": sport_type_id,
                "sportTypeKey": sport_type_key,
                "displayOrder": 1
            }

            # 3. Final Payload
            final_payload = {
                "workoutName": workout_json.get('workoutName', 'AI Workout'),
                "description": workout_json.get('description', 'Generated by Health AI'),
                "sportType": sport_type_obj, # NESTED OBJECT
                "workoutSegments": [
                    {
                        "segmentOrder": 1,
                        "sportType": sport_type_obj, # NESTED OBJECT
                        "workoutSteps": garmin_steps
                    }
                ]
            }

            # NOTE: We do NOT remove None values anymore. 
            # The Debug JSON showed explicit nulls for targetValueOne/Two/zoneNumber are expected.

            logger.info(f"Sending transformed payload to Garmin: {json.dumps(final_payload)}")

            url = "/workout-service/workout"
            response = self.client.connectapi(url, method="POST", json=final_payload)
            
            if response and ('workoutId' in response or (isinstance(response, dict) and 'workoutId' in response)):
                w_id = response['workoutId']
                logger.info(f"✅ Workout uploaded successfully. ID: {w_id}")
                return str(w_id) # Return ID instead of True
            else:
                logger.error(f"❌ Workout upload response invalid: {response}")
                return None

        except Exception as e:
            logger.error(f"❌ Failed to upload workout: {e}")
            raise e

    def schedule_workout(self, workout_id: str, date_str: str) -> bool:
        """
        Schedules a workout on the Garmin Calendar.
        """
        if not self.client:
            self.connect()

        try:
            logger.info(f"Scheduling workout {workout_id} for {date_str}...")
            
            url = f"/workout-service/schedule/{workout_id}"
            payload = {"date": date_str}
            
            # response is usually the scheduled item with 'scheduleId'
            response = self.client.connectapi(url, method="POST", json=payload)
            
            if response and ('scheduleId' in response or (isinstance(response, dict) and 'scheduleId' in response)):
                logger.info(f"✅ Workout scheduled successfully.")
                return True
            else:
                logger.warning(f"⚠️ Schedule response unexpected: {response}")
                return False # Might still have worked? But treat as potentially failed.
                
        except Exception as e:
            logger.error(f"❌ Failed to schedule workout: {e}")
            return False
