import os
from dotenv import load_dotenv

def load_env_vars():
    load_dotenv()
    hf_key = os.getenv("HUGGINGFACE_API_KEY")
    if hf_key and not os.getenv("HF_TOKEN"):
        os.environ["HF_TOKEN"] = hf_key
    return {
        "OLLAMA_API_KEY": os.getenv("OLLAMA_API_KEY"),
        "FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY"),
        "EXA_API_KEY": os.getenv("EXA_API_KEY"),
        "HUGGINGFACE_API_KEY": hf_key,
    }
