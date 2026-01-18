"""
Tarihi Yarimada CBS - Database Connection
PostGIS database connection and session management

Standards:
- Dublin Core (metadata)
- TUCBS Koruma Alanlari (heritage protection)
- ISO 19115 (geographic metadata)
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
# Önce proje kök dizinindeki .env'i dene, sonra backend klasöründekini
env_path = Path(__file__).parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Backend klasöründeki .env'i dene
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()  # Mevcut dizinde .env ara

# Database URL from environment
# Önce local_database_url (küçük harf), sonra LOCAL_DATABASE_URL, sonra DATABASE_URL
DATABASE_URL = (
    os.getenv("local_database_url") or 
    os.getenv("LOCAL_DATABASE_URL") or 
    os.getenv("DATABASE_URL") or
    os.getenv("AZURE_DATABASE_URL")
)

if not DATABASE_URL:
    raise ValueError(
        "Veritabanı URL'i bulunamadı! "
        ".env dosyasında 'local_database_url', 'LOCAL_DATABASE_URL' veya 'DATABASE_URL' tanımlı olmalı."
    )

# SQLAlchemy Engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10"))
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator:
    """Dependency injection for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database with PostGIS extension and create tables"""
    # Enable PostGIS extension
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.commit()

    # Import models to ensure they're registered with Base
    from . import models  # noqa: F401

    # Create all tables
    Base.metadata.create_all(bind=engine)


def check_db_connection() -> bool:
    """Check if database connection is working"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
