"""
Veritabanı başlatma scripti
.env dosyasındaki local_database_url veya DATABASE_URL kullanarak
PostGIS extension'ını ekler ve tüm tabloları oluşturur.
"""

import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

# .env dosyasını yükle
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Backend klasöründeki .env'i dene
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()  # Mevcut dizinde .env ara

# Python'un 'app' modülünü bulabilmesi için mevcut dizini listeye ekliyoruz
sys.path.append(str(Path(__file__).parent))

# Database URL'i al - önce local_database_url (küçük harf), sonra LOCAL_DATABASE_URL, sonra DATABASE_URL
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

# database.py modülü DATABASE_URL bekliyor, environment variable olarak set et
os.environ["DATABASE_URL"] = DATABASE_URL

print(f"Veritabanı bağlantısı: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")

# SQLAlchemy Engine oluştur
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False  # SQL sorgularını gösterme
)

# Modelleri import et (Base'e kaydolmaları için)
# database.py'den Base'i al (artık DATABASE_URL set edildi)
from app.db.database import Base  # noqa: E402
from app.db import models  # noqa: E402, F401


def init_database():
    """PostGIS extension'ını ekle ve tüm tabloları oluştur"""
    print("\n" + "="*60)
    print("Veritabanı başlatılıyor...")
    print("="*60)
    
    try:
        # PostGIS extension'ını ekle
        print("\n[1/2] PostGIS extension kontrol ediliyor...")
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.commit()
        print("[OK] PostGIS extension hazır")
        
        # Tüm tabloları oluştur
        print("\n[2/2] Veritabanı tabloları oluşturuluyor...")
        Base.metadata.create_all(bind=engine)
        
        print("\n" + "="*60)
        print("[OK] Veritabanı başarıyla güncellendi!")
        print("="*60)
        print("\nOluşturulan tablolar:")
        print("  - heritage_assets (Ana kültürel miras varlıkları)")
        print("  - asset_segments (3D model segmentleri)")
        print("  - dataset_metadata (ISO 19115 metadata)")
        print("  - actors (Mimarlar ve patronlar)")
        print("  - asset_actors (Varlık-Aktör ilişkileri)")
        print("  - media (Medya dosyaları)")
        print("  - user_notes (Kullanıcı notları)")
        print("\n")
        
    except Exception as e:
        print("\n" + "="*60)
        print("[HATA] HATA OLUŞTU!")
        print("="*60)
        print(f"Hata mesajı: {e}")
        print("\nKontrol edin:")
        print("  1. PostgreSQL servisi çalışıyor mu?")
        print("  2. Veritabanı URL'i doğru mu?")
        print("  3. Kullanıcı adı ve şifre doğru mu?")
        print("  4. Veritabanı mevcut mu?")
        sys.exit(1)


if __name__ == "__main__":
    init_database()