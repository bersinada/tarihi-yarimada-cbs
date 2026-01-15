"""
Tarihi Yarimada CBS - Assets API
/api/v1/assets endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import Optional, List

from ..db.database import get_db
from ..db.models import HeritageAsset, AssetSegment, Actor, AssetActor, Media
from ..schemas.asset import (
    AssetCreate, AssetUpdate, AssetResponse, AssetWithLocation,
    AssetFeatureCollection, AssetGeoJSONFeature, AssetGeoJSONProperties,
    GeoJSONGeometry, ActorResponse, MediaResponse, DatasetMetadataResponse
)

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


# ==================================================
# Helper Functions
# ==================================================

def asset_to_response(asset: HeritageAsset, include_location: bool = False) -> dict:
    """Convert HeritageAsset to response dict"""
    segment_count = len(asset.segments) if asset.segments else 0

    response = {
        "id": asset.id,
        "identifier": asset.identifier,
        "name_tr": asset.name_tr,
        "name_en": asset.name_en,
        "asset_type": asset.asset_type,
        "description_tr": asset.description_tr,
        "description_en": asset.description_en,
        "construction_year": asset.construction_year,
        "construction_period": asset.construction_period,
        "historical_period": asset.historical_period,
        "neighborhood": asset.neighborhood,
        "address": asset.address,
        "protection_status": asset.protection_status,
        "registration_no": asset.registration_no,
        "model_url": asset.model_url,
        "model_type": asset.model_type,
        "model_lod": asset.model_lod,
        "is_visitable": asset.is_visitable,
        "data_source": asset.data_source,
        "created_at": asset.created_at,
        "updated_at": asset.updated_at,
        "segment_count": segment_count
    }

    return response


def get_asset_coordinates(db: Session, asset_id: int) -> tuple:
    """Get asset coordinates from PostGIS geometry"""
    result = db.execute(
        text("""
            SELECT ST_X(location) as lon, ST_Y(location) as lat
            FROM heritage_assets WHERE id = :id
        """),
        {"id": asset_id}
    ).fetchone()
    if result:
        return result.lon, result.lat
    return None, None


# ==================================================
# Asset List & Search
# ==================================================

@router.get("", response_model=List[AssetResponse])
async def get_assets(
    asset_type: Optional[str] = None,
    historical_period: Optional[str] = None,
    neighborhood: Optional[str] = None,
    protection_status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get list of heritage assets with optional filtering.

    - **asset_type**: Filter by type (cami, hamam, saray, etc.)
    - **historical_period**: Filter by period (bizans, osmanli_klasik, etc.)
    - **neighborhood**: Filter by neighborhood
    - **protection_status**: Filter by protection status
    - **search**: Search in name fields
    """
    query = db.query(HeritageAsset)

    if asset_type:
        query = query.filter(func.lower(HeritageAsset.asset_type) == asset_type.lower())
    if historical_period:
        query = query.filter(func.lower(HeritageAsset.historical_period) == historical_period.lower())
    if neighborhood:
        query = query.filter(func.lower(HeritageAsset.neighborhood) == neighborhood.lower())
    if protection_status:
        query = query.filter(HeritageAsset.protection_status.ilike(f"%{protection_status}%"))
    if search:
        query = query.filter(
            HeritageAsset.name_tr.ilike(f"%{search}%") |
            HeritageAsset.name_en.ilike(f"%{search}%")
        )

    assets = query.offset(offset).limit(limit).all()
    return [asset_to_response(a) for a in assets]


@router.get("/geojson", response_model=AssetFeatureCollection)
async def get_assets_geojson(
    asset_type: Optional[str] = None,
    historical_period: Optional[str] = None,
    bbox: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get assets as GeoJSON FeatureCollection.

    - **bbox**: Bounding box filter (west,south,east,north)
    """
    # Build query with coordinates
    sql = """
        SELECT
            ha.id, ha.identifier, ha.name_tr, ha.asset_type,
            ha.historical_period, ha.construction_year,
            ha.protection_status, ha.model_type,
            ST_X(ha.location) as lon, ST_Y(ha.location) as lat,
            COUNT(s.id) as segment_count
        FROM heritage_assets ha
        LEFT JOIN asset_segments s ON s.asset_id = ha.id
        WHERE 1=1
    """
    params = {}

    if asset_type:
        sql += " AND LOWER(ha.asset_type) = :asset_type"
        params["asset_type"] = asset_type.lower()

    if historical_period:
        sql += " AND LOWER(ha.historical_period) = :period"
        params["period"] = historical_period.lower()

    if bbox:
        try:
            west, south, east, north = [float(x) for x in bbox.split(",")]
            sql += " AND ST_Within(ha.location, ST_MakeEnvelope(:west, :south, :east, :north, 4326))"
            params.update({"west": west, "south": south, "east": east, "north": north})
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid bbox format. Use: west,south,east,north")

    sql += " GROUP BY ha.id"

    result = db.execute(text(sql), params)
    rows = result.fetchall()

    features = []
    for row in rows:
        feature = AssetGeoJSONFeature(
            id=row.identifier,
            geometry=GeoJSONGeometry(coordinates=[row.lon, row.lat]),
            properties=AssetGeoJSONProperties(
                identifier=row.identifier,
                name_tr=row.name_tr,
                asset_type=row.asset_type,
                historical_period=row.historical_period,
                construction_year=row.construction_year,
                protection_status=row.protection_status,
                model_type=row.model_type,
                segment_count=row.segment_count
            )
        )
        features.append(feature)

    return AssetFeatureCollection(features=features)


# ==================================================
# Single Asset CRUD
# ==================================================

@router.get("/{asset_id}", response_model=AssetWithLocation)
async def get_asset(asset_id: int, db: Session = Depends(get_db)):
    """Get a single heritage asset by ID"""
    asset = db.query(HeritageAsset).filter(HeritageAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    response = asset_to_response(asset)
    lon, lat = get_asset_coordinates(db, asset_id)
    response["longitude"] = lon
    response["latitude"] = lat
    return response


@router.get("/identifier/{identifier}", response_model=AssetWithLocation)
async def get_asset_by_identifier(identifier: str, db: Session = Depends(get_db)):
    """Get a heritage asset by its identifier (e.g., HA-0001)"""
    asset = db.query(HeritageAsset).filter(HeritageAsset.identifier == identifier).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    response = asset_to_response(asset)
    lon, lat = get_asset_coordinates(db, asset.id)
    response["longitude"] = lon
    response["latitude"] = lat
    return response


@router.post("", response_model=AssetResponse, status_code=201)
async def create_asset(asset_data: AssetCreate, db: Session = Depends(get_db)):
    """Create a new heritage asset"""
    # Check if identifier already exists
    existing = db.query(HeritageAsset).filter(
        HeritageAsset.identifier == asset_data.identifier
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Asset with this identifier already exists")

    # Create geometry from coordinates
    location_wkt = f"SRID=4326;POINT({asset_data.longitude} {asset_data.latitude})"

    asset = HeritageAsset(
        identifier=asset_data.identifier,
        name_tr=asset_data.name_tr,
        name_en=asset_data.name_en,
        asset_type=asset_data.asset_type,
        description_tr=asset_data.description_tr,
        description_en=asset_data.description_en,
        construction_year=asset_data.construction_year,
        construction_period=asset_data.construction_period,
        historical_period=asset_data.historical_period,
        location=location_wkt,
        neighborhood=asset_data.neighborhood,
        address=asset_data.address,
        protection_status=asset_data.protection_status,
        registration_no=asset_data.registration_no,
        registration_date=asset_data.registration_date,
        legal_foundation=asset_data.legal_foundation,
        model_url=asset_data.model_url,
        model_type=asset_data.model_type,
        model_lod=asset_data.model_lod,
        is_visitable=asset_data.is_visitable,
        data_source=asset_data.data_source
    )

    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset_to_response(asset)


@router.patch("/{asset_id}", response_model=AssetResponse)
async def update_asset(asset_id: int, asset_data: AssetUpdate, db: Session = Depends(get_db)):
    """Update a heritage asset"""
    asset = db.query(HeritageAsset).filter(HeritageAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    update_data = asset_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)

    db.commit()
    db.refresh(asset)
    return asset_to_response(asset)


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    """Delete a heritage asset"""
    asset = db.query(HeritageAsset).filter(HeritageAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    db.delete(asset)
    db.commit()
    return None


# ==================================================
# Asset Actors
# ==================================================

@router.get("/{asset_id}/actors", response_model=List[ActorResponse])
async def get_asset_actors(asset_id: int, db: Session = Depends(get_db)):
    """Get actors (architects, patrons) associated with an asset"""
    asset = db.query(HeritageAsset).filter(HeritageAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    actors = []
    for asset_actor in asset.actors:
        actor = asset_actor.actor
        actors.append({
            "id": actor.id,
            "identifier": actor.identifier,
            "name_tr": actor.name_tr,
            "name_en": actor.name_en,
            "actor_type": actor.actor_type,
            "bio_tr": actor.bio_tr,
            "birth_year": actor.birth_year,
            "death_year": actor.death_year,
            "role": asset_actor.role
        })
    return actors


# ==================================================
# Asset Media
# ==================================================

@router.get("/{asset_id}/media", response_model=List[MediaResponse])
async def get_asset_media(asset_id: int, db: Session = Depends(get_db)):
    """Get media associated with an asset"""
    asset = db.query(HeritageAsset).filter(HeritageAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    return asset.media


# ==================================================
# Statistics
# ==================================================

@router.get("/stats/summary")
async def get_assets_statistics(db: Session = Depends(get_db)):
    """Get statistics about heritage assets"""
    total = db.query(HeritageAsset).count()

    by_type = db.query(
        HeritageAsset.asset_type,
        func.count(HeritageAsset.id).label("count")
    ).group_by(HeritageAsset.asset_type).all()

    by_period = db.query(
        HeritageAsset.historical_period,
        func.count(HeritageAsset.id).label("count")
    ).group_by(HeritageAsset.historical_period).all()

    by_protection = db.query(
        HeritageAsset.protection_status,
        func.count(HeritageAsset.id).label("count")
    ).group_by(HeritageAsset.protection_status).all()

    return {
        "total_assets": total,
        "by_type": [{"type": t[0], "count": t[1]} for t in by_type if t[0]],
        "by_period": [{"period": p[0], "count": p[1]} for p in by_period if p[0]],
        "by_protection": [{"status": s[0], "count": s[1]} for s in by_protection if s[0]]
    }
