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
from database import (
    init_db, get_db, engine,
    Yapi as DBYapi,
    YapiMetadata as DBYapiMetadata,
    Katman as DBKatman,
    Aciklama as DBAciklama
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
    """DBYapi'yi response formatına çevir"""
    return {
        "id": yapi.id,
        "ad": yapi.ad,
        "ad_en": yapi.ad_en,
        "tur": yapi.tur,
        "donem": yapi.donem,
        "mimar": yapi.mimar,
        "yapim_yili": yapi.yapim_yili,
        "konum": yapi.konum,
        "ilce": yapi.ilce,
        "aciklama": yapi.aciklama
    }


def add_sample_data():
    """Örnek veri ekle"""
    from database import SessionLocal
    db = SessionLocal()
    try:
        # Mevcut veri kontrolü
        existing = db.query(DBYapi).filter(DBYapi.ad == "Molla Hüsrev Camii").first()
        if existing:
            print("Örnek veri zaten mevcut.")
            return
        
        # Molla Hüsrev Camii
        yapi = DBYapi(
            ad="Molla Hüsrev Camii",
            ad_en="Molla Husrev Mosque",
            tur="Cami",
            donem="Osmanlı",
            mimar="Bilinmiyor",
            yapim_yili="1475-1476",
            konum="Molla Hüsrev, Fatih",
            ilce="Fatih",
            aciklama="Fatih döneminde Şeyhülislam Molla Hüsrev tarafından yaptırılmış tarihi cami."
        )
        db.add(yapi)
        db.commit()
        db.refresh(yapi)
        
        # Metadata ekle
        metadata = DBYapiMetadata(
            yapi_id=yapi.id,
            tileset_url="cesium_ion:4270999",
            nokta_bulutu_url="/data/pointcloud/molla-husrev/metadata.json",
            lod_seviyesi=3,
            nokta_sayisi=15000000,
            dosya_boyutu_mb=1920.0
        )
        db.add(metadata)
        
        # Örnek katmanlar ekle
        katmanlar = [
            DBKatman(ad="Molla Hüsrev - Dış Cephe", tur="3dtiles", url="cesium_ion:4270999", gorunur=True, saydamlik=1.0, sira=1),
            DBKatman(ad="Molla Hüsrev - İç Mekan", tur="pointcloud", url="/data/pointcloud/molla-husrev/metadata.json", gorunur=True, saydamlik=1.0, sira=2),
            DBKatman(ad="Çevre LoD0 Modeli", tur="3dtiles", url="/data/3dtiles/context/tileset.json", gorunur=True, saydamlik=0.8, sira=3),
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
# Geocoding Endpoint
# ============================================

@app.get("/api/v1/ara")
async def geocode(q: str, db: Session = Depends(get_db)):
    """Coğrafi arama"""
    yapilar = db.query(DBYapi).filter(
        DBYapi.ad.ilike(f"%{q}%")
    ).all()
    return {"sonuclar": [yapi_to_response(y) for y in yapilar]}


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
