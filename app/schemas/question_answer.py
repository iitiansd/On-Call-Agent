from pydantic import BaseModel
from typing import Union

class QuestionAnswerCreate(BaseModel):
    question: str
    answer: str
    organization_id: str

class QuestionAnswerSearch(BaseModel):
    query: str
    organization_id: str

class QuestionAnswerResponse(BaseModel):
    id: str
    question: str
    answer: str
    organization_id: str
    relevance_score: Union[float, None] = None