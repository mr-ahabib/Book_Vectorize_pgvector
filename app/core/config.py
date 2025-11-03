import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    EMBED_DIM: int = int(os.getenv("EMBED_DIM", 1536))

settings = Settings()
