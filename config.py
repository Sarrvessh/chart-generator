import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings"""
    APP_NAME = "Chart Generator API"
    APP_VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "False") == "True"

    # File upload settings
    MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES = ['csv', 'json', 'xlsx']
    UPLOAD_DIR = "./uploads"

    # LLM settings
    LLM_MODEL = os.getenv("LLM_MODEL", "phi-3.5-mini-instruct")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:8000/v1")

    # AWS settings (optional)
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET = os.getenv("S3_BUCKET", "")

    # Data validation
    MIN_ROWS_FOR_CHART = 2
    MAX_ROWS_FOR_CHART = 100000

    # CORS settings
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8501",
        "http://localhost:8000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8000",
    ]

settings = Settings()
