import asyncio
import openai
from sqlalchemy import text, select
from app.db.database import AsyncSessionLocal
from app.models.book_embedding import BookEmbedding
from app.core.config import settings
from app.utils.pdf_extractor import extract_text


openai.api_key = settings.OPENAI_API_KEY


def chunk_text(text, size=1600, overlap=300):
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


async def get_embedding(chunk):
    """Fetch embedding for a single chunk."""
    response = openai.embeddings.create(
        model="text-embedding-3-small",  
        input=chunk
    )
    emb = response.data[0].embedding
    return chunk, emb


async def process_pdf(file_path: str, book_id: str):
    """Process PDF: extract, chunk, embed, and store embeddings in parallel."""
    print(f"Processing started for: {book_id}")


    with open(file_path, "rb") as f:
        file_bytes = f.read()

    text_content = extract_text(file_bytes)
    chunks = chunk_text(text_content)

    print(f"Total chunks: {len(chunks)}")

    tasks = [get_embedding(chunk) for chunk in chunks]
    results = await asyncio.gather(*tasks)

    async with AsyncSessionLocal() as session:
        for idx, (chunk, emb) in enumerate(results):
            session.add(BookEmbedding(
                book_id=book_id,
                chunk_index=idx,
                content=chunk,
                embedding=emb
            ))

        await session.commit()
        await session.execute(text("ANALYZE book_embeddings;"))
        await session.commit()

    print(f"Embeddings stored successfully for: {book_id}")


async def semantic_search(query: str, top_k: int = 5):
    """Perform vector search using pgvector similarity."""
    query_emb = openai.embeddings.create(
        model="text-embedding-3-small",
        input=query
    ).data[0].embedding

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BookEmbedding.content)
            .order_by(BookEmbedding.embedding.op("<->")(query_emb))
            .limit(top_k)
        )
        return result.scalars().all()
