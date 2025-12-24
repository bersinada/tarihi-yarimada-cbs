"""
Tarihi Yarımada CBS - Database Connection
PostGIS veritabanı bağlantısı

Standartlar:
- INSPIRE Annex III (Buildings)
- TÜCBS Bina Teması v2.0
- ISO 19115/19139 (Metadata)
- CORINE Arazi Örtüsü
"""

from sqlalchemy import create_engine, text, Enum
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Date, Numeric, ARRAY
from sqlalchemy.dialects.postgresql import UUID, ARRAY as PG_ARRAY
from geoalchemy2 import Geometry
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
import enum

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
        # Not: postgis_topology ve uuid-ossp Azure'da izin gerektiriyor
        # conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_topology;"))
        # conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
        conn.commit()
    
    # Tabloları oluştur
    Base.metadata.create_all(bind=engine)


# ============================================
# ENUM Tipleri (INSPIRE & TÜCBS)
# ============================================

class LodSeviyesiEnum(enum.Enum):
    """INSPIRE LoD Seviyeleri"""
    LOD0 = "LoD0"  # Taban/Çatı poligonları
    LOD1 = "LoD1"  # Blok modeller
    LOD2 = "LoD2"  # Çatı yapısı belirgin
    LOD3 = "LoD3"  # Detaylı mimari
    LOD4 = "LoD4"  # İç mekan dahil


class YapiTuruEnum(enum.Enum):
    """TÜCBS Yapı Türleri"""
    KONUT = "konut"
    TICARI = "ticari"
    SANAYI = "sanayi"
    RESMI = "resmi"
    EGITIM = "egitim"
    SAGLIK = "saglik"
    DINI = "dini"
    KULTUREL = "kulturel"
    TARIHI = "tarihi"
    ANIT = "anit"
    ASKERI = "askeri"
    DIGER = "diger"


class YapiDurumuEnum(enum.Enum):
    """TÜCBS Yapı Durumu"""
    KULLANILABILIR = "kullanilabilir"
    ONARIM_GEREKLI = "onarim_gerekli"
    RESTORASYON_ALTINDA = "restorasyon_altinda"
    HARAP = "harap"
    YIKILMIS = "yikilmis"
    INSAAT_HALINDE = "insaat_halinde"


class BuildingNatureEnum(enum.Enum):
    """INSPIRE Building Nature"""
    ARCH = "arch"
    BUNKER = "bunker"
    CASTLE = "castle"
    CAVE_BUILDING = "caveBuilding"
    CHAPEL = "chapel"
    CHURCH = "church"
    MOSQUE = "mosque"
    SYNAGOGUE = "synagogue"
    TOWER = "tower"
    LIGHTHOUSE = "lighthouse"
    MONUMENT = "monument"
    WINDMILL = "windmill"
    RELIGIOUS_BUILDING = "religiousBuilding"
    HISTORIC_BUILDING = "historicBuilding"
    OTHER = "other"


class MulkiyetDurumuEnum(enum.Enum):
    """TÜCBS Mülkiyet Durumu"""
    KAMU = "kamu"
    OZEL = "ozel"
    VAKIF = "vakif"
    KARMA = "karma"
    BELIRSIZ = "belirsiz"


class GuncellemeFrekansiEnum(enum.Enum):
    """ISO 19115 Güncelleme Frekansı"""
    SUREKLI = "surekli"
    GUNLUK = "gunluk"
    HAFTALIK = "haftalik"
    ONBESGUNLUK = "onbesgunluk"
    AYLIK = "aylik"
    UC_AYLIK = "uc_aylik"
    ALTI_AYLIK = "alti_aylik"
    YILLIK = "yillik"
    GEREKTIGINDE = "gerektiginde"
    DUZENSIZ = "duzensiz"
    PLANLANMAMIS = "planlanmamis"
    BILINMIYOR = "bilinmiyor"


class ErisimKisitlamasiEnum(enum.Enum):
    """ISO 19115 Erişim Kısıtlaması"""
    ACIK = "acik"
    SINIRLI = "sinirli"
    TELIF_HAKKI = "telif_hakki"
    PATENT = "patent"
    TICARI_GIZLILIK = "ticari_gizlilik"
    LISANS = "lisans"
    FIKRI_MULKIYET = "fikri_mulkiyet"
    KISITLANMIS = "kisitlanmis"
    DIGER = "diger"


# ============================================
# SQLAlchemy Models - INSPIRE/TÜCBS Uyumlu
# ============================================

class Yapi(Base):
    """
    YAPI tablosu - Tarihi yapılar
    TÜCBS Bina Teması v2.0 + INSPIRE Buildings uyumlu
    """
    __tablename__ = "yapi"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # ===== Temel Bilgiler =====
    bina_adi = Column(String(255), nullable=False, index=True)  # TÜCBS: bina_adi
    ad_en = Column(String(255))  # İngilizce isim
    tur = Column(String(100), index=True)  # Legacy (eski)
    donem = Column(String(100), index=True)
    mimar = Column(String(255))
    insaat_tarihi = Column(String(50))  # TÜCBS: insaat_tarihi (yapim_yili'den dönüştürüldü)
    konum = Column(String(255))
    ilce = Column(String(100), index=True)
    aciklama = Column(Text)
    
    # ===== PostGIS Geometri (EPSG:4326) =====
    geom = Column(Geometry('POINTZ', srid=4326))  # Ana konum
    lod_0_footprint = Column(Geometry('POLYGON', srid=4326))  # Taban izi
    lod_0_roofedge = Column(Geometry('POLYGON', srid=4326))  # Çatı izi
    
    # ===== INSPIRE ID =====
    inspire_namespace = Column(String(100), default='TR.TUCBS.BINA')
    inspire_local_id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    inspire_version_id = Column(String(50))
    
    # ===== TÜCBS SoyutYapi Öznitelikleri =====
    yapi_turu = Column(String(50), default='dini')  # YapiTuruEnum
    yapi_durumu = Column(String(50), default='kullanilabilir')  # YapiDurumuEnum
    tescil_no = Column(String(50))
    tescil_tarihi = Column(Date)
    koruma_grubu = Column(String(20))
    
    # ===== TÜCBS SoyutBina Öznitelikleri =====
    bina_yuksekligi = Column(Numeric(6, 2))  # Metre
    kat_sayisi = Column(Integer)
    bodrum_kat_sayisi = Column(Integer, default=0)
    yapi_alani = Column(Numeric(12, 2))  # m²
    toplam_insaat_alani = Column(Numeric(12, 2))  # m²
    cephe_uzunlugu = Column(Numeric(8, 2))  # Metre
    
    # ===== INSPIRE Building Öznitelikleri =====
    building_nature = Column(String(50), default='mosque')  # BuildingNatureEnum
    lod_seviyesi = Column(String(10), default='LoD3')  # LodSeviyesiEnum
    
    # ===== Mülkiyet ve Adres =====
    mulkiyet_durumu = Column(String(20), default='vakif')  # MulkiyetDurumuEnum
    malik_adi = Column(String(255))
    ada_no = Column(String(20))
    parsel_no = Column(String(20))
    mahalle = Column(String(100))
    sokak = Column(String(255))
    kapi_no = Column(String(20))
    posta_kodu = Column(String(10))
    
    # ===== CORINE Arazi Örtüsü =====
    land_cover_code = Column(String(10))  # Örn: "1.1.1"
    land_cover_desc = Column(String(255))  # Örn: "Sürekli Kentsel Yapı"
    
    # ===== Çok Dilli Destek =====
    building_name_en = Column(String(255))
    description_en = Column(Text)
    
    # ===== Timestamps =====
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)
    guncellenme_tarihi = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ===== Relationships =====
    yapi_metadata = relationship("YapiMetadata", back_populates="yapi", uselist=False)
    aciklamalar = relationship("Aciklama", back_populates="yapi")
    # Not: Aşağıdaki ilişkiler migration sonrası aktif edilecek
    # ic_mekan_bolgeler = relationship("IcMekanBolge", back_populates="yapi")
    # metadata_kayitlari = relationship("Metadata", back_populates="yapi")
    
    @property
    def inspire_id(self):
        """INSPIRE tam ID"""
        return f"{self.inspire_namespace}.{self.inspire_local_id}"


class YapiMetadata(Base):
    """YAPI_METADATA tablosu - 3D veri bilgileri"""
    __tablename__ = "yapi_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    yapi_id = Column(Integer, ForeignKey("yapi.id"), unique=True)
    
    # 3D data URLs - Dış Cephe
    tileset_url = Column(String(500))
    nokta_bulutu_url = Column(String(500))
    
    # 3D data URLs - İç Mekan (Cesium)
    ic_mekan_tileset_url = Column(String(500))
    ic_mekan_ion_asset_id = Column(Integer)
    
    # Geometri referans noktaları
    merkez_nokta = Column(Geometry('POINTZ', srid=4326))
    giris_noktasi = Column(Geometry('POINTZ', srid=4326))
    
    # Technical info
    lod_seviyesi = Column(Integer)
    nokta_sayisi = Column(Integer)
    dosya_boyutu_mb = Column(Float)
    
    # Timestamps
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)
    guncellenme_tarihi = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    yapi = relationship("Yapi", back_populates="yapi_metadata")


class IcMekanBolge(Base):
    """
    İç Mekan Bölge tablosu - Cesium iç mekan navigasyonu için
    Yapının iç mekan bölgelerini/odalarını tanımlar
    """
    __tablename__ = "ic_mekan_bolge"
    
    id = Column(Integer, primary_key=True, index=True)
    yapi_id = Column(Integer, ForeignKey("yapi.id"))
    
    # Bölge tanımlama
    bolge_adi = Column(String(255), nullable=False)
    bolge_adi_en = Column(String(255))
    bolge_turu = Column(String(50))  # 'giris', 'ana_mekan', 'galeri', 'koridor' vb.
    aciklama = Column(Text)
    
    # 3D Pozisyon (Cesium için)
    geom = Column(Geometry('POINTZ', srid=4326))  # Merkez noktası
    kamera_pozisyon = Column(Geometry('POINTZ', srid=4326))  # Kameranın bakış noktası
    kamera_hedef = Column(Geometry('POINTZ', srid=4326))  # Kameranın baktığı nokta
    kamera_heading = Column(Numeric(6, 2), default=0)  # Derece
    kamera_pitch = Column(Numeric(6, 2), default=-30)  # Derece
    kamera_roll = Column(Numeric(6, 2), default=0)  # Derece
    
    # Navigasyon
    giris_noktasi = Column(Boolean, default=False)  # Giriş kapısı noktası mı?
    siralama = Column(Integer, default=0)  # Tur sıralaması
    gezinti_suresi = Column(Integer, default=5)  # Saniye cinsinden bekleme süresi
    
    # 3D Tiles/Model referansı
    tileset_url = Column(String(500))
    cesium_ion_asset_id = Column(Integer)
    
    # Bağlantılar (komşu bölgeler)
    bagli_bolgeler = Column(PG_ARRAY(Integer))
    
    # Timestamps
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)
    guncellenme_tarihi = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Not: Relationships migration sonrası aktif edilecek
    # yapi = relationship("Yapi", back_populates="ic_mekan_bolgeler")
    # aciklamalar = relationship("Aciklama", back_populates="ic_mekan_bolge")


class IcMekanRota(Base):
    """İç Mekan Rota tablosu - Önceden tanımlı tur rotaları"""
    __tablename__ = "ic_mekan_rota"
    
    id = Column(Integer, primary_key=True, index=True)
    yapi_id = Column(Integer, ForeignKey("yapi.id"))
    
    rota_adi = Column(String(255), nullable=False)
    rota_adi_en = Column(String(255))
    aciklama = Column(Text)
    
    # Rota bölgeleri (sıralı)
    bolge_siralamasi = Column(PG_ARRAY(Integer), nullable=False)  # ic_mekan_bolge ID'leri
    
    # Rota özellikleri
    toplam_sure = Column(Integer)  # Saniye
    zorluk_seviyesi = Column(String(20), default='kolay')
    engelli_erisimi = Column(Boolean, default=True)
    
    # Timestamps
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)


class Aciklama(Base):
    """AÇIKLAMALAR tablosu - 3D anotasyonlar"""
    __tablename__ = "aciklamalar"
    
    id = Column(Integer, primary_key=True, index=True)
    yapi_id = Column(Integer, ForeignKey("yapi.id"))
    # Not: ic_mekan_bolge_id migration sonrası aktif edilecek
    # ic_mekan_bolge_id = Column(Integer, ForeignKey("ic_mekan_bolge.id"))
    
    baslik = Column(String(255), nullable=False)
    aciklama = Column(Text)
    
    # 3D pozisyon (x, y, z ayrı)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    
    # Not: geom sütunu migration sonrası aktif edilecek
    # geom = Column(Geometry('POINTZ', srid=4326))
    
    olusturan = Column(String(100))
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    yapi = relationship("Yapi", back_populates="aciklamalar")
    # ic_mekan_bolge = relationship("IcMekanBolge", back_populates="aciklamalar")


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
    
    # Not: Aşağıdaki sütunlar migration sonrası aktif edilecek
    # ic_mekan = Column(Boolean, default=False)
    # cesium_ion_asset_id = Column(Integer)
    # baslangic_kamera_pozisyon = Column(Geometry('POINTZ', srid=4326))
    
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)
    
    # Relationships - Migration sonrası aktif edilecek
    # metadata_kayitlari = relationship("Metadata", back_populates="katman")


class Metadata(Base):
    """
    ISO 19115/19139 uyumlu Metadata tablosu
    Veri kalitesi, sorumlusu, güncelleme frekansı ve erişim kısıtlamaları
    """
    __tablename__ = "metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # İlişkilendirme
    yapi_id = Column(Integer, ForeignKey("yapi.id"))
    katman_id = Column(Integer, ForeignKey("katmanlar.id"))
    ic_mekan_bolge_id = Column(Integer, ForeignKey("ic_mekan_bolge.id"))
    
    # ===== MD_Identification - Tanımlama =====
    baslik = Column(String(500), nullable=False)
    baslik_en = Column(String(500))
    ozet = Column(Text)
    ozet_en = Column(Text)
    amac = Column(Text)
    anahtar_kelimeler = Column(PG_ARRAY(String))
    
    # ===== MD_DataIdentification =====
    dil = Column(String(10), default='tur')  # ISO 639-2
    karakter_seti = Column(String(20), default='utf8')
    konu_kategorisi = Column(String(50), default='structure')
    
    # ===== Coğrafi Kapsam (EX_GeographicBoundingBox) =====
    bbox_west = Column(Numeric(10, 6))
    bbox_east = Column(Numeric(10, 6))
    bbox_south = Column(Numeric(10, 6))
    bbox_north = Column(Numeric(10, 6))
    
    # ===== Zamansal Kapsam =====
    zamansal_baslangic = Column(Date)
    zamansal_bitis = Column(Date)
    
    # ===== CI_Citation - Kaynak Bilgisi =====
    kaynak_adi = Column(String(255))
    kaynak_tarihi = Column(Date)
    kaynak_turu = Column(String(50))  # 'creation', 'publication', 'revision'
    
    # ===== DQ_DataQuality - Veri Kalitesi =====
    kalite_seviyesi = Column(String(50), default='dataset')
    kalite_aciklama = Column(Text)  # Lineage
    konum_dogrulugu = Column(Numeric(8, 4))  # Metre
    tamamlanma_orani = Column(Numeric(5, 2))  # Yüzde (0-100)
    
    # ===== MD_Constraints - Kısıtlamalar =====
    erisim_kisitlamasi = Column(String(50), default='acik')  # ErisimKisitlamasiEnum
    kullanim_kisitlamasi = Column(Text)
    diger_kisitlamalar = Column(Text)
    
    # ===== CI_ResponsibleParty - Sorumlu Taraf =====
    sorumlu_kisi = Column(String(255))
    sorumlu_kurum = Column(String(255))
    sorumlu_email = Column(String(255))
    sorumlu_telefon = Column(String(50))
    sorumlu_rol = Column(String(50), default='pointOfContact')
    
    # ===== MD_MaintenanceInformation - Bakım Bilgisi =====
    guncelleme_frekansi = Column(String(50), default='gerektiginde')  # GuncellemeFrekansiEnum
    son_guncelleme_tarihi = Column(DateTime)
    sonraki_guncelleme_tarihi = Column(Date)
    bakim_notu = Column(Text)
    
    # ===== MD_Distribution - Dağıtım Bilgisi =====
    dagitim_formati = Column(String(100))
    dagitim_boyutu = Column(Numeric(12, 2))  # MB
    erisim_url = Column(String(500))
    
    # ===== INSPIRE Spesifik =====
    inspire_tema = Column(String(100), default='Buildings')
    inspire_uyumlu = Column(Boolean, default=True)
    tucbs_uyumlu = Column(Boolean, default=True)
    
    # ===== Timestamps =====
    metadata_olusturma_tarihi = Column(DateTime, default=datetime.utcnow)
    metadata_guncelleme_tarihi = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Not: Relationships migration sonrası aktif edilecek
    # yapi = relationship("Yapi", back_populates="metadata_kayitlari")
    # katman = relationship("Katman", back_populates="metadata_kayitlari")


class CorineAraziOrtusu(Base):
    """CORINE Arazi Örtüsü referans tablosu"""
    __tablename__ = "corine_arazi_ortusi"
    
    id = Column(Integer, primary_key=True, index=True)
    kod = Column(String(10), unique=True, nullable=False)  # "1.1.1", "1.2.1" vb.
    seviye_1 = Column(String(100))  # Ana sınıf
    seviye_2 = Column(String(100))  # Alt sınıf
    seviye_3 = Column(String(100))  # Detay
    aciklama = Column(Text)
    renk_kodu = Column(String(7))  # HEX renk kodu


# SQL script for PostGIS setup (Legacy - for initial setup)
POSTGIS_INIT_SQL = """
-- PostGIS extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
"""
