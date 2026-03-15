from firebase_admin import messaging
from logger import logger
import firestore_manager as db_manager

class NotificationService:
    @staticmethod
    def send_push_notification(user_id: str, title: str, body: str, data: dict = None):
        """
        Sends a push notification to a specific user via FCM.
        """
        try:
            # 1. Get user's FCM token from Firestore
            fcm_token = db_manager.get_fcm_token(user_id)
            if not fcm_token:
                logger.warning(f"No FCM token found for user {user_id}. Skipping notification.")
                return False

            # 2. Construct message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=fcm_token,
            )

            # 3. Send message
            response = messaging.send(message)
            logger.info(f"Successfully sent message to user {user_id}: {response}")
            return True

        except Exception as e:
            logger.error(f"Error sending push notification to user {user_id}: {e}")
            return False

notification_service = NotificationService()
