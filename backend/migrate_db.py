"""
Veritabani Migration Scripti
Eski tablolari silip yeni yapiyi olusturur
"""

from sqlalchemy import create_engine, text
from database import Base, DATABASE_URL, Yapi, YapiMetadata, Aciklama, Katman
from datetime import datetime

def migrate():
    """Veritabanini yeni yapiya guncelle"""
    
    engine = create_engine(DATABASE_URL)
    
    print("=" * 50)
    print("Veritabani Migration Basliyor...")
    print("=" * 50)
    
    with engine.connect() as conn:
        # PostGIS extension aktifleştir
        print("\n[1/4] PostGIS extension kontrol ediliyor...")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.commit()
        print("[OK] PostGIS aktif")
        
        # Eski tablolari sil
        print("\n[2/4] Eski tablolar siliniyor...")
        old_tables = [
            "annotations",
            "measurements", 
            "building_metadata",
            "layers",
            "buildings"
        ]
        
        for table in old_tables:
            try:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
                print(f"  [OK] {table} silindi")
            except Exception as e:
                print(f"  [-] {table} bulunamadi veya silinemedi")
        
        conn.commit()
        
        # Yeni tablolari da sil (temiz baslangic icin)
        print("\n[3/4] Yeni tablo yapisi hazirlaniyor...")
        new_tables = [
            "aciklamalar",
            "yapi_metadata",
            "katmanlar",
            "yapi"
        ]
        
        for table in new_tables:
            try:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
            except:
                pass
        
        conn.commit()
    
    # Yeni tablolari olustur
    print("\n[4/4] Yeni tablolar olusturuluyor...")
    Base.metadata.create_all(bind=engine)
    print("[OK] Tablolar olusturuldu:")
    print("  - yapi")
    print("  - yapi_metadata")
    print("  - aciklamalar")
    print("  - katmanlar")
    
    # Ornek veri ekle
    print("\n" + "=" * 50)
    print("Ornek veri ekleniyor...")
    print("=" * 50)
    
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Molla Husrev Camii
        yapi = Yapi(
            ad="Molla Husrev Camii",
            ad_en="Molla Husrev Mosque",
            tur="Cami",
            donem="Osmanli",
            mimar="Bilinmiyor",
            yapim_yili="1460",
            konum="Vefa, Fatih",
            ilce="Fatih",
            aciklama="Fatih doneminde Seyhulislam Molla Husrev tarafindan yaptirilmis tarihi cami."
        )
        session.add(yapi)
        session.commit()
        session.refresh(yapi)
        print(f"[OK] Yapi eklendi: {yapi.ad} (ID: {yapi.id})")
        
        # Metadata
        metadata = YapiMetadata(
            yapi_id=yapi.id,
            tileset_url="cesium_ion:4270999",
            nokta_bulutu_url="/data/pointcloud/molla-husrev/metadata.json",
            lod_seviyesi=3,
            nokta_sayisi=15000000,
            dosya_boyutu_mb=1920.0
        )
        session.add(metadata)
        print("[OK] Metadata eklendi")
        
        # Katmanlar
        katmanlar = [
            Katman(ad="Molla Husrev - Dis Cephe", tur="3dtiles", url="cesium_ion:4270999", gorunur=True, saydamlik=1.0, sira=1),
            Katman(ad="Molla Husrev - Ic Mekan", tur="3dtiles", url="/data/pointcloud/molla-husrev/metadata.json", gorunur=True, saydamlik=1.0, sira=2),
            Katman(ad="Cevre LoD0 Modeli", tur="3dtiles", url="/data/3dtiles/context/tileset.json", gorunur=True, saydamlik=0.8, sira=3),
        ]
        for k in katmanlar:
            session.add(k)
        print(f"[OK] {len(katmanlar)} katman eklendi")
        
        # Ornek aciklama
        aciklama = Aciklama(
            yapi_id=yapi.id,
            baslik="Ana Giris",
            aciklama="Caminin ana giris kapisi",
            x=28.9487,
            y=41.0169,
            z=10.0,
            olusturan="Sistem"
        )
        session.add(aciklama)
        print("[OK] Ornek aciklama eklendi")
        
        session.commit()
        
    except Exception as e:
        print(f"[HATA] {e}")
        session.rollback()
    finally:
        session.close()
    
    print("\n" + "=" * 50)
    print("[OK] Migration tamamlandi!")
    print("=" * 50)
    
    # Tablo kontrolu
    print("\nTablo durumu:")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        for row in result:
            print(f"  - {row[0]}")


if __name__ == "__main__":
    migrate()

