"""
Tarihi Yarimada CBS - Configuration
Environment variables and application settings
"""

import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Tarihi Yarimada CBS API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # Cesium
    CESIUM_TOKEN: Optional[str] = None

    # CORS
    ALLOWED_ORIGINS: str = "*"

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Convenience access
settings = get_settings()
