from uuid import UUID

from pydantic import BaseModel


class ChatCommand(BaseModel):
    session_id: UUID
    message: str
