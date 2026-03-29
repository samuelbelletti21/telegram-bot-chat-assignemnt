from datetime import datetime
from pydantic import BaseModel

from app.const import Direction


class MessageCreate(BaseModel):
    text: str
    direction: Direction

class Message(BaseModel):
    id: str
    text: str
    direction: Direction
    timestamp: datetime
