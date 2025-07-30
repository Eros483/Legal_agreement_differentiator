from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    session_id: str
    system_prompt: Optional[str]=None

class ChatResponse(BaseModel):
    response: str
    session_id: str