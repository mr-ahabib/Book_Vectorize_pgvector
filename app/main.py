from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Book Vectorizer")

app.include_router(router)
