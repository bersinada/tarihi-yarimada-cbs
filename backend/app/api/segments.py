"""
Tarihi Yarimada CBS - Segments API
/api/v1/segments endpoints for SAM3D integration
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List

from ..db.database import get_db
from ..db.models import AssetSegment, HeritageAsset
from ..schemas.segment import (
    SegmentCreate, SegmentUpdate, SegmentResponse,
    SegmentWithAsset, SegmentStatistics, SegmentTypeCount
)

router = APIRouter(prefix="/api/v1/segments", tags=["segments"])


# ==================================================
# Segment Types Reference
# ==================================================

SEGMENT_TYPES = {
    "dome": "Kubbe",
    "minaret": "Minare",
    "portal": "Tackapi/Giris",
    "wall": "Duvar",
    "window": "Pencere",
    "courtyard": "Avlu",
    "fountain": "Sadirvan",
    "column": "Sutun",
    "arch": "Kemer",
    "roof": "Cati",
    "other": "Diger"
}


# ==================================================
# List & Search Segments
# ==================================================

@router.get("", response_model=List[SegmentResponse])
async def get_segments(
    asset_id: Optional[int] = None,
    segment_type: Optional[str] = None,
    condition: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get list of segments with optional filtering.

    - **asset_id**: Filter by parent asset
    - **segment_type**: Filter by type (dome, minaret, portal, etc.)
    - **condition**: Filter by condition (original, restored, damaged)
    """
    query = db.query(AssetSegment)

    if asset_id:
        query = query.filter(AssetSegment.asset_id == asset_id)
    if segment_type:
        query = query.filter(func.lower(AssetSegment.segment_type) == segment_type.lower())
    if condition:
        query = query.filter(func.lower(AssetSegment.condition) == condition.lower())

    segments = query.offset(offset).limit(limit).all()
    return segments


@router.get("/types")
async def get_segment_types():
    """Get list of available segment types with Turkish translations"""
    return {
        "types": [
            {"code": code, "name_tr": name_tr}
            for code, name_tr in SEGMENT_TYPES.items()
        ]
    }


@router.get("/by-asset/{asset_id}", response_model=List[SegmentResponse])
async def get_segments_by_asset(
    asset_id: int,
    segment_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all segments for a specific asset"""
    # Check if asset exists
    asset = db.query(HeritageAsset).filter(HeritageAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    query = db.query(AssetSegment).filter(AssetSegment.asset_id == asset_id)

    if segment_type:
        query = query.filter(func.lower(AssetSegment.segment_type) == segment_type.lower())

    return query.all()


# ==================================================
# Single Segment CRUD
# ==================================================

@router.get("/{segment_id}", response_model=SegmentWithAsset)
async def get_segment(segment_id: int, db: Session = Depends(get_db)):
    """Get a single segment by ID"""
    segment = db.query(AssetSegment).filter(AssetSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    # Get asset info
    asset = segment.asset

    return {
        **segment.__dict__,
        "asset_name_tr": asset.name_tr if asset else None,
        "asset_identifier": asset.identifier if asset else None
    }


@router.post("", response_model=SegmentResponse, status_code=201)
async def create_segment(segment_data: SegmentCreate, db: Session = Depends(get_db)):
    """Create a new segment for an asset"""
    # Check if asset exists
    asset = db.query(HeritageAsset).filter(HeritageAsset.id == segment_data.asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Validate segment type
    if segment_data.segment_type.lower() not in SEGMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid segment type. Valid types: {list(SEGMENT_TYPES.keys())}"
        )

    segment = AssetSegment(
        asset_id=segment_data.asset_id,
        segment_name=segment_data.segment_name,
        segment_type=segment_data.segment_type.lower(),
        object_id=segment_data.object_id,
        material=segment_data.material,
        height_m=segment_data.height_m,
        width_m=segment_data.width_m,
        volume_m3=segment_data.volume_m3,
        condition=segment_data.condition,
        restoration_year=segment_data.restoration_year,
        description_tr=segment_data.description_tr,
        description_en=segment_data.description_en
    )

    db.add(segment)
    db.commit()
    db.refresh(segment)
    return segment


@router.patch("/{segment_id}", response_model=SegmentResponse)
async def update_segment(
    segment_id: int,
    segment_data: SegmentUpdate,
    db: Session = Depends(get_db)
):
    """Update a segment"""
    segment = db.query(AssetSegment).filter(AssetSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    update_data = segment_data.model_dump(exclude_unset=True)

    # Validate segment type if provided
    if "segment_type" in update_data:
        if update_data["segment_type"].lower() not in SEGMENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid segment type. Valid types: {list(SEGMENT_TYPES.keys())}"
            )
        update_data["segment_type"] = update_data["segment_type"].lower()

    for field, value in update_data.items():
        setattr(segment, field, value)

    db.commit()
    db.refresh(segment)
    return segment


@router.delete("/{segment_id}", status_code=204)
async def delete_segment(segment_id: int, db: Session = Depends(get_db)):
    """Delete a segment"""
    segment = db.query(AssetSegment).filter(AssetSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    db.delete(segment)
    db.commit()
    return None


# ==================================================
# Statistics
# ==================================================

@router.get("/stats/summary", response_model=SegmentStatistics)
async def get_segment_statistics(db: Session = Depends(get_db)):
    """Get statistics about segments"""
    total = db.query(AssetSegment).count()

    by_type = db.query(
        AssetSegment.segment_type,
        func.count(AssetSegment.id).label("count")
    ).group_by(AssetSegment.segment_type).all()

    by_condition = db.query(
        AssetSegment.condition,
        func.count(AssetSegment.id).label("count")
    ).group_by(AssetSegment.condition).all()

    return SegmentStatistics(
        total_segments=total,
        by_type=[
            SegmentTypeCount(segment_type=t[0], count=t[1])
            for t in by_type if t[0]
        ],
        by_condition=[
            {"condition": c[0], "count": c[1]}
            for c in by_condition if c[0]
        ]
    )


@router.get("/stats/by-asset/{asset_id}")
async def get_asset_segment_stats(asset_id: int, db: Session = Depends(get_db)):
    """Get segment statistics for a specific asset"""
    asset = db.query(HeritageAsset).filter(HeritageAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    segments = db.query(AssetSegment).filter(AssetSegment.asset_id == asset_id).all()

    by_type = {}
    by_condition = {}
    total_height = 0
    total_volume = 0

    for seg in segments:
        # Count by type
        if seg.segment_type:
            by_type[seg.segment_type] = by_type.get(seg.segment_type, 0) + 1

        # Count by condition
        if seg.condition:
            by_condition[seg.condition] = by_condition.get(seg.condition, 0) + 1

        # Sum measurements
        if seg.height_m:
            total_height += seg.height_m
        if seg.volume_m3:
            total_volume += seg.volume_m3

    return {
        "asset_id": asset_id,
        "asset_name_tr": asset.name_tr,
        "total_segments": len(segments),
        "by_type": [{"type": k, "count": v} for k, v in by_type.items()],
        "by_condition": [{"condition": k, "count": v} for k, v in by_condition.items()],
        "total_height_m": round(total_height, 2),
        "total_volume_m3": round(total_volume, 2)
    }
