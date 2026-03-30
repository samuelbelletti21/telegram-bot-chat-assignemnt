from datetime import datetime
from pydantic import BaseModel, field_validator

from app.const import Direction


class MessageCreate(BaseModel):
    text: str
    direction: Direction

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message text cannot be empty or whitespace")
        return v

class Message(BaseModel):
    id: str
    text: str
    direction: Direction
    timestamp: datetime
