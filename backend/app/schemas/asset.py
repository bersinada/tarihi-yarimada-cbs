"""
Tarihi Yarimada CBS - Asset Pydantic Schemas
Request/Response models for Heritage Assets
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Any
from datetime import datetime, date
from enum import Enum


class AssetType(str, Enum):
    """Heritage asset types"""
    CAMI = "cami"
    KILISE = "kilise"
    HAMAM = "hamam"
    SARAY = "saray"
    KALE = "kale"
    MEDRESE = "medrese"
    HAN = "han"
    CESME = "cesme"
    TURBE = "turbe"
    SINAGOG = "sinagog"
    DIGER = "diger"


class HistoricalPeriod(str, Enum):
    """Historical periods"""
    BIZANS = "bizans"
    OSMANLI_ERKEN = "osmanli_erken"
    OSMANLI_KLASIK = "osmanli_klasik"
    OSMANLI_GEC = "osmanli_gec"
    CUMHURIYET = "cumhuriyet"


class ModelType(str, Enum):
    """3D model types"""
    SPLAT = "SPLAT"
    MESH = "MESH"
    TILES_3D = "3DTILES"


# ==================================================
# Asset Schemas
# ==================================================

class AssetBase(BaseModel):
    """Base asset schema"""
    name_tr: str = Field(..., min_length=1, max_length=255)
    name_en: Optional[str] = Field(None, max_length=255)
    asset_type: str = Field(..., max_length=50)
    description_tr: Optional[str] = None
    description_en: Optional[str] = None
    construction_year: Optional[int] = None
    construction_period: Optional[str] = Field(None, max_length=100)
    historical_period: Optional[str] = Field(None, max_length=50)
    neighborhood: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    protection_status: Optional[str] = Field(None, max_length=50)
    registration_no: Optional[str] = Field(None, max_length=50)
    model_url: Optional[str] = Field(None, max_length=500)
    model_type: Optional[str] = Field(None, max_length=20)
    model_lod: Optional[str] = Field(None, max_length=10)
    cesium_ion_asset_id: Optional[int] = None
    is_visitable: bool = True
    data_source: Optional[str] = Field(None, max_length=255)


class AssetCreate(AssetBase):
    """Schema for creating a new asset"""
    identifier: str = Field(..., max_length=20)
    longitude: float = Field(..., ge=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)
    registration_date: Optional[date] = None
    legal_foundation: Optional[str] = None


class AssetUpdate(BaseModel):
    """Schema for updating an asset"""
    name_tr: Optional[str] = Field(None, min_length=1, max_length=255)
    name_en: Optional[str] = Field(None, max_length=255)
    asset_type: Optional[str] = Field(None, max_length=50)
    description_tr: Optional[str] = None
    description_en: Optional[str] = None
    construction_year: Optional[int] = None
    construction_period: Optional[str] = Field(None, max_length=100)
    historical_period: Optional[str] = Field(None, max_length=50)
    neighborhood: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    protection_status: Optional[str] = Field(None, max_length=50)
    model_url: Optional[str] = Field(None, max_length=500)
    model_type: Optional[str] = Field(None, max_length=20)
    is_visitable: Optional[bool] = None


class AssetResponse(BaseModel):
    """Asset response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    identifier: str
    name_tr: str
    name_en: Optional[str] = None
    asset_type: str
    description_tr: Optional[str] = None
    description_en: Optional[str] = None
    construction_year: Optional[int] = None
    construction_period: Optional[str] = None
    historical_period: Optional[str] = None
    neighborhood: Optional[str] = None
    address: Optional[str] = None
    protection_status: Optional[str] = None
    registration_no: Optional[str] = None
    model_url: Optional[str] = None
    model_type: Optional[str] = None
    model_lod: Optional[str] = None
    cesium_ion_asset_id: Optional[int] = None
    is_visitable: bool = True
    data_source: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    segment_count: Optional[int] = None


class AssetWithLocation(AssetResponse):
    """Asset response with location coordinates"""
    longitude: Optional[float] = None
    latitude: Optional[float] = None


# ==================================================
# GeoJSON Schemas
# ==================================================

class GeoJSONGeometry(BaseModel):
    """GeoJSON geometry"""
    type: str = "Point"
    coordinates: List[float]


class AssetGeoJSONProperties(BaseModel):
    """GeoJSON feature properties for asset"""
    identifier: str
    name_tr: str
    asset_type: str
    historical_period: Optional[str] = None
    construction_year: Optional[int] = None
    protection_status: Optional[str] = None
    model_type: Optional[str] = None
    segment_count: Optional[int] = None


class AssetGeoJSONFeature(BaseModel):
    """GeoJSON Feature for asset"""
    type: str = "Feature"
    id: str
    geometry: GeoJSONGeometry
    properties: AssetGeoJSONProperties


class CRS(BaseModel):
    """Coordinate Reference System"""
    type: str = "name"
    properties: dict = {"name": "EPSG:4326"}


class AssetFeatureCollection(BaseModel):
    """GeoJSON FeatureCollection"""
    type: str = "FeatureCollection"
    crs: CRS = CRS()
    features: List[AssetGeoJSONFeature]


# ==================================================
# Actor Schemas
# ==================================================

class ActorBase(BaseModel):
    """Base actor schema"""
    identifier: Optional[str] = Field(None, max_length=20)
    name_tr: str = Field(..., min_length=1, max_length=255)
    name_en: Optional[str] = Field(None, max_length=255)
    actor_type: str = Field(..., max_length=50)  # 'architect', 'patron'
    bio_tr: Optional[str] = None
    birth_year: Optional[int] = None
    death_year: Optional[int] = None


class ActorCreate(ActorBase):
    """Schema for creating an actor"""
    pass


class ActorResponse(ActorBase):
    """Actor response schema"""
    model_config = ConfigDict(from_attributes=True)
    id: int


# ==================================================
# Media Schemas
# ==================================================

class MediaBase(BaseModel):
    """Base media schema"""
    media_type: str = Field(default="image", max_length=20)
    url: str = Field(..., max_length=500)
    caption: Optional[str] = None
    is_primary: bool = False


class MediaCreate(MediaBase):
    """Schema for creating media"""
    asset_id: int


class MediaResponse(MediaBase):
    """Media response schema"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    asset_id: int
    created_at: Optional[datetime] = None


# ==================================================
# Dataset Metadata Schema
# ==================================================

class DatasetMetadataResponse(BaseModel):
    """Dataset metadata response (ISO 19115)"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    abstract: Optional[str] = None
    purpose: Optional[str] = None
    language: str = "tr"
    west_bound: Optional[float] = None
    east_bound: Optional[float] = None
    south_bound: Optional[float] = None
    north_bound: Optional[float] = None
    coordinate_system: str = "EPSG:4326"
    lineage: Optional[str] = None
    spatial_resolution: Optional[str] = None
    distribution_format: str = "GeoJSON"
    license: Optional[str] = None
    contact_organization: Optional[str] = None
    metadata_date: Optional[datetime] = None
    metadata_standard: str = "ISO 19115:2014"
