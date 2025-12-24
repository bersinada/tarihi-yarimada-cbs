"""
Tarihi Yarımada CBS - Database Connection
PostGIS veritabanı bağlantısı
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from geoalchemy2 import Geometry
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Database URL (PostgreSQL + PostGIS)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL ortam değişkeni bulunamadı")

# SQLAlchemy Engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency injection için database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Veritabanını başlat ve tabloları oluştur"""
    # PostGIS extension'ı aktifleştir
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.commit()
    
    # Tabloları oluştur
    Base.metadata.create_all(bind=engine)


# ============================================
# SQLAlchemy Models - Diyagrama Göre
# ============================================

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime


class Yapi(Base):
    """YAPI tablosu - Tarihi yapılar"""
    __tablename__ = "yapi"
    
    id = Column(Integer, primary_key=True, index=True)
    ad = Column(String(255), nullable=False, index=True)
    ad_en = Column(String(255))
    tur = Column(String(100), index=True)
    donem = Column(String(100), index=True)
    mimar = Column(String(255))
    yapim_yili = Column(String(50))
    konum = Column(String(255))
    ilce = Column(String(100), index=True)
    aciklama = Column(Text)
    
    # Timestamps
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)
    guncellenme_tarihi = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    yapi_metadata = relationship("YapiMetadata", back_populates="yapi", uselist=False)
    aciklamalar = relationship("Aciklama", back_populates="yapi")


class YapiMetadata(Base):
    """YAPI_METADATA tablosu - 3D veri bilgileri"""
    __tablename__ = "yapi_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    yapi_id = Column(Integer, ForeignKey("yapi.id"), unique=True)
    
    # 3D data URLs
    tileset_url = Column(String(500))
    nokta_bulutu_url = Column(String(500))
    
    # Technical info
    lod_seviyesi = Column(Integer)
    nokta_sayisi = Column(Integer)
    dosya_boyutu_mb = Column(Float)
    
    # Timestamps
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)
    guncellenme_tarihi = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    yapi = relationship("Yapi", back_populates="yapi_metadata")


class Aciklama(Base):
    """AÇIKLAMALAR tablosu - 3D anotasyonlar"""
    __tablename__ = "aciklamalar"
    
    id = Column(Integer, primary_key=True, index=True)
    yapi_id = Column(Integer, ForeignKey("yapi.id"))
    baslik = Column(String(255), nullable=False)
    aciklama = Column(Text)
    
    # 3D pozisyon
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    
    olusturan = Column(String(100))
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    yapi = relationship("Yapi", back_populates="aciklamalar")


class Katman(Base):
    """KATMANLAR tablosu - Harita katmanları"""
    __tablename__ = "katmanlar"
    
    id = Column(Integer, primary_key=True, index=True)
    ad = Column(String(255), nullable=False)
    tur = Column(String(50))  # '3dtiles', 'pointcloud', 'geojson', etc.
    url = Column(String(500))
    gorunur = Column(Boolean, default=True)
    saydamlik = Column(Float, default=1.0)
    sira = Column(Integer, default=0)
    
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)


# SQL script for PostGIS setup
POSTGIS_INIT_SQL = """
-- PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Örnek veri: Molla Hüsrev Camii
INSERT INTO yapi (ad, ad_en, tur, donem, mimar, yapim_yili, konum, ilce, aciklama)
VALUES (
    'Molla Hüsrev Camii',
    'Molla Husrev Mosque',
    'Cami',
    'Osmanlı',
    'Bilinmiyor',
    '1475-1476',
    'Molla Hüsrev, Fatih',
    'Fatih',
    'Fatih döneminde Şeyhülislam Molla Hüsrev tarafından yaptırılmış tarihi cami.'
) ON CONFLICT DO NOTHING;
"""

