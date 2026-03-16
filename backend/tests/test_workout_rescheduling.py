
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import asyncio

# Mock dependencies before importing main
mock_db_manager = MagicMock()
mock_firestore_metrics = MagicMock()
mock_notification_service = MagicMock()
mock_ai_coach = MagicMock()

sys.modules['firestore_manager'] = mock_db_manager
sys.modules['db_manager'] = mock_db_manager
sys.modules['firestore_garmin_metrics'] = mock_firestore_metrics
sys.modules['notification_service'] = MagicMock()
sys.modules['notification_service'].notification_service = mock_notification_service
sys.modules['ai_coach'] = mock_ai_coach

# Now import the functions to test
sys.path.append(os.path.join(os.getcwd(), 'backend'))
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
        
    @patch('main.logger')
    def test_process_workout_rescheduling_success(self, mock_logger):
        # Setup mocks
        mock_firestore_metrics.get_user_daily_metrics.return_value = [
            {"date": "2026-03-16", "bodyBatteryHighestValue": 75, "TSB": -5.2}
        ]
        
        mock_ai_coach.generate_rescheduling_suggestion.return_value = {
            "new_date": "2026-03-22",
            "reasoning": "You need more recovery after recent high load.",
            "push_message": "Siirrettiin juoksu sunnuntaille paremman palautumisen vuoksi."
        }
        
        # Execute
        try:
            suggestion = main._process_workout_rescheduling(self.user_id, self.workout_data)
        except Exception as e:
            print(f"Exception caught in test: {e}")
            suggestion = None
        
        # Verify
        if suggestion is None:
             print(f"Suggestion is None. mock_ai_coach.generate_rescheduling_suggestion status: {mock_ai_coach.generate_rescheduling_suggestion.called}")
        
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion['new_date'], "2026-03-22")
        
        # Verify status update to SKIPPED
        mock_db_manager.db.collection().document().collection().document().update.assert_called()
        
    @patch('main.db_manager')
    def test_check_and_reschedule_missed_workout(self, mock_main_db):
        mock_main_db.get_last_missed_workout.return_value = self.workout_data
        with patch('main._process_workout_rescheduling') as mock_process:
            main.check_and_reschedule_missed_workout(self.user_id)
            mock_process.assert_called_with(self.user_id, self.workout_data)

    @patch('main.verify_token')
    async def test_skip_workout_endpoint_success(self, mock_verify):
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = self.workout_data
        mock_db_manager.db.collection().document().collection().document().get.return_value = mock_doc
        
        with patch('main._process_workout_rescheduling') as mock_process:
            mock_process.return_value = {"new_date": "2026-03-22"}
            response = await main.skip_workout_endpoint(self.workout_id, user={'uid': self.user_id})
            self.assertEqual(response['status'], "success")
            self.assertEqual(response['suggestion']['new_date'], "2026-03-22")

if __name__ == '__main__':
    unittest.main()
