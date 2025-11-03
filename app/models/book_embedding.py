from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Text, JSON
from pgvector.sqlalchemy import Vector
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from app.core.config import settings

Base = declarative_base()

class BookEmbedding(Base):
    __tablename__ = "book_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Text, nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    meta_data = Column(JSON, default={})
    embedding = Column(Vector(settings.EMBED_DIM))
    created_at = Column(TIMESTAMP, server_default=func.now())
