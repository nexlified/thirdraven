from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+asyncpg://thirdraven:secret@localhost:5432/thirdraven_db"
    )
    secret_key: str = "changeme"
    access_token_expire_minutes: int = 1440
    algorithm: str = "HS256"
    raven_ollama_url: str | None = None  # e.g. http://localhost:11434
    raven_model: str = "llama3.2"


@lru_cache
def get_settings() -> Settings:
    return Settings()
