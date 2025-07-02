from datetime import datetime
from pydantic import BaseModel


class MessageResponse(BaseModel):
    role: str
    content: str

class MessageCreate(BaseModel):
    session_id: str
    history: list[MessageResponse]
    role: str # user|assistant
    content: str

