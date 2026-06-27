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

    @property
    def cors_origins_list(self) -> list[str]:
        """Virgülle ayrılmış CORS origin'lerini listeye çevirir."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
