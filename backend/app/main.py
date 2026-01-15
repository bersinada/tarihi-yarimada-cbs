"""
Tarihi Yarimada CBS - FastAPI Backend
Clean Architecture implementation with PostGIS integration

Standards:
- Dublin Core (metadata)
- TUCBS Koruma Alanlari (heritage protection)
- ISO 19115 (geographic metadata)
- OGC WFS 2.0 (web feature service)
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from sqlalchemy import text
from pathlib import Path
import os

from dotenv import load_dotenv
load_dotenv()

from .db.database import init_db, get_db, check_db_connection
from .db.models import DatasetMetadata
from .api import assets_router, segments_router, notes_router, ogc_router

# Project root directory (one level up from backend)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle - initialize database on startup"""
    print("Initializing database...")
    try:
        init_db()
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Database initialization error: {e}")
    yield


# FastAPI application
app = FastAPI(
    title="Tarihi Yarimada CBS API",
    description="""
Istanbul Tarihi Yarimada Kulturel Miras CBS Platformu API

## Features
- Heritage asset management (CRUD)
- SAM3D segment integration
- OGC WFS 2.0 compatible endpoints
- GeoJSON output format

## Standards
- Dublin Core (metadata)
- TUCBS Koruma Alanlari
- ISO 19115 (geographic metadata)
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(assets_router)
app.include_router(segments_router)
app.include_router(notes_router)
app.include_router(ogc_router)

# Static files (CSS, JS) - only if directories exist
css_path = BASE_DIR / "css"
js_path = BASE_DIR / "js"

if css_path.exists():
    app.mount("/css", StaticFiles(directory=css_path), name="css")
if js_path.exists():
    app.mount("/js", StaticFiles(directory=js_path), name="js")


# ==================================================
# Root & Health Endpoints
# ==================================================

@app.get("/")
async def root():
    """Root endpoint - serve index.html or API info"""
    index_path = BASE_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "message": "Tarihi Yarimada CBS API",
        "version": "2.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/api/v1/health")
async def health_check(db: Session = Depends(get_db)):
    """API health check endpoint"""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy",
        "database": db_status,
        "version": "2.0.0"
    }


# ==================================================
# Cesium Configuration
# ==================================================

@app.get("/api/cesium-config")
async def get_cesium_config():
    """
    Return Cesium Ion Access Token securely.
    Frontend uses this endpoint to get the token.
    """
    cesium_token = os.getenv("CESIUM_TOKEN")

    if not cesium_token:
        raise HTTPException(
            status_code=500,
            detail="CESIUM_TOKEN environment variable is not set"
        )

    return {
        "accessToken": cesium_token,
        "ionAssetEndpoint": "https://api.cesium.com/"
    }


# ==================================================
# Dataset Metadata (ISO 19115)
# ==================================================

@app.get("/api/v1/metadata")
async def get_dataset_metadata(db: Session = Depends(get_db)):
    """Get dataset-level metadata (ISO 19115)"""
    metadata = db.query(DatasetMetadata).first()

    if not metadata:
        return {
            "title": "Istanbul Tarihi Yarimada Kulturel Miras Envanteri",
            "abstract": "Henuz metadata kaydedilmemis",
            "metadata_standard": "ISO 19115:2014"
        }

    return {
        "id": metadata.id,
        "title": metadata.title,
        "abstract": metadata.abstract,
        "purpose": metadata.purpose,
        "language": metadata.language,
        "spatial_extent": {
            "west_bound": metadata.west_bound,
            "east_bound": metadata.east_bound,
            "south_bound": metadata.south_bound,
            "north_bound": metadata.north_bound,
            "coordinate_system": metadata.coordinate_system
        },
        "temporal_extent": {
            "begin": metadata.temporal_begin.isoformat() if metadata.temporal_begin else None,
            "end": metadata.temporal_end.isoformat() if metadata.temporal_end else None
        },
        "data_quality": {
            "lineage": metadata.lineage,
            "spatial_resolution": metadata.spatial_resolution
        },
        "distribution": {
            "format": metadata.distribution_format,
            "access_url": metadata.access_url
        },
        "contact": {
            "name": metadata.contact_name,
            "email": metadata.contact_email,
            "organization": metadata.contact_organization
        },
        "constraints": {
            "use_constraints": metadata.use_constraints,
            "license": metadata.license
        },
        "metadata_info": {
            "date": metadata.metadata_date.isoformat() if metadata.metadata_date else None,
            "standard": metadata.metadata_standard
        }
    }


# ==================================================
# Search Endpoint
# ==================================================

@app.get("/api/v1/search")
async def search(
    q: str,
    db: Session = Depends(get_db)
):
    """
    Search across heritage assets by name.

    - **q**: Search query string
    """
    from .db.models import HeritageAsset

    assets = db.query(HeritageAsset).filter(
        HeritageAsset.name_tr.ilike(f"%{q}%") |
        HeritageAsset.name_en.ilike(f"%{q}%")
    ).limit(20).all()

    results = []
    for asset in assets:
        # Get coordinates
        coords = db.execute(
            text("SELECT ST_X(location) as lon, ST_Y(location) as lat FROM heritage_assets WHERE id = :id"),
            {"id": asset.id}
        ).fetchone()

        results.append({
            "id": asset.id,
            "identifier": asset.identifier,
            "name_tr": asset.name_tr,
            "name_en": asset.name_en,
            "asset_type": asset.asset_type,
            "longitude": coords.lon if coords else None,
            "latitude": coords.lat if coords else None
        })

    return {"results": results, "count": len(results)}


# ==================================================
# Main Entry Point
# ==================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
