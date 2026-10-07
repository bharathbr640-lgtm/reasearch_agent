import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "https://ollama.com/v1")
OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "ollama")
MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-oss:120b-cloud")
MAX_TURNS: int = int(os.getenv("MAX_TURNS", "60"))
MAX_TOOL_CALLS: int = int(os.getenv("MAX_TOOL_CALLS", "30"))
