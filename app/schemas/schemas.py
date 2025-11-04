from pydantic import BaseModel
from typing import List
class UploadResponse(BaseModel):
    book_id: str
    status: str

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class Question(BaseModel):
    question: str
    options: List[str]
    answer: str

class MockTestRequest(BaseModel):
    book_id: str
    num_questions: int = 10

class MockTestResponse(BaseModel):
    book_id: str
    total_questions: int
    questions: List[Question]
