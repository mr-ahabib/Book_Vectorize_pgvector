import asyncio
import re
import json
from sqlalchemy import select, text
from app.db.database import AsyncSessionLocal
from app.models.book_embedding import BookEmbedding
from app.core.config import settings
from app.utils.pdf_extractor import extract_text
from openai import OpenAI

# Initialize new OpenAI client (v1 API)
client = OpenAI(api_key=settings.OPENAI_API_KEY)


def chunk_text(text: str, size: int = 1600, overlap: int = 300):
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


# -------------------- Embeddings -------------------- #
async def get_embedding(chunk: str):
    """Fetch embedding for a single chunk asynchronously."""
    response = await client.embeddings.acreate(
        model="text-embedding-3-small",
        input=chunk
    )
    return chunk, response.data[0].embedding


async def process_pdf(file_path: str, book_id: str):
    """Extract text, create embeddings, and store them in DB."""
    print(f"Processing started: {book_id}")

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    text_content = extract_text(file_bytes)
    chunks = chunk_text(text_content)
    print(f"Total chunks: {len(chunks)}")

    # Create embeddings in parallel
    results = await asyncio.gather(*(get_embedding(chunk) for chunk in chunks))

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

    print(f"Embeddings stored successfully: {book_id}")


async def semantic_search(query: str, top_k: int = 5):
    """Vector search using pgvector similarity."""
    query_emb = (await client.embeddings.acreate(
        model="text-embedding-3-small",
        input=query
    )).data[0].embedding

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BookEmbedding.content)
            .order_by(BookEmbedding.embedding.op("<->")(query_emb))
            .limit(top_k)
        )
        return result.scalars().all()


# -------------------- Book content -------------------- #
async def get_book_content(book_id: str):
    """Return main textbook content (skip front matter)."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BookEmbedding.content)
            .where(BookEmbedding.book_id == book_id)
            .order_by(BookEmbedding.chunk_index)
        )
        texts = [t for t in result.scalars().all() if t.strip()]

    # Skip first 1–3 chunks (usually front matter)
    content_chunks = texts[3:] if len(texts) > 3 else texts
    content = " ".join(content_chunks)
    content = re.sub(r'\s+', ' ', content).strip()
    return content if content else None


# -------------------- Question Generation -------------------- #
async def generate_questions_from_chunk(chunk: str):
    """Generate MCQs from a single chunk using OpenAI API asynchronously."""
    prompt = f"""
You are a strict JSON generator.

Generate multiple-choice questions (MCQs)
ONLY from the medical textbook content below.

CONTENT:
\"\"\"
{chunk}
\"\"\"

IMPORTANT:
- Do NOT generate questions about authors, publishers, ISBNs, or disclaimers.
- Use ONLY actual textbook content: concepts, explanations, examples, diseases, treatments.
- Output ONLY valid JSON, no markdown or extra text.
- Exactly 4 options per question.
- Format:
[
  {{"question": "...", "options": ["A","B","C","D"], "answer": "A"}}
]
"""

    # Run synchronous GPT call in a thread to keep FastAPI async
    def sync_call():
        return client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )

    response = await asyncio.to_thread(sync_call)

    try:
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"JSON parse error: {e}")
        return []


async def generate_mock_questions(content: str, num_questions: int = None):
    """Generate MCQs from the full textbook content in parallel."""
    chunk_size = 30000
    overlap = 500
    chunks = []
    start = 0
    while start < len(content):
        end = start + chunk_size
        chunks.append(content[start:end])
        start = end - overlap

    all_questions = []

    tasks = [generate_questions_from_chunk(chunk) for chunk in chunks]

    for future in asyncio.as_completed(tasks):
        chunk_questions = await future
        all_questions.extend(chunk_questions)

    # If num_questions is set, trim the list
    if num_questions is not None:
        return all_questions[:num_questions]
    return all_questions

