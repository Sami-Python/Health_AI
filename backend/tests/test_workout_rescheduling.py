
import unittest
from unittest.mock import MagicMock, patch, ANY
import sys
import os

# Ensure backend is in path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# We still need to satisfy imports during main.py load
mock_modules = {
    'firestore_manager': MagicMock(),
    'firestore_garmin_metrics': MagicMock(),
    'notification_service': MagicMock(),
    'ai_coach': MagicMock(),
    'auth_middleware': MagicMock()
}

for mod_name, mock_obj in mock_modules.items():
    if mod_name not in sys.modules:
        sys.modules[mod_name] = mock_obj

import main

class TestWorkoutRescheduling(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user_id = "test_user_678"
        self.workout_id = "test_workout_999"
        self.workout_data = {
            "id": self.workout_id,
            "date": "2026-03-20",
            "activity": "Running",
            "status": "PENDING",
            "type": "planned"
        }

    @patch('main.firestore_garmin_metrics')
    @patch('main.ai_coach')
    @patch('main.notification_service')
    @patch('main.db_manager')
    def test_process_workout_rescheduling_success(self, mock_db, mock_notif, mock_ai, mock_metrics):
        # Setup mocks
        mock_metrics.get_user_daily_metrics.return_value = [
            {"date": "2026-03-16", "bodyBatteryHighestValue": 75, "TSB": -5.2}
        ]
        
        mock_ai.generate_rescheduling_suggestion.return_value = {
            "new_date": "2026-03-22",
            "reasoning": "You need more recovery after recent high load.",
            "push_message": "Siirrettiin juoksu sunnuntaille paremman palautumisen vuoksi."
        }
        
        # Execute
        suggestion = main._process_workout_rescheduling(self.user_id, self.workout_data)
        
        # Verify
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion['new_date'], "2026-03-22")
        
        # Verify status update to SKIPPED
        # Using ANY for the document path components to be flexible but specific about the call
        mock_db.db.collection.assert_called_with('users')
        mock_db.db.collection().document.assert_any_call(self.user_id)
        mock_db.db.collection().document().collection.assert_called_with('workouts')
        mock_db.db.collection().document().collection().document.assert_any_call(self.workout_id)
        
        # Check for update call
        update_call_found = False
        for call in mock_db.db.mock_calls:
            if 'update' in str(call) and "{'status': 'SKIPPED'}" in str(call):
                update_call_found = True
                break
        self.assertTrue(update_call_found, "Firestore update({'status': 'SKIPPED'}) was not called")

    @patch('main.db_manager')
    def test_check_and_reschedule_missed_workout(self, mock_db):
        mock_db.get_last_missed_workout.return_value = self.workout_data
        with patch('main._process_workout_rescheduling') as mock_process:
            main.check_and_reschedule_missed_workout(self.user_id)
            mock_process.assert_called_with(self.user_id, self.workout_data)

    @patch('main.db_manager')
    @patch('main.verify_token')
    async def test_skip_workout_endpoint_success(self, mock_verify, mock_db):
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = self.workout_data
        
        # Setup doc chain
        mock_db.db.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = mock_doc
        
        with patch('main._process_workout_rescheduling') as mock_process:
            mock_process.return_value = {"new_date": "2026-03-22"}
            response = await main.skip_workout_endpoint(self.workout_id, user={'uid': self.user_id})
            self.assertEqual(response['status'], "success")
            self.assertEqual(response['suggestion']['new_date'], "2026-03-22")

if __name__ == '__main__':
    unittest.main()
