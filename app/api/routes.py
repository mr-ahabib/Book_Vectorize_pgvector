from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from app.schemas.schemas import UploadResponse, SearchRequest, MockTestRequest, MockTestResponse
from app.services.vector_service import process_pdf, semantic_search, get_book_content, generate_mock_questions
import os
import shutil
from datetime import datetime
from app.db.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.book_embedding import BookEmbedding

router = APIRouter()
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    book_id = file.filename
    file_path = os.path.join(UPLOAD_FOLDER, book_id)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(process_pdf, file_path, book_id)

    return UploadResponse(book_id=book_id, status="Processing Started")


@router.post("/search")
async def search(req: SearchRequest):
    results = await semantic_search(req.query, req.top_k)
    return {"results": results}


@router.post("/mock-test", response_model=MockTestResponse)
async def create_mock_test(req: MockTestRequest):
    book_id = req.book_id
    content = await get_book_content(book_id)
    if not content:
        return {"book_id": book_id, "total_questions": 0, "questions": []}

    # Generate MCQs asynchronously
    questions = await generate_mock_questions(content, req.num_questions)

    return MockTestResponse(
        book_id=book_id,
        total_questions=len(questions),
        questions=questions
    )


@router.get("/books")
async def list_books():
    books = []
    async with AsyncSessionLocal() as session:
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if not filename.lower().endswith(".pdf"):
                continue

            size = os.path.getsize(file_path)
            uploaded_time = datetime.fromtimestamp(os.path.getctime(file_path))

            result = await session.execute(
                select(BookEmbedding.id).where(BookEmbedding.book_id == filename)
            )
            processed = result.first() is not None

            books.append({
                "book_id": filename,
                "size_bytes": size,
                "size_mb": round(size / (1024 * 1024), 2),
                "uploaded_at": uploaded_time.isoformat(),
                "status": "Ready" if processed else "Processing"
            })

    return {"books": books}
