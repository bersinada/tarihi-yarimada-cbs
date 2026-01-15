"""
Tarihi Yarimada CBS - Segment Pydantic Schemas
Request/Response models for Asset Segments (SAM3D)
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SegmentType(str, Enum):
    """Segment types for SAM3D integration"""
    DOME = "dome"              # Kubbe
    MINARET = "minaret"        # Minare
    PORTAL = "portal"          # Tac kapi/Giris
    WALL = "wall"              # Duvar
    WINDOW = "window"          # Pencere
    COURTYARD = "courtyard"    # Avlu
    FOUNTAIN = "fountain"      # Sadirvan
    COLUMN = "column"          # Sutun
    ARCH = "arch"              # Kemer
    ROOF = "roof"              # Cati
    OTHER = "other"            # Diger


class ConditionType(str, Enum):
    """Segment condition types"""
    ORIGINAL = "original"
    RESTORED = "restored"
    DAMAGED = "damaged"


# ==================================================
# Segment Schemas
# ==================================================

class SegmentBase(BaseModel):
    """Base segment schema"""
    segment_name: str = Field(..., min_length=1, max_length=100)
    segment_type: str = Field(..., max_length=50)
    object_id: Optional[str] = Field(None, max_length=50)
    material: Optional[str] = Field(None, max_length=100)
    height_m: Optional[float] = Field(None, ge=0)
    width_m: Optional[float] = Field(None, ge=0)
    volume_m3: Optional[float] = Field(None, ge=0)
    condition: Optional[str] = Field(None, max_length=50)
    restoration_year: Optional[int] = None
    description_tr: Optional[str] = None
    description_en: Optional[str] = None


class SegmentCreate(SegmentBase):
    """Schema for creating a segment"""
    asset_id: int


class SegmentUpdate(BaseModel):
    """Schema for updating a segment"""
    segment_name: Optional[str] = Field(None, min_length=1, max_length=100)
    segment_type: Optional[str] = Field(None, max_length=50)
    object_id: Optional[str] = Field(None, max_length=50)
    material: Optional[str] = Field(None, max_length=100)
    height_m: Optional[float] = Field(None, ge=0)
    width_m: Optional[float] = Field(None, ge=0)
    volume_m3: Optional[float] = Field(None, ge=0)
    condition: Optional[str] = Field(None, max_length=50)
    restoration_year: Optional[int] = None
    description_tr: Optional[str] = None
    description_en: Optional[str] = None


class SegmentResponse(SegmentBase):
    """Segment response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int
    created_at: Optional[datetime] = None


class SegmentWithAsset(SegmentResponse):
    """Segment response with asset info"""
    asset_name_tr: Optional[str] = None
    asset_identifier: Optional[str] = None


# ==================================================
# Segment Statistics Schemas
# ==================================================

class SegmentTypeCount(BaseModel):
    """Count of segments by type"""
    segment_type: str
    count: int


class SegmentStatistics(BaseModel):
    """Statistics about segments"""
    total_segments: int
    by_type: List[SegmentTypeCount]
    by_condition: List[dict]


# ==================================================
# Note Schemas (for user_notes)
# ==================================================

class NoteBase(BaseModel):
    """Base note schema"""
    note_text: str = Field(..., min_length=1)
    user_identifier: Optional[str] = Field(None, max_length=255)


class NoteCreate(NoteBase):
    """Schema for creating a note"""
    asset_id: int


class NoteResponse(NoteBase):
    """Note response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int
    created_at: Optional[datetime] = None
