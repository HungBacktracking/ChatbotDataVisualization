import os
from typing import List

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

ENV: str = ""


class Configs(BaseSettings):
    ENV: str = os.getenv("ENV", "dev")
    API: str = "/api"
    API_V1_STR: str = "/api/v1"
    API_V2_STR: str = "/api/v2"
    PROJECT_NAME: str = "NavigaTech"
    ENV_DATABASE_MAPPER: dict = {
        "prod": "prod",
        "dev": "dev",
        "test": "test",
        "local": "local",
    }
    DB_ENGINE_MAPPER: dict = {
        "postgresql": "postgresql",
        "mysql": "mysql+pymysql",
    }

    PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    DATETIME_FORMAT: str = "%Y-%m-%dT%H:%M:%S"
    DATE_FORMAT: str = "%Y-%m-%d"

    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 60 minutes * 24 hours * 30 days = 30 days

    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    QDRANT_URL: str = os.getenv("QDRANT_URL")
    QDRANT_API_TOKEN: str = os.getenv("QDRANT_API_TOKEN")
    QDRANT_COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION_NAME")


    HF_TOKEN: str = os.getenv("HF_TOKEN")
    GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-pro")
    GEMINI_TOKEN: str = os.getenv("GEMINI_TOKEN")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", 10240))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", 0.6))
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "intfloat/multilingual-e5-large")
    SCORING_MODEL_NAME: str = os.getenv("SCORING_MODEL_NAME", "all-mpnet-base-v2")

    TOP_K: int = int(os.getenv("TOP_K", 15))
    TOKEN_LIMIT: int = int(os.getenv("TOKEN_LIMIT", 20048))

    COHERE_API_TOKEN: str = os.getenv("COHERE_API_TOKEN")

    PAGE: int = 1
    PAGE_SIZE: int = 20
    ORDERING: str = "-id"


    class Config:
        case_sensitive = True


class TestConfigs(Configs):
    ENV: str = "test"


configs = Configs()

if ENV == "prod":
    pass
elif ENV == "stage":
    pass
elif ENV == "test":
    setting = TestConfigs()
