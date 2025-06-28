from app.exceptions.custom_error import CustomError
from typing import Optional, Dict, Any, List


class ChatbotRepository:
    def __init__(self):
        pass

    def post_message(self, session_id: str, role: str, content: str):
        try:
            i = 1 # dummy
        except Exception as e:
            print(f"Error posting message: {str(e)}")
            raise CustomError.INTERNAL_SERVER_ERROR.as_exception(f"Failed to post message: {str(e)}")

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        try:
            i = 1 # dummy
            return []
        except Exception as e:
            print(f"Error getting messages: {str(e)}")
            return []
