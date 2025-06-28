from fastapi import HTTPException, status
from typing import Any, Dict, Optional


class ClientException(HTTPException):
    def __init__(self, status_code: int, code: str, message: str = None):
        super().__init__(status_code=status_code, detail=message)
        self.code = code