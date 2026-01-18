"""
Tarihi Yarimada CBS - Database Seed Script
Populates the database with initial sample data

Data includes:
- 1 Dataset Metadata (ISO 19115)
- 3 Actors (architects/patrons)
- 5 Heritage Assets
- 6+ Asset Segments (SAM3D)
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# .env dosyasını yükle
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Backend klasöründeki .env'i dene
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()  # Mevcut dizinde .env ara

# Database URL'i al - önce local_database_url (küçük harf), sonra LOCAL_DATABASE_URL, sonra DATABASE_URL
database_url = (
    os.getenv("local_database_url") or 
    os.getenv("LOCAL_DATABASE_URL") or 
    os.getenv("DATABASE_URL") or
    os.getenv("AZURE_DATABASE_URL")
)

# Eğer local_database_url bulunduysa, DATABASE_URL'i de set et
# (database.py modülü DATABASE_URL bekliyor)
if database_url and not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = database_url

from sqlalchemy import text
from app.db.database import SessionLocal, engine, Base, init_db
from app.db.models import (
    HeritageAsset, AssetSegment, DatasetMetadata,
    Actor, AssetActor, Media, UserNote
)


def seed_database():
    """Seed the database with sample data"""
    print("Starting database seed process...")

    # Initialize database (create tables)
    init_db()

    db = SessionLocal()

    try:
        # Check if data already exists
        existing_assets = db.query(HeritageAsset).count()
        if existing_assets > 0:
            print(f"Database already contains {existing_assets} assets. Skipping seed.")
            return

        print("Seeding data...")

        # ==================================================
        # 1. Dataset Metadata (ISO 19115)
        # ==================================================
        print("  Adding dataset metadata...")
        metadata = DatasetMetadata(
            title="Istanbul Tarihi Yarimada Kulturel Miras Envanteri",
            abstract="Istanbul Tarihi Yarimada'daki tescilli kulturel miras yapilarinin mekansal veritabani. SAM3D segmentasyon ve Gaussian Splatting 3D model destegi.",
            purpose="Kulturel miras yapilarinin 3D gorsellestirmesi, segmentasyon analizi ve CBS tabanli bilgi sistemi",
            language="tr",
            west_bound=28.916,
            east_bound=28.990,
            south_bound=40.996,
            north_bound=41.030,
            coordinate_system="EPSG:4326",
            lineage="Veriler Kultur ve Turizm Bakanligi, IBB Acik Veri Portali ve saha calismalarindan derlenmistir. 3D modeller SAM3D ve Gaussian Splatting teknikleriyle uretilmistir.",
            spatial_resolution="Bina ve yapi elemani duzeyi",
            distribution_format="GeoJSON, 3D Tiles, Gaussian Splat",
            license="CC BY-NC 4.0",
            contact_organization="Tarihi Yarimada CBS Projesi",
            metadata_standard="ISO 19115:2014"
        )
        db.add(metadata)

        # ==================================================
        # 2. Actors (Architects & Patrons)
        # ==================================================
        print("  Adding actors...")

        # Mimar Sinan
        sinan = Actor(
            identifier="AC-0001",
            name_tr="Mimar Sinan",
            name_en="Sinan the Architect",
            actor_type="architect",
            bio_tr="Osmanli Imparatorlugu'nun en buyuk mimari. 400'den fazla yapi tasarlamistir.",
            birth_year=1489,
            death_year=1588
        )
        db.add(sinan)

        # Kanuni Sultan Suleyman
        kanuni = Actor(
            identifier="AC-0002",
            name_tr="Kanuni Sultan Suleyman",
            name_en="Suleiman the Magnificent",
            actor_type="patron",
            bio_tr="Osmanli Imparatorlugu'nun 10. padisahi. Pek cok onemli yapinin banisidir.",
            birth_year=1494,
            death_year=1566
        )
        db.add(kanuni)

        # I. Justinianus
        justinian = Actor(
            identifier="AC-0003",
            name_tr="I. Justinianus",
            name_en="Justinian I",
            actor_type="patron",
            bio_tr="Bizans Imparatoru. Ayasofya'nin insasini baslatan hukumdardir.",
            birth_year=482,
            death_year=565
        )
        db.add(justinian)

        db.flush()  # Get IDs for actors

        # ==================================================
        # 3. Heritage Assets (5 buildings)
        # ==================================================
        print("  Adding heritage assets...")

        # Suleymaniye Camii
        suleymaniye = HeritageAsset(
            identifier="HA-0001",
            name_tr="Suleymaniye Camii",
            name_en="Suleymaniye Mosque",
            asset_type="cami",
            construction_year=1557,
            construction_period="1550-1557",
            historical_period="osmanli_klasik",
            location="SRID=4326;POINT(28.9639 41.0162)",
            neighborhood="Suleymaniye",
            description_tr="Mimar Sinan'in 'kalfalik eserim' dedigi cami. Osmanli mimarisinin en onemli yapilarindan biri.",
            description_en="The mosque that Sinan called his 'journeyman work'. One of the most important structures of Ottoman architecture.",
            protection_status="1. derece",
            model_type="3DTILES",
            model_lod="LOD3",
            cesium_ion_asset_id=4357341,
            is_visitable=True,
            data_source="Kultur ve Turizm Bakanligi"
        )
        db.add(suleymaniye)

        # Ayasofya
        ayasofya = HeritageAsset(
            identifier="HA-0002",
            name_tr="Ayasofya",
            name_en="Hagia Sophia",
            asset_type="cami",
            construction_year=537,
            construction_period="532-537",
            historical_period="bizans",
            location="SRID=4326;POINT(28.9802 41.0086)",
            neighborhood="Sultanahmet",
            description_tr="Bizans Imparatorlugu'nun en buyuk katedrali olarak insa edilmis, dunya mimarlik tarihinin en onemli yapilarindan.",
            description_en="Built as the largest cathedral of the Byzantine Empire, one of the most important structures in world architectural history.",
            protection_status="UNESCO",
            model_type="3DTILES",
            model_lod="LOD3",
            cesium_ion_asset_id=4357357,
            is_visitable=True,
            data_source="UNESCO Dunya Mirasi"
        )
        db.add(ayasofya)

        # Sultanahmet Camii
        sultanahmet = HeritageAsset(
            identifier="HA-0003",
            name_tr="Sultanahmet Camii",
            name_en="Sultan Ahmed Mosque (Blue Mosque)",
            asset_type="cami",
            construction_year=1616,
            construction_period="1609-1616",
            historical_period="osmanli_klasik",
            location="SRID=4326;POINT(28.9768 41.0054)",
            neighborhood="Sultanahmet",
            description_tr="6 minaresiyle unlu, 'Mavi Cami' olarak da bilinen Osmanli donemi camisi.",
            description_en="Famous for its 6 minarets, also known as the 'Blue Mosque', an Ottoman-era mosque.",
            protection_status="1. derece",
            model_type="3DTILES",
            model_lod="LOD3",
            cesium_ion_asset_id=4357335,
            is_visitable=True,
            data_source="Kultur ve Turizm Bakanligi"
        )
        db.add(sultanahmet)

        # Kariye Camii
        kariye = HeritageAsset(
            identifier="HA-0004",
            name_tr="Kariye Camii",
            name_en="Chora Church (Kariye Mosque)",
            asset_type="cami",
            construction_year=534,
            construction_period="534-1511",
            historical_period="bizans",
            location="SRID=4326;POINT(28.9390 41.0312)",
            neighborhood="Edirnekapi",
            description_tr="Bizans donemi kilisesi. Dunyaca unlu mozaik ve fresklerine sahip onemli bir kulturel miras yapisi.",
            description_en="Byzantine-era church. An important cultural heritage structure with world-famous mosaics and frescoes.",
            protection_status="UNESCO",
            model_type="3DTILES",
            model_lod="LOD3",
            cesium_ion_asset_id=4357343,
            is_visitable=True,
            data_source="UNESCO Dunya Mirasi"
        )
        db.add(kariye)

        # Molla Husrev Camii
        molla_husrev = HeritageAsset(
            identifier="HA-0005",
            name_tr="Molla Husrev Camii",
            name_en="Molla Husrev Mosque",
            asset_type="cami",
            construction_year=1455,
            construction_period="1455",
            historical_period="osmanli_klasik",
            location="SRID=4326;POINT(28.9593 41.0146)",
            neighborhood="Fatih",
            description_tr="Osmanli Devleti'nin ilk seyhulislamlarindan Molla Husrev tarafindan yaptirilan cami.",
            description_en="Mosque built by Molla Husrev, one of the first Shaykh al-Islams of the Ottoman Empire.",
            protection_status="1. derece",
            model_type="3DTILES",
            model_lod="LOD3",
            cesium_ion_asset_id=4357344,
            is_visitable=True,
            data_source="Kultur ve Turizm Bakanligi"
        )
        db.add(molla_husrev)

        db.flush()  # Get IDs for assets

        # ==================================================
        # 4. Asset-Actor Relationships
        # ==================================================
        print("  Adding asset-actor relationships...")

        # Suleymaniye - Sinan (architect)
        db.add(AssetActor(asset_id=suleymaniye.id, actor_id=sinan.id, role="architect"))
        # Suleymaniye - Kanuni (patron)
        db.add(AssetActor(asset_id=suleymaniye.id, actor_id=kanuni.id, role="patron"))
        # Ayasofya - Justinian (patron)
        db.add(AssetActor(asset_id=ayasofya.id, actor_id=justinian.id, role="patron"))
        # Kariye - Justinian (patron)
        db.add(AssetActor(asset_id=kariye.id, actor_id=justinian.id, role="patron"))

        # ==================================================
        # 5. Asset Segments (SAM3D) - Basit ornekler
        # ==================================================
        print("  Adding asset segments...")

        # Ayasofya ana kubbe
        db.add(AssetSegment(
            asset_id=ayasofya.id,
            segment_name="Ana Kubbe",
            segment_type="dome",
            object_id="dome_main_001",
            material="Tugla",
            height_m=55.6,
            width_m=31.87,
            condition="restored",
            description_tr="Yapildigi donemde dunyanin en buyuk kubbesi."
        ))

        # Sultanahmet ana kubbe
        db.add(AssetSegment(
            asset_id=sultanahmet.id,
            segment_name="Ana Kubbe",
            segment_type="dome",
            object_id="dome_main_001",
            material="Kursun kaplama",
            height_m=43.0,
            width_m=23.5,
            condition="restored",
            restoration_year=2017,
            description_tr="Alti yarım kubbe ile desteklenen ana kubbe."
        ))

        db.commit()
        print("\nDatabase seed completed successfully!")

        # Print summary
        print("\nSummary:")
        print(f"  - Dataset Metadata: 1")
        print(f"  - Actors: {db.query(Actor).count()}")
        print(f"  - Heritage Assets: {db.query(HeritageAsset).count()}")
        print(f"  - Asset Segments: {db.query(AssetSegment).count()}")
        print(f"  - Asset-Actor Relations: {db.query(AssetActor).count()}")

    except Exception as e:
        db.rollback()
        print(f"Error during seed: {e}")
        raise
    finally:
        db.close()


def clear_database():
    """Clear all data from the database (use with caution!)"""
    db = SessionLocal()
    try:
        print("Clearing database...")
        db.execute(text("DELETE FROM asset_actors"))
        db.execute(text("DELETE FROM asset_segments"))
        db.execute(text("DELETE FROM media"))
        db.execute(text("DELETE FROM user_notes"))
        db.execute(text("DELETE FROM heritage_assets"))
        db.execute(text("DELETE FROM actors"))
        db.execute(text("DELETE FROM dataset_metadata"))
        db.commit()
        print("Database cleared!")
    except Exception as e:
        db.rollback()
        print(f"Error clearing database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Database seed script")
    parser.add_argument("--clear", action="store_true", help="Clear database before seeding")
    args = parser.parse_args()

    if args.clear:
        clear_database()

    seed_database()
