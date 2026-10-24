import os
from pathlib import Path
from dotenv import load_dotenv

_env_file = Path(__file__).resolve().parent.parent / ".env"
if _env_file.exists():
    load_dotenv(_env_file)
else:
    load_dotenv()


OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "https://ollama.com/v1")
OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "ollama")
MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-oss:120b-cloud")
MAX_TURNS: int = int(os.getenv("MAX_TURNS", "60"))
MAX_TOOL_CALLS: int = int(os.getenv("MAX_TOOL_CALLS", "50"))
FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY", "").strip()
FIRECRAWL_BASE_URL: str = os.getenv("FIRECRAWL_BASE_URL", "https://api.firecrawl.dev").strip()
