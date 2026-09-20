"""Application configuration loaded from environment variables.

Centralizing settings here means the rest of the app never reads os.environ
directly, which keeps provider/config details out of business logic.
"""
from functools import lru_cache
from pathlib import Path
from typing import List, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"

    # CORS
    backend_cors_origins: str = "http://localhost:4200,http://127.0.0.1:4200"

    # Camunda
    camunda_mode: Literal["real"] = "real"
    camunda_operate_base_url: str = "http://localhost:8080/v2"
    camunda_mcp_server_url: str = ""
    camunda_mcp_transport: Literal["streamable_http", "sse"] = "streamable_http"

    # Database
    database_url: str = "postgresql://raguser:ragpassword@localhost:5432/rag_app"

    # LLM provider
    llm_model: str = "gemini-3.6-flash"
    llm_api_key: str | None = None
    chat_message_word_limit: int = Field(default=500, gt=0)

    # Embedding provider
    embedding_model: str = "gemini-embedding-2"
    embedding_api_key: str | None = None
    embedding_dimensions: int = 1024
    vectorstore_table: str = "vectorstore"
    document_chunk_size: int = 800
    document_chunk_overlap: int = 120

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
