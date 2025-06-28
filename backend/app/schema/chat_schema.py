from datetime import datetime
from pydantic import BaseModel



class MessageCreate(BaseModel):
    role: str # user|assistant
    content: str

class MessageResponse(BaseModel):
    role: str
    content: str
    timestamp: datetime