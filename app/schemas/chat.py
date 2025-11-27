# app/schemas/chat.py

from pydantic import BaseModel
from typing import List

class ChatRequest(BaseModel):
    query: str
    organization_id: str
    conversation_id: int
    sender: str


class ChatResponse(BaseModel):
    answer: str
    relevant_docs: List[str]
    relevant_questions: List[str]