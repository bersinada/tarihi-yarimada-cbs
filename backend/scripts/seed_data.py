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
load_dotenv()

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
            model_type="SPLAT",
            model_lod="LOD3",
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
            is_visitable=True,
            data_source="UNESCO Dunya Mirasi"
        )
        db.add(ayasofya)

        # Kucuk Ayasofya
        kucuk_ayasofya = HeritageAsset(
            identifier="HA-0003",
            name_tr="Kucuk Ayasofya Camii",
            name_en="Little Hagia Sophia (Church of Saints Sergius and Bacchus)",
            asset_type="cami",
            construction_year=536,
            construction_period="527-536",
            historical_period="bizans",
            location="SRID=4326;POINT(28.9719 41.0042)",
            neighborhood="Sultanahmet",
            description_tr="Bizans Imparatoru I. Justinianus tarafindan yaptirilan kilise. Ayasofya'nin kucuk prototipi olarak kabul edilir.",
            description_en="Church built by Byzantine Emperor Justinian I. Considered a small prototype of Hagia Sophia.",
            protection_status="1. derece",
            model_type="SPLAT",
            model_lod="LOD2",
            is_visitable=True,
            data_source="Kultur ve Turizm Bakanligi"
        )
        db.add(kucuk_ayasofya)

        # Sultanahmet Camii
        sultanahmet = HeritageAsset(
            identifier="HA-0004",
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
            model_type="SPLAT",
            model_lod="LOD3",
            is_visitable=True,
            data_source="Kultur ve Turizm Bakanligi"
        )
        db.add(sultanahmet)

        # Topkapi Sarayi
        topkapi = HeritageAsset(
            identifier="HA-0005",
            name_tr="Topkapi Sarayi",
            name_en="Topkapi Palace",
            asset_type="saray",
            construction_year=1478,
            construction_period="1460-1478",
            historical_period="osmanli_klasik",
            location="SRID=4326;POINT(28.9833 41.0115)",
            neighborhood="Sultanahmet",
            description_tr="Osmanli padisahlarinin yaklasik 400 yil boyunca yasadigi ve devleti yonettigi saray kompleksi.",
            description_en="The palace complex where Ottoman sultans lived and ruled the empire for approximately 400 years.",
            protection_status="UNESCO",
            model_type="3DTILES",
            model_lod="LOD2",
            is_visitable=True,
            data_source="UNESCO Dunya Mirasi"
        )
        db.add(topkapi)

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
        # Kucuk Ayasofya - Justinian (patron)
        db.add(AssetActor(asset_id=kucuk_ayasofya.id, actor_id=justinian.id, role="patron"))

        # ==================================================
        # 5. Asset Segments (SAM3D)
        # ==================================================
        print("  Adding asset segments...")

        # Suleymaniye segments
        db.add(AssetSegment(
            asset_id=suleymaniye.id,
            segment_name="Ana Kubbe",
            segment_type="dome",
            object_id="dome_main_001",
            material="Tas, kursun kaplama",
            height_m=53.0,
            width_m=26.5,
            condition="restored",
            restoration_year=2011,
            description_tr="Sinan'in en buyuk kubbelerinden biri. Capi 26.5 metre."
        ))

        db.add(AssetSegment(
            asset_id=suleymaniye.id,
            segment_name="Kuzeybati Minare",
            segment_type="minaret",
            object_id="minaret_nw_001",
            material="Kesme tas",
            height_m=76.0,
            condition="original",
            description_tr="Dort minareden biri. Uc serefeli."
        ))

        db.add(AssetSegment(
            asset_id=suleymaniye.id,
            segment_name="Avlu",
            segment_type="courtyard",
            object_id="courtyard_001",
            material="Mermer doseme",
            condition="restored",
            description_tr="Revakli avlu, ortasinda sadirvan bulunur."
        ))

        # Ayasofya segments
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

        # Kucuk Ayasofya segments
        db.add(AssetSegment(
            asset_id=kucuk_ayasofya.id,
            segment_name="Ana Kubbe",
            segment_type="dome",
            object_id="dome_main_001",
            material="Tugla",
            height_m=20.0,
            width_m=16.0,
            condition="restored",
            description_tr="Sekizgen kasnak uzerine oturan kubbe. Ayasofya'nin prototiplerinden."
        ))

        db.add(AssetSegment(
            asset_id=kucuk_ayasofya.id,
            segment_name="Revakli Avlu",
            segment_type="courtyard",
            object_id="courtyard_001",
            material="Mermer sutunlar",
            condition="restored",
            description_tr="Osmanli doneminde eklenen revakli avlu."
        ))

        # Sultanahmet segments
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

        db.add(AssetSegment(
            asset_id=sultanahmet.id,
            segment_name="Bati Minare 1",
            segment_type="minaret",
            object_id="minaret_w1_001",
            material="Kesme tas",
            height_m=64.0,
            condition="original",
            description_tr="Alti minareden biri. Uc serefeli."
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
