from enum import Enum
from starlette import status

from app.exceptions.errors.CustomClientException import ClientException


class CustomError(Enum):
    CHAT_ENGINE_ERROR = (status.HTTP_500_INTERNAL_SERVER_ERROR, "100", "Chat engine could not initialized")
    INTERNAL_SERVER_ERROR = (status.HTTP_500_INTERNAL_SERVER_ERROR, "101", "Internal server error")
    NOT_FOUND = (status.HTTP_404_NOT_FOUND, "102", "The resource could not be found")
    # …

    def __init__(self, http_status: int, code: str, message: str):
        self.http_status = http_status
        self.code = code
        self.message = message

    def as_exception(self):
        return ClientException(
            status_code=self.http_status,
            code=self.code,
            message=self.message
        )
