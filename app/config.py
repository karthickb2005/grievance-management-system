import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # Database
    DATABASE_URL: str = "sqlite:///./grievance_router.db"

    # ML Models
    EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"
    FAISS_INDEX_PATH: str = "./data/faiss_index.bin"

    # Geo
    MERGE_RADIUS_METERS: int = 150
    ALERT_THRESHOLD_COUNT: int = 5
    ALERT_WINDOW_HOURS: int = 24

    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    FRONTEND_DIR: Path = BASE_DIR / "frontend"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(exist_ok=True)
settings.FRONTEND_DIR.mkdir(exist_ok=True)
