"""
Tarihi Yarimada CBS - OGC API
/api/v1/ogc endpoints for OGC WFS 2.0 compatibility
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from ..db.database import get_db
from ..db.models import HeritageAsset, AssetSegment

router = APIRouter(prefix="/api/v1/ogc", tags=["ogc"])


# ==================================================
# WFS GetCapabilities
# ==================================================

@router.get("/wfs/capabilities")
async def get_capabilities():
    """
    WFS 2.0 GetCapabilities - Returns service metadata

    Returns information about available feature types and operations.
    """
    return {
        "service": "WFS",
        "version": "2.0.0",
        "title": "Tarihi Yarimada CBS WFS Servisi",
        "abstract": "Istanbul Tarihi Yarimada kulturel miras yapilarinin WFS servisi",
        "keywords": ["kulturel miras", "heritage", "istanbul", "tarihi yarimada", "cbs", "gis"],
        "provider": {
            "name": "Tarihi Yarimada CBS",
            "site": "https://tarihi-yarimada-cbs.example.com"
        },
        "operations": [
            {"name": "GetCapabilities", "url": "/api/v1/ogc/wfs/capabilities"},
            {"name": "GetFeature", "url": "/api/v1/ogc/wfs"}
        ],
        "featureTypes": [
            {
                "name": "heritage_assets",
                "title": "Kulturel Miras Yapilari",
                "abstract": "Tarihi yarimadaki tescilli kulturel miras yapilari",
                "defaultCRS": "EPSG:4326",
                "outputFormats": ["application/json", "application/geo+json"]
            },
            {
                "name": "asset_segments",
                "title": "Yapi Segmentleri (SAM3D)",
                "abstract": "SAM3D ile segmente edilmis 3D model parcalari",
                "defaultCRS": "EPSG:4326",
                "outputFormats": ["application/json"]
            }
        ],
        "filterCapabilities": {
            "spatialOperators": ["BBOX", "Within", "Intersects"],
            "comparisonOperators": ["EqualTo", "Like"]
        }
    }


# ==================================================
# WFS GetFeature
# ==================================================

@router.get("/wfs")
async def wfs_get_feature(
    service: str = Query("WFS"),
    request: str = Query("GetFeature"),
    typeName: str = Query("heritage_assets"),
    outputFormat: str = Query("application/json"),
    srsName: str = Query("EPSG:4326"),
    bbox: Optional[str] = Query(None, description="Bounding box: west,south,east,north"),
    propertyName: Optional[str] = Query(None, description="Comma-separated property names"),
    maxFeatures: int = Query(100, le=1000),
    startIndex: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    OGC WFS 2.0 GetFeature - Simplified implementation

    Returns features as GeoJSON FeatureCollection.

    Parameters:
    - **service**: Service type (WFS)
    - **request**: Request type (GetFeature)
    - **typeName**: Feature type (heritage_assets or asset_segments)
    - **outputFormat**: Output format (application/json)
    - **srsName**: Coordinate reference system
    - **bbox**: Bounding box filter (west,south,east,north)
    - **maxFeatures**: Maximum number of features to return
    - **startIndex**: Starting index for pagination
    """

    if typeName == "heritage_assets":
        return await _get_heritage_assets_wfs(
            db, bbox, maxFeatures, startIndex, srsName
        )
    elif typeName == "asset_segments":
        return await _get_segments_wfs(db, maxFeatures, startIndex)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown typeName: {typeName}. Available types: heritage_assets, asset_segments"
        )


async def _get_heritage_assets_wfs(
    db: Session,
    bbox: Optional[str],
    max_features: int,
    start_index: int,
    srs_name: str
) -> dict:
    """Get heritage assets as WFS GeoJSON"""

    sql = """
        SELECT
            ha.id,
            ha.identifier,
            ha.name_tr,
            ha.name_en,
            ha.asset_type,
            ha.historical_period,
            ha.construction_year,
            ha.construction_period,
            ha.neighborhood,
            ha.protection_status,
            ha.model_type,
            ha.model_url,
            ha.is_visitable,
            ST_X(ha.location) as longitude,
            ST_Y(ha.location) as latitude,
            COUNT(s.id) as segment_count
        FROM heritage_assets ha
        LEFT JOIN asset_segments s ON s.asset_id = ha.id
        WHERE 1=1
    """
    params = {}

    # Apply bbox filter
    if bbox:
        try:
            west, south, east, north = [float(x.strip()) for x in bbox.split(",")]
            sql += " AND ST_Within(ha.location, ST_MakeEnvelope(:west, :south, :east, :north, 4326))"
            params.update({
                "west": west,
                "south": south,
                "east": east,
                "north": north
            })
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid bbox format. Expected: west,south,east,north"
            )

    sql += " GROUP BY ha.id"
    sql += f" ORDER BY ha.id LIMIT :limit OFFSET :offset"
    params["limit"] = max_features
    params["offset"] = start_index

    result = db.execute(text(sql), params)
    rows = result.fetchall()

    # Build GeoJSON FeatureCollection
    features = []
    for row in rows:
        feature = {
            "type": "Feature",
            "id": row.identifier,
            "geometry": {
                "type": "Point",
                "coordinates": [row.longitude, row.latitude]
            },
            "properties": {
                "identifier": row.identifier,
                "name_tr": row.name_tr,
                "name_en": row.name_en,
                "asset_type": row.asset_type,
                "historical_period": row.historical_period,
                "construction_year": row.construction_year,
                "construction_period": row.construction_period,
                "neighborhood": row.neighborhood,
                "protection_status": row.protection_status,
                "model_type": row.model_type,
                "model_url": row.model_url,
                "is_visitable": row.is_visitable,
                "segment_count": row.segment_count
            }
        }
        features.append(feature)

    # Get total count
    count_sql = "SELECT COUNT(*) FROM heritage_assets"
    if bbox:
        count_sql += " WHERE ST_Within(location, ST_MakeEnvelope(:west, :south, :east, :north, 4326))"
    total_count = db.execute(text(count_sql), params).scalar()

    return {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {"name": srs_name}
        },
        "numberMatched": total_count,
        "numberReturned": len(features),
        "features": features
    }


async def _get_segments_wfs(
    db: Session,
    max_features: int,
    start_index: int
) -> dict:
    """Get asset segments as WFS response"""

    segments = db.query(AssetSegment).offset(start_index).limit(max_features).all()
    total_count = db.query(AssetSegment).count()

    features = []
    for seg in segments:
        feature = {
            "type": "Feature",
            "id": f"SEG-{seg.id:04d}",
            "properties": {
                "id": seg.id,
                "asset_id": seg.asset_id,
                "segment_name": seg.segment_name,
                "segment_type": seg.segment_type,
                "object_id": seg.object_id,
                "material": seg.material,
                "height_m": seg.height_m,
                "width_m": seg.width_m,
                "volume_m3": seg.volume_m3,
                "condition": seg.condition,
                "restoration_year": seg.restoration_year,
                "description_tr": seg.description_tr
            }
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "numberMatched": total_count,
        "numberReturned": len(features),
        "features": features
    }


# ==================================================
# DescribeFeatureType
# ==================================================

@router.get("/wfs/describe")
async def describe_feature_type(
    typeName: str = Query("heritage_assets")
):
    """
    WFS DescribeFeatureType - Returns schema information

    Returns the structure and properties of a feature type.
    """

    if typeName == "heritage_assets":
        return {
            "typeName": "heritage_assets",
            "properties": {
                "identifier": {"type": "string", "maxLength": 20, "description": "Unique identifier (e.g., HA-0001)"},
                "name_tr": {"type": "string", "maxLength": 255, "description": "Turkish name"},
                "name_en": {"type": "string", "maxLength": 255, "description": "English name"},
                "asset_type": {"type": "string", "maxLength": 50, "description": "Asset type (cami, hamam, saray, etc.)"},
                "historical_period": {"type": "string", "maxLength": 50, "description": "Historical period"},
                "construction_year": {"type": "integer", "description": "Construction year"},
                "construction_period": {"type": "string", "description": "Construction period range"},
                "neighborhood": {"type": "string", "maxLength": 100, "description": "Neighborhood"},
                "protection_status": {"type": "string", "maxLength": 50, "description": "Protection status"},
                "model_type": {"type": "string", "description": "3D model type (SPLAT, MESH, 3DTILES)"},
                "model_url": {"type": "string", "description": "URL to 3D model"},
                "is_visitable": {"type": "boolean", "description": "Whether asset is visitable"},
                "segment_count": {"type": "integer", "description": "Number of SAM3D segments"}
            },
            "geometry": {
                "type": "Point",
                "srid": 4326
            }
        }
    elif typeName == "asset_segments":
        return {
            "typeName": "asset_segments",
            "properties": {
                "id": {"type": "integer", "description": "Segment ID"},
                "asset_id": {"type": "integer", "description": "Parent asset ID"},
                "segment_name": {"type": "string", "description": "Segment name"},
                "segment_type": {"type": "string", "description": "Type (dome, minaret, portal, etc.)"},
                "object_id": {"type": "string", "description": "Object ID in 3D model"},
                "material": {"type": "string", "description": "Material"},
                "height_m": {"type": "number", "description": "Height in meters"},
                "width_m": {"type": "number", "description": "Width in meters"},
                "volume_m3": {"type": "number", "description": "Volume in cubic meters"},
                "condition": {"type": "string", "description": "Condition (original, restored, damaged)"},
                "restoration_year": {"type": "integer", "description": "Year of restoration"}
            }
        }
    else:
        raise HTTPException(status_code=400, detail=f"Unknown typeName: {typeName}")
