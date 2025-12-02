import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    HF_TOKEN = os.getenv("HF_TOKEN")
    BASE_MODEL_PATH = "./models/base/qwen-2.5-3b-instruct"
    ADAPTER_TR_PATH = "./adapters/tr_chat"
    ADAPTER_PYTHON_PATH = "./adapters/python_coder"
    CHROMA_PERSIST_DIR = "./data/chromadb"
    LOG_DIR = "./logs"
    
settings = Settings()
