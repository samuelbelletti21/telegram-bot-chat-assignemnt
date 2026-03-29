from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class MessageCreate(BaseModel):
    text: str
    direction: Literal["incoming", "outgoing"]

class Message(BaseModel):
    id: str
    text: str
    direction: Literal["incoming", "outgoing"]
    timestamp: datetime
