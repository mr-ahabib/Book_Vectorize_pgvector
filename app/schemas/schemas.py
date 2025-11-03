from pydantic import BaseModel

class UploadResponse(BaseModel):
    book_id: str
    status: str

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
