
---

## 📌 README.md

```markdown
# 📚 Book Vectorization & Semantic Search System

A FastAPI-based system that allows users to upload books (PDF), automatically extract and vectorize the content using OpenAI embeddings, and perform semantic search over stored chapters/pages.  
Processing is handled asynchronously in the background so the user doesn’t have to wait.

---

## ✅ Features

- Upload a PDF book through API
- Background task extracts text from PDF + generates vector embeddings
- Stores embeddings into PostgreSQL + pgvector
- Use semantic search to retrieve relevant text segments
- Prevents duplicate re-processing of already processed books
- Supports encrypted PDFs (via PyCryptodome)
- Scales efficiently using parallel requests

---

## 🛠️ Tech Stack

| Component | Technology |
|----------|------------|
| Backend API | FastAPI |
| Database | PostgreSQL + pgvector extension |
| ORM | SQLAlchemy Async |
| AI Embeddings | OpenAI (text-embedding-3-small) |
| PDF Parsing | PyPDF2 |
| Background Tasks | Starlette BackgroundTasks |

---

---

## 🧩 Installation

### ✅ Requirements

✔ Python >= 3.10  
✔ PostgreSQL installed  
✔ pgvector extension enabled

---

### ✅ Create & Activate Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
````

---

### ✅ Install Dependencies

```bash
pip install -r requirements.txt
```

Make sure you also install:

```bash
pip install pycryptodome
```

(required for encrypted PDFs ✅)

---

## 🗄️ Database Setup

Login to PostgreSQL shell and enable **pgvector**:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Run migrations (or create table manually if already included):

```sql
CREATE TABLE book_embeddings (
    id SERIAL PRIMARY KEY,
    book_id TEXT NOT NULL,
    chunk_index INT NOT NULL,
    content TEXT,
    embedding vector(1536)
);
```

---

## 🔑 Environment Variables

Create a **.env** file:

```
OPENAI_API_KEY=your_api_key_here
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/bookdb
```

---

## 🚀 Run Server

```bash
uvicorn main:app --reload
```

> API available at: [http://127.0.0.1:8000](http://127.0.0.1:8000)
> Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📌 API Usage

### 📤 Upload a PDF

```
POST /upload
```

Response example:

```json
{
  "book_id": "your_book.pdf",
  "status": "Processing Started"
}
```

### 🔍 Semantic Search

```
POST /search
```

Request body:

```json
{
  "query": "rheumatoid arthritis treatment",
  "top_k": 5
}
```

Response contains most relevant text chunks.

---

## ✅ Background Processing Status

All extracted vectors are stored in DB.
Check DB records or logs for processing completion:

```bash
SELECT COUNT(*) FROM book_embeddings WHERE book_id='your_book.pdf';
```

If embeddings exist → ✅ processing completed.

---

## ✨ Future Enhancements

* Frontend UI (Next.js) for upload/search
* Progress tracking endpoint
* Chapter-level classification (easy/medium/hard)
* Redis queue for workload scaling

---
