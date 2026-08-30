"""Application configuration loaded from environment variables.

Centralizing settings here means the rest of the app never reads os.environ
directly, which keeps provider/config details out of business logic.
"""
from functools import lru_cache
from typing import List, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"

    # CORS
    backend_cors_origins: str = "http://localhost:3000"

    # Camunda (Phase 2)
    camunda_mode: Literal["mock", "real"] = "mock"
    camunda_zeebe_rest_address: str = "http://localhost:8080"
    camunda_operate_base_url: str = "http://localhost:8081"
    camunda_tasklist_base_url: str = "http://localhost:8082"
    camunda_client_id: str = ""
    camunda_client_secret: str = ""
    camunda_auth_url: str = ""

    # Database
    database_url: str = "postgresql://raguser:ragpassword@localhost:5432/rag_app"

    # LLM provider - configurable without touching app logic
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str = ""
    llm_base_url: str = ""

    # Embedding provider
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_api_key: str = ""

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
