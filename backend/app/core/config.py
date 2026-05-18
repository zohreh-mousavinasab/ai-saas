from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "DocMind AI"
    environment: str = "local"
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_chat_model: str = "qwen3.5"
    ollama_embed_model: str = "qwen3-embedding"
    ollama_timeout_seconds: float = 240.0
    ollama_model_chat_timeout_seconds: float = 300.0
    ollama_chat_num_predict: int = 512
    ollama_embed_batch_size: int = 16

    chroma_persist_dir: Path = Field(default=Path("./data/chroma"))
    upload_dir: Path = Field(default=Path("./data/uploads"))
    chat_memory_dir: Path = Field(default=Path("./data/chat_sessions"))
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    current_settings = Settings()
    if not current_settings.upload_dir.is_absolute():
        current_settings.upload_dir = BACKEND_DIR / current_settings.upload_dir
    if not current_settings.chroma_persist_dir.is_absolute():
        current_settings.chroma_persist_dir = BACKEND_DIR / current_settings.chroma_persist_dir
    if not current_settings.chat_memory_dir.is_absolute():
        current_settings.chat_memory_dir = BACKEND_DIR / current_settings.chat_memory_dir
    current_settings.upload_dir.mkdir(parents=True, exist_ok=True)
    current_settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    current_settings.chat_memory_dir.mkdir(parents=True, exist_ok=True)
    return current_settings


settings = get_settings()
