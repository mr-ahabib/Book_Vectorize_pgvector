from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from app.schemas.schemas import UploadResponse, SearchRequest
from app.services.vector_service import process_pdf, semantic_search
import os
import shutil



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
