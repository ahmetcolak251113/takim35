"""
Uygulama yapılandırması — Pydantic BaseSettings ile .env okuma.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_PATH: str = "./dijital_gardrop.db"
    GEMINI_API_KEY: Optional[str] = None
    FIREBASE_BUCKET: Optional[str] = None
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8081"
    LLM_PROVIDER: str = "ollama"                           # "ollama" veya "gemini"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    @property
    def cors_origins_list(self) -> list[str]:
        """Virgülle ayrılmış CORS origin'lerini listeye çevirir."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
