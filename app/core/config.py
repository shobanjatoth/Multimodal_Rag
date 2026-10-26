
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Multimodal RAG Pipeline"
    DEBUG: bool = False
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Logger
    LOG_LEVEL: str = "INFO"

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_LOCATION: Optional[str] = None

    # Groq LLM
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # OpenAI-compatible API endpoint used by Groq
    LLM_BASE_URL: str = "https://api.groq.com/openai/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()

