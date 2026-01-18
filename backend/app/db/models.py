"""
Tarihi Yarimada CBS - Database Models
7 tables following Dublin Core + TUCBS + ISO 19115 standards

Tables:
1. heritage_assets - Main heritage asset table
2. asset_segments - SAM3D segmented 3D model parts
3. dataset_metadata - ISO 19115 Geographic Metadata
4. actors - Architects and patrons
5. asset_actors - Asset-Actor relationship (many-to-many)
6. media - Asset media/images
7. user_notes - User notes on assets
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, Date, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from .database import Base


# ==================================================
# Table 1: heritage_assets
# ==================================================

class HeritageAsset(Base):
    """
    Main heritage asset table
    Standards: Dublin Core + TUCBS Koruma Alanlari
    """
    __tablename__ = "heritage_assets"

    id = Column(Integer, primary_key=True)

    # === Dublin Core ===
    identifier = Column(String(20), unique=True, nullable=False)  # "HA-0001"
    name_tr = Column(String(255), nullable=False)                 # title
    name_en = Column(String(255))
    asset_type = Column(String(50), nullable=False)               # type: cami, hamam...
    description_tr = Column(Text)                                 # description
    description_en = Column(Text)

    # === Chronology ===
    construction_year = Column(Integer)
    construction_period = Column(String(100))                     # "1550-1557"
    historical_period = Column(String(50))                        # bizans, osmanli_klasik

    # === Spatial (EPSG:4326) ===
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    footprint = Column(Geometry('POLYGON', srid=4326))
    neighborhood = Column(String(100))
    address = Column(Text)

    # === TUCBS Koruma Alanlari ===
    inspire_id = Column(String(100))
    protection_status = Column(String(50))                        # '1. derece', 'UNESCO'
    registration_no = Column(String(50))
    registration_date = Column(Date)
    legal_foundation = Column(Text)

    # === 3D Model ===
    model_url = Column(String(500))                               # 3D Tiles or Splat URL
    model_type = Column(String(20))                               # 'SPLAT', 'MESH', '3DTILES'
    model_lod = Column(String(10))                                # 'LOD1', 'LOD2', 'LOD3'
    cesium_ion_asset_id = Column(Integer)                         # Cesium Ion Asset ID

    # === Status ===
    is_visitable = Column(Boolean, default=True)

    # === Metadata ===
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    data_source = Column(String(255))

    # === Relationships ===
    actors = relationship("AssetActor", back_populates="asset", cascade="all, delete-orphan")
    media = relationship("Media", back_populates="asset", cascade="all, delete-orphan")
    notes = relationship("UserNote", back_populates="asset", cascade="all, delete-orphan")
    segments = relationship("AssetSegment", back_populates="asset", cascade="all, delete-orphan")


# ==================================================
# Table 2: asset_segments (SAM3D Integration)
# ==================================================

class AssetSegment(Base):
    """
    SAM3D segmented 3D model parts
    Manages building elements like domes, minarets, portals separately
    """
    __tablename__ = "asset_segments"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("heritage_assets.id", ondelete="CASCADE"), nullable=False)

    # === Segment Definition ===
    segment_name = Column(String(100), nullable=False)            # "Ana Kubbe", "Kuzey Minare"
    segment_type = Column(String(50), nullable=False)             # 'dome', 'minaret', 'portal', etc.
    object_id = Column(String(50))                                # Segment ID in 3D model

    # === Technical Details ===
    material = Column(String(100))                                # "Tas", "Kursun kaplama"
    height_m = Column(Float)                                      # Height (meters)
    width_m = Column(Float)                                       # Width
    volume_m3 = Column(Float)                                     # Volume

    # === Condition ===
    condition = Column(String(50))                                # 'original', 'restored', 'damaged'
    restoration_year = Column(Integer)

    # === Description ===
    description_tr = Column(Text)
    description_en = Column(Text)

    # === Metadata ===
    created_at = Column(DateTime, default=func.now())

    # === Relationship ===
    asset = relationship("HeritageAsset", back_populates="segments")


# ==================================================
# Table 3: dataset_metadata (ISO 19115)
# ==================================================

class DatasetMetadata(Base):
    """
    ISO 19115 Geographic Metadata - Basic Profile
    Dataset-level metadata
    """
    __tablename__ = "dataset_metadata"

    id = Column(Integer, primary_key=True)

    # === Identification ===
    title = Column(String(255), nullable=False)
    abstract = Column(Text)
    purpose = Column(Text)
    language = Column(String(10), default='tr')

    # === Spatial Extent (Bounding Box) ===
    west_bound = Column(Float)
    east_bound = Column(Float)
    south_bound = Column(Float)
    north_bound = Column(Float)
    coordinate_system = Column(String(50), default='EPSG:4326')

    # === Temporal Extent ===
    temporal_begin = Column(Date)
    temporal_end = Column(Date)

    # === Data Quality ===
    lineage = Column(Text)                                        # Data source and production process
    spatial_resolution = Column(String(50))

    # === Reference System ===
    reference_system = Column(String(100), default='EPSG:4326 - WGS84')

    # === Distribution ===
    distribution_format = Column(String(50), default='GeoJSON')
    access_url = Column(String(500))

    # === Contact ===
    contact_name = Column(String(255))
    contact_email = Column(String(255))
    contact_organization = Column(String(255))

    # === Constraints ===
    use_constraints = Column(Text)
    license = Column(String(100))

    # === Metadata Info ===
    metadata_date = Column(DateTime, default=func.now())
    metadata_standard = Column(String(100), default='ISO 19115:2014')


# ==================================================
# Table 4: actors
# ==================================================

class Actor(Base):
    """Architects and patrons"""
    __tablename__ = "actors"

    id = Column(Integer, primary_key=True)
    identifier = Column(String(20), unique=True)                  # "AC-0001"
    name_tr = Column(String(255), nullable=False)
    name_en = Column(String(255))
    actor_type = Column(String(50), nullable=False)               # 'architect', 'patron'
    bio_tr = Column(Text)
    birth_year = Column(Integer)
    death_year = Column(Integer)

    assets = relationship("AssetActor", back_populates="actor")


# ==================================================
# Table 5: asset_actors
# ==================================================

class AssetActor(Base):
    """Asset-Actor relationship (many-to-many)"""
    __tablename__ = "asset_actors"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("heritage_assets.id", ondelete="CASCADE"), nullable=False)
    actor_id = Column(Integer, ForeignKey("actors.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)                     # 'architect', 'patron', 'restorer'

    asset = relationship("HeritageAsset", back_populates="actors")
    actor = relationship("Actor", back_populates="assets")

    __table_args__ = (
        UniqueConstraint('asset_id', 'actor_id', 'role', name='uq_asset_actor_role'),
    )


# ==================================================
# Table 6: media
# ==================================================

class Media(Base):
    """Asset images and media"""
    __tablename__ = "media"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("heritage_assets.id", ondelete="CASCADE"), nullable=False)
    media_type = Column(String(20), default="image")              # 'image', 'historical', 'video', '360'
    url = Column(String(500), nullable=False)
    caption = Column(Text)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    asset = relationship("HeritageAsset", back_populates="media")


# ==================================================
# Table 7: user_notes
# ==================================================

class UserNote(Base):
    """User notes on assets"""
    __tablename__ = "user_notes"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("heritage_assets.id", ondelete="CASCADE"), nullable=False)
    user_identifier = Column(String(255))
    note_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())

    asset = relationship("HeritageAsset", back_populates="notes")


# ==================================================
# Indexes
# ==================================================

# Spatial indexes (GIST)
Index('idx_assets_location', HeritageAsset.location, postgresql_using='gist')
Index('idx_assets_footprint', HeritageAsset.footprint, postgresql_using='gist')

# B-tree indexes
Index('idx_assets_type', HeritageAsset.asset_type)
Index('idx_assets_period', HeritageAsset.historical_period)
Index('idx_assets_identifier', HeritageAsset.identifier)
Index('idx_segments_asset', AssetSegment.asset_id)
Index('idx_segments_type', AssetSegment.segment_type)
