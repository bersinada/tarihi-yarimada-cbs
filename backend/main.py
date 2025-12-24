"""
Tarihi Yarımada CBS - FastAPI Backend
PostGIS veritabanı ile entegrasyon
Azure App Service için optimize edilmiş
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from sqlalchemy import func
from dotenv import load_dotenv
from pathlib import Path
import os
import json

# .env dosyasını yükle
load_dotenv()

# Proje kök dizini (backend klasörünün bir üstü)
BASE_DIR = Path(__file__).resolve().parent.parent

# Database imports
from backend.database import (
    init_db, get_db, engine,
    Yapi as DBYapi,
    YapiMetadata as DBYapiMetadata,
    Katman as DBKatman,
    Aciklama as DBAciklama,
    IcMekanBolge as DBIcMekanBolge,
    Metadata as DBMetadata
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başlangıcında veritabanını başlat"""
    print("Veritabanı başlatılıyor...")
    try:
        init_db()
        print("Veritabanı tabloları oluşturuldu!")
        # Örnek veri ekle
        add_sample_data()
    except Exception as e:
        print(f"Veritabanı hatası: {e}")
    yield


# FastAPI uygulaması
app = FastAPI(
    title="Tarihi Yarımada CBS API",
    description="İstanbul Tarihi Yarımada Kültürel Miras CBS Platformu API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS ayarları (Frontend erişimi için)
# Production'da ALLOWED_ORIGINS env variable kullanılabilir
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static dosyaları serve et (CSS, JS)
app.mount("/css", StaticFiles(directory=BASE_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=BASE_DIR / "js"), name="js")


# ============================================
# Pydantic Modelleri (Response/Request)
# ============================================

class HealthResponse(BaseModel):
    status: str
    database: str
    version: str


class YapiCreate(BaseModel):
    """Yapı oluşturma modeli"""
    ad: str
    ad_en: Optional[str] = None
    tur: str
    donem: Optional[str] = None
    mimar: Optional[str] = None
    yapim_yili: Optional[str] = None
    konum: str
    ilce: str
    aciklama: Optional[str] = None


class YapiResponse(BaseModel):
    """Yapı response modeli"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    ad: str
    ad_en: Optional[str] = None
    tur: Optional[str] = None
    donem: Optional[str] = None
    mimar: Optional[str] = None
    yapim_yili: Optional[str] = None
    konum: Optional[str] = None
    ilce: Optional[str] = None
    aciklama: Optional[str] = None


class YapiMetadataResponse(BaseModel):
    """Yapı metadata response modeli"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    yapi_id: int
    tileset_url: Optional[str] = None
    nokta_bulutu_url: Optional[str] = None
    lod_seviyesi: Optional[int] = None
    nokta_sayisi: Optional[int] = None
    dosya_boyutu_mb: Optional[float] = None


class KatmanCreate(BaseModel):
    """Katman oluşturma modeli"""
    ad: str
    tur: str
    url: str
    gorunur: bool = True
    saydamlik: float = 1.0


class KatmanResponse(BaseModel):
    """Katman response modeli"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    ad: str
    tur: Optional[str] = None
    url: Optional[str] = None
    gorunur: Optional[bool] = True
    saydamlik: Optional[float] = 1.0
    sira: Optional[int] = 0


class AciklamaCreate(BaseModel):
    """Açıklama oluşturma modeli"""
    yapi_id: int
    baslik: str
    aciklama: Optional[str] = None
    x: float
    y: float
    z: float
    olusturan: Optional[str] = None


class AciklamaResponse(BaseModel):
    """Açıklama response modeli"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    yapi_id: Optional[int] = None
    baslik: str
    aciklama: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    olusturan: Optional[str] = None


# ============================================
# Helper Functions
# ============================================

def yapi_to_response(yapi: DBYapi) -> dict:
    """DBYapi'yi response formatına çevir (TÜCBS uyumlu)"""
    return {
        "id": yapi.id,
        "ad": getattr(yapi, 'bina_adi', None) or getattr(yapi, 'ad', None),
        "bina_adi": getattr(yapi, 'bina_adi', None) or getattr(yapi, 'ad', None),
        "ad_en": yapi.ad_en,
        "tur": yapi.tur,
        "yapi_turu": getattr(yapi, 'yapi_turu', None),
        "donem": yapi.donem,
        "mimar": yapi.mimar,
        "yapim_yili": getattr(yapi, 'insaat_tarihi', None) or getattr(yapi, 'yapim_yili', None),
        "insaat_tarihi": getattr(yapi, 'insaat_tarihi', None) or getattr(yapi, 'yapim_yili', None),
        "konum": yapi.konum,
        "ilce": yapi.ilce,
        "aciklama": yapi.aciklama,
        # INSPIRE/TÜCBS ek alanlar
        "lod_seviyesi": getattr(yapi, 'lod_seviyesi', None),
        "building_nature": getattr(yapi, 'building_nature', None),
        "koruma_grubu": getattr(yapi, 'koruma_grubu', None),
        "land_cover_code": getattr(yapi, 'land_cover_code', None)
    }


def add_sample_data():
    """Örnek veri ekle"""
    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        # Mevcut veri kontrolü (bina_adi sütunuyla)
        existing = db.query(DBYapi).filter(DBYapi.bina_adi == "Molla Hüsrev Camii").first()
        if existing:
            print("Örnek veri zaten mevcut.")
            return
        
        # Molla Hüsrev Camii - TÜCBS ve INSPIRE uyumlu
        yapi = DBYapi(
            bina_adi="Molla Hüsrev Camii",
            ad_en="Molla Husrev Mosque",
            tur="Cami",
            yapi_turu="dini",
            donem="Osmanlı - Fatih Dönemi",
            mimar="Bilinmiyor (Klasik Osmanlı Üslubu)",
            insaat_tarihi="1460",
            konum="Molla Hüsrev Mahallesi, Fatih",
            ilce="Fatih",
            aciklama="Fatih Sultan Mehmed döneminin ünlü Şeyhülislamı Molla Hüsrev tarafından 1460 yılında yaptırılan bu cami, klasik Osmanlı mimarisinin erken dönem örneklerinden biridir.",
            building_nature="mosque",
            lod_seviyesi="LoD3",
            yapi_durumu="kullanilabilir",
            koruma_grubu="I",
            mulkiyet_durumu="vakif",
            mahalle="Molla Hüsrev",
            land_cover_code="1.1.1",
            land_cover_desc="Sürekli Kentsel Yapı"
        )
        db.add(yapi)
        db.commit()
        db.refresh(yapi)
        
        # Metadata ekle - Doğru Cesium Ion Asset ID'leri
        metadata = DBYapiMetadata(
            yapi_id=yapi.id,
            tileset_url="cesium_ion:4270999",  # Dış cephe
            ic_mekan_tileset_url="cesium_ion:4271001",  # İç mekan
            ic_mekan_ion_asset_id=4275532,  # İç mekan point cloud
            lod_seviyesi=3,
            nokta_sayisi=15000000,
            dosya_boyutu_mb=1920.0
        )
        db.add(metadata)
        
        # Örnek katmanlar ekle - Doğru Cesium Ion Asset ID'leri
        katmanlar = [
            DBKatman(ad="Molla Hüsrev - Dış Cephe", tur="3dtiles", url="cesium_ion:4270999", gorunur=True, saydamlik=1.0, sira=1),
            DBKatman(ad="Molla Hüsrev - İç Mekan 1", tur="3dtiles", url="cesium_ion:4271001", gorunur=True, saydamlik=1.0, sira=2),
            DBKatman(ad="Molla Hüsrev - İç Mekan 2", tur="3dtiles", url="cesium_ion:4275532", gorunur=True, saydamlik=1.0, sira=3),
        ]
        for katman in katmanlar:
            db.add(katman)
        
        db.commit()
        print("Örnek veri başarıyla eklendi!")
    except Exception as e:
        print(f"Örnek veri eklenirken hata: {e}")
        db.rollback()
    finally:
        db.close()


# ============================================
# API Endpoints
# ============================================

@app.get("/")
async def root():
    """Ana sayfa - index.html'i serve et"""
    index_path = BASE_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "message": "Tarihi Yarımada CBS API",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """API sağlık kontrolü"""
    try:
        # Veritabanı bağlantısını test et
        db.execute(func.now())
        db_status = "connected"
    except:
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "database": db_status,
        "version": "1.0.0"
    }


# ============================================
# Cesium Config Endpoint
# ============================================

@app.get("/api/cesium-config")
async def get_cesium_config():
    """
    Cesium Ion Access Token'ı güvenli şekilde döndür.
    Frontend bu endpoint'i kullanarak token'a erişir.
    """
    cesium_token = os.getenv("CESIUM_TOKEN")
    
    if not cesium_token:
        raise HTTPException(
            status_code=500, 
            detail="CESIUM_TOKEN ortam değişkeni tanımlanmamış"
        )
    
    return {
        "accessToken": cesium_token,
        "ionAssetEndpoint": "https://api.cesium.com/"
    }


# ============================================
# YAPI Endpoints
# ============================================

@app.get("/api/v1/yapilar", response_model=List[YapiResponse])
async def get_yapilar(
    ilce: Optional[str] = None,
    tur: Optional[str] = None,
    donem: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """Yapı listesini getir"""
    query = db.query(DBYapi)
    
    # Filtreleme
    if ilce:
        query = query.filter(func.lower(DBYapi.ilce) == ilce.lower())
    if tur:
        query = query.filter(func.lower(DBYapi.tur) == tur.lower())
    if donem:
        query = query.filter(func.lower(DBYapi.donem) == donem.lower())
    
    yapilar = query.offset(offset).limit(limit).all()
    return [yapi_to_response(y) for y in yapilar]


@app.get("/api/v1/yapilar/{yapi_id}", response_model=YapiResponse)
async def get_yapi(yapi_id: int, db: Session = Depends(get_db)):
    """Tek bir yapıyı getir"""
    yapi = db.query(DBYapi).filter(DBYapi.id == yapi_id).first()
    if not yapi:
        raise HTTPException(status_code=404, detail="Yapı bulunamadı")
    return yapi_to_response(yapi)


@app.post("/api/v1/yapilar", response_model=YapiResponse)
async def create_yapi(yapi_data: YapiCreate, db: Session = Depends(get_db)):
    """Yeni yapı ekle"""
    yapi = DBYapi(
        ad=yapi_data.ad,
        ad_en=yapi_data.ad_en,
        tur=yapi_data.tur,
        donem=yapi_data.donem,
        mimar=yapi_data.mimar,
        yapim_yili=yapi_data.yapim_yili,
        konum=yapi_data.konum,
        ilce=yapi_data.ilce,
        aciklama=yapi_data.aciklama
    )
    db.add(yapi)
    db.commit()
    db.refresh(yapi)
    return yapi_to_response(yapi)


@app.get("/api/v1/yapilar/{yapi_id}/metadata", response_model=YapiMetadataResponse)
async def get_yapi_metadata(yapi_id: int, db: Session = Depends(get_db)):
    """Yapı metadatasını getir"""
    metadata = db.query(DBYapiMetadata).filter(
        DBYapiMetadata.yapi_id == yapi_id
    ).first()
    if not metadata:
        raise HTTPException(status_code=404, detail="Metadata bulunamadı")
    return metadata


@app.get("/api/v1/yapilar/{yapi_id}/tileset")
async def get_tileset_url(yapi_id: int, db: Session = Depends(get_db)):
    """3D Tiles tileset URL'ini getir"""
    metadata = db.query(DBYapiMetadata).filter(
        DBYapiMetadata.yapi_id == yapi_id
    ).first()
    if not metadata or not metadata.tileset_url:
        raise HTTPException(status_code=404, detail="Tileset bulunamadı")
    return {"url": metadata.tileset_url}


@app.get("/api/v1/yapilar/{yapi_id}/nokta-bulutu")
async def get_pointcloud_url(yapi_id: int, db: Session = Depends(get_db)):
    """Point Cloud URL'ini getir"""
    metadata = db.query(DBYapiMetadata).filter(
        DBYapiMetadata.yapi_id == yapi_id
    ).first()
    if not metadata or not metadata.nokta_bulutu_url:
        raise HTTPException(status_code=404, detail="Nokta bulutu bulunamadı")
    return {"url": metadata.nokta_bulutu_url}


# ============================================
# KATMANLAR Endpoints
# ============================================

@app.get("/api/v1/katmanlar", response_model=List[KatmanResponse])
async def get_katmanlar(db: Session = Depends(get_db)):
    """Katman listesini getir"""
    katmanlar = db.query(DBKatman).order_by(DBKatman.sira).all()
    return katmanlar


@app.get("/api/v1/katmanlar/{katman_id}", response_model=KatmanResponse)
async def get_katman(katman_id: int, db: Session = Depends(get_db)):
    """Katman bilgisini getir"""
    katman = db.query(DBKatman).filter(DBKatman.id == katman_id).first()
    if not katman:
        raise HTTPException(status_code=404, detail="Katman bulunamadı")
    return katman


@app.post("/api/v1/katmanlar", response_model=KatmanResponse)
async def create_katman(katman_data: KatmanCreate, db: Session = Depends(get_db)):
    """Yeni katman ekle"""
    katman = DBKatman(
        ad=katman_data.ad,
        tur=katman_data.tur,
        url=katman_data.url,
        gorunur=katman_data.gorunur,
        saydamlik=katman_data.saydamlik
    )
    db.add(katman)
    db.commit()
    db.refresh(katman)
    return katman


# ============================================
# AÇIKLAMALAR Endpoints
# ============================================

@app.post("/api/v1/aciklamalar", response_model=AciklamaResponse)
async def add_aciklama(aciklama_data: AciklamaCreate, db: Session = Depends(get_db)):
    """Açıklama ekle"""
    aciklama = DBAciklama(
        yapi_id=aciklama_data.yapi_id,
        baslik=aciklama_data.baslik,
        aciklama=aciklama_data.aciklama,
        x=aciklama_data.x,
        y=aciklama_data.y,
        z=aciklama_data.z,
        olusturan=aciklama_data.olusturan
    )
    db.add(aciklama)
    db.commit()
    db.refresh(aciklama)
    return aciklama


@app.get("/api/v1/yapilar/{yapi_id}/aciklamalar", response_model=List[AciklamaResponse])
async def get_aciklamalar(yapi_id: int, db: Session = Depends(get_db)):
    """Yapıya ait açıklamaları getir"""
    aciklamalar = db.query(DBAciklama).filter(
        DBAciklama.yapi_id == yapi_id
    ).all()
    return aciklamalar


# ============================================
# İÇ MEKAN BÖLGELERİ Endpoints
# ============================================

class IcMekanBolgeResponse(BaseModel):
    """İç mekan bölge response modeli"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    yapi_id: Optional[int] = None
    bolge_adi: str
    bolge_adi_en: Optional[str] = None
    bolge_turu: Optional[str] = None
    aciklama: Optional[str] = None
    giris_noktasi: bool = False
    siralama: int = 0
    gezinti_suresi: int = 5
    kamera_lon: Optional[float] = None
    kamera_lat: Optional[float] = None
    kamera_height: Optional[float] = None
    kamera_heading: Optional[float] = 0
    kamera_pitch: Optional[float] = -30
    kamera_roll: Optional[float] = 0
    hedef_lon: Optional[float] = None
    hedef_lat: Optional[float] = None
    hedef_height: Optional[float] = None


@app.get("/api/v1/yapilar/{yapi_id}/ic-mekan-bolgeler", response_model=List[IcMekanBolgeResponse])
async def get_ic_mekan_bolgeler(yapi_id: int, db: Session = Depends(get_db)):
    """Yapının iç mekan bölgelerini getir"""
    try:
        # Raw SQL ile geometri değerlerini çıkar
        from sqlalchemy import text
        query = text("""
            SELECT 
                id, yapi_id, bolge_adi, bolge_adi_en, bolge_turu, aciklama,
                giris_noktasi, siralama, gezinti_suresi,
                ST_X(kamera_pozisyon) as kamera_lon,
                ST_Y(kamera_pozisyon) as kamera_lat,
                ST_Z(kamera_pozisyon) as kamera_height,
                kamera_heading, kamera_pitch, kamera_roll,
                ST_X(kamera_hedef) as hedef_lon,
                ST_Y(kamera_hedef) as hedef_lat,
                ST_Z(kamera_hedef) as hedef_height
            FROM ic_mekan_bolge
            WHERE yapi_id = :yapi_id
            ORDER BY siralama
        """)
        result = db.execute(query, {"yapi_id": yapi_id})
        bolgeler = result.fetchall()
        
        return [
            {
                "id": b.id,
                "yapi_id": b.yapi_id,
                "bolge_adi": b.bolge_adi,
                "bolge_adi_en": b.bolge_adi_en,
                "bolge_turu": b.bolge_turu,
                "aciklama": b.aciklama,
                "giris_noktasi": b.giris_noktasi,
                "siralama": b.siralama,
                "gezinti_suresi": b.gezinti_suresi,
                "kamera_lon": float(b.kamera_lon) if b.kamera_lon else None,
                "kamera_lat": float(b.kamera_lat) if b.kamera_lat else None,
                "kamera_height": float(b.kamera_height) if b.kamera_height else None,
                "kamera_heading": float(b.kamera_heading) if b.kamera_heading else 0,
                "kamera_pitch": float(b.kamera_pitch) if b.kamera_pitch else -30,
                "kamera_roll": float(b.kamera_roll) if b.kamera_roll else 0,
                "hedef_lon": float(b.hedef_lon) if b.hedef_lon else None,
                "hedef_lat": float(b.hedef_lat) if b.hedef_lat else None,
                "hedef_height": float(b.hedef_height) if b.hedef_height else None
            }
            for b in bolgeler
        ]
    except Exception as e:
        print(f"İç mekan bölgeleri yüklenirken hata: {e}")
        return []


@app.get("/api/v1/yapilar/{yapi_id}/ic-mekan-giris")
async def get_ic_mekan_giris(yapi_id: int, db: Session = Depends(get_db)):
    """Yapının iç mekan giriş noktasını getir"""
    try:
        from sqlalchemy import text
        query = text("""
            SELECT 
                id, bolge_adi,
                ST_X(kamera_pozisyon) as lon,
                ST_Y(kamera_pozisyon) as lat,
                ST_Z(kamera_pozisyon) as height,
                kamera_heading as heading,
                kamera_pitch as pitch
            FROM ic_mekan_bolge
            WHERE yapi_id = :yapi_id AND giris_noktasi = TRUE
            ORDER BY siralama
            LIMIT 1
        """)
        result = db.execute(query, {"yapi_id": yapi_id})
        giris = result.fetchone()
        
        if not giris:
            raise HTTPException(status_code=404, detail="Giriş noktası bulunamadı")
        
        return {
            "bolge_id": giris.id,
            "bolge_adi": giris.bolge_adi,
            "lon": float(giris.lon) if giris.lon else None,
            "lat": float(giris.lat) if giris.lat else None,
            "height": float(giris.height) if giris.height else None,
            "heading": float(giris.heading) if giris.heading else 0,
            "pitch": float(giris.pitch) if giris.pitch else -15
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Giriş noktası yüklenirken hata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# INSPIRE/TÜCBS Uyumlu Endpoints
# ============================================

@app.get("/api/v1/inspire/buildings")
async def get_inspire_buildings(db: Session = Depends(get_db)):
    """INSPIRE Buildings formatında yapıları getir"""
    try:
        from sqlalchemy import text
        query = text("""
            SELECT * FROM v_inspire_buildings
        """)
        result = db.execute(query)
        buildings = result.fetchall()
        
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": b.inspire_id if hasattr(b, 'inspire_id') else f"TR.TUCBS.BINA.{b.id}",
                    "properties": {
                        "inspireId": b.inspire_id if hasattr(b, 'inspire_id') else None,
                        "name": b.name if hasattr(b, 'name') else b.bina_adi,
                        "buildingNature": b.building_nature if hasattr(b, 'building_nature') else None,
                        "lodLevel": b.lod_seviyesi if hasattr(b, 'lod_seviyesi') else None,
                        "heightAboveGround": float(b.height_above_ground) if hasattr(b, 'height_above_ground') and b.height_above_ground else None,
                        "numberOfFloorsAboveGround": b.number_of_floors_above_ground if hasattr(b, 'number_of_floors_above_ground') else None
                    }
                }
                for b in buildings
            ]
        }
    except Exception as e:
        print(f"INSPIRE buildings yüklenirken hata: {e}")
        # View yoksa normal yapi tablosundan döndür
        yapilar = db.query(DBYapi).all()
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": f"TR.TUCBS.BINA.{y.id}",
                    "properties": {
                        "name": y.bina_adi if hasattr(y, 'bina_adi') else y.ad,
                        "buildingNature": y.building_nature if hasattr(y, 'building_nature') else None,
                        "lodLevel": y.lod_seviyesi if hasattr(y, 'lod_seviyesi') else None
                    }
                }
                for y in yapilar
            ]
        }


@app.get("/api/v1/tucbs/binalar")
async def get_tucbs_binalar(db: Session = Depends(get_db)):
    """TÜCBS Bina Teması formatında yapıları getir"""
    try:
        from sqlalchemy import text
        query = text("""
            SELECT * FROM v_tucbs_binalar
        """)
        result = db.execute(query)
        binalar = result.fetchall()
        
        return {
            "binalar": [
                {
                    "id": b.id,
                    "bina_adi": b.bina_adi,
                    "yapi_turu": b.yapi_turu,
                    "yapi_durumu": b.yapi_durumu,
                    "bina_yuksekligi": float(b.bina_yuksekligi) if b.bina_yuksekligi else None,
                    "kat_sayisi": b.kat_sayisi,
                    "insaat_tarihi": b.insaat_tarihi,
                    "tescil_no": b.tescil_no,
                    "koruma_grubu": b.koruma_grubu,
                    "mulkiyet_durumu": b.mulkiyet_durumu,
                    "mahalle": b.mahalle,
                    "ilce": b.ilce,
                    "land_cover_code": b.land_cover_code
                }
                for b in binalar
            ]
        }
    except Exception as e:
        print(f"TÜCBS binalar yüklenirken hata: {e}")
        # View yoksa normal yapi tablosundan döndür
        yapilar = db.query(DBYapi).all()
        return {
            "binalar": [yapi_to_response(y) for y in yapilar]
        }


# ============================================
# Geocoding Endpoint
# ============================================

@app.get("/api/v1/ara")
async def geocode(q: str, db: Session = Depends(get_db)):
    """Coğrafi arama"""
    # Önce bina_adi ile ara, sonra ad ile
    yapilar = db.query(DBYapi).filter(
        DBYapi.bina_adi.ilike(f"%{q}%") if hasattr(DBYapi, 'bina_adi') else DBYapi.ad.ilike(f"%{q}%")
    ).all()
    return {"sonuclar": [yapi_to_response(y) for y in yapilar]}


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
