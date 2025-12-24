"""
Veritabani Schema Migration Scripti
Mevcut tablolari INSPIRE/TUCBS uyumlu hale getirir
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
from backend.database import DATABASE_URL


def run_migration():
    """Mevcut tabloları yeni şemaya güncelle"""
    
    engine = create_engine(DATABASE_URL)
    
    print("=" * 60)
    print("INSPIRE/TUCBS Schema Migration Basliyor...")
    print("=" * 60)
    
    with engine.connect() as conn:
        
        # 1. PostGIS extension
        print("\n[1/6] PostGIS extension kontrol ediliyor...")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.commit()
        print("  [OK] PostGIS aktif")
        
        # 2. YAPI tablosuna yeni sutunlar ekle
        print("\n[2/6] YAPI tablosuna yeni sutunlar ekleniyor...")
        
        yapi_columns = [
            ("bina_adi", "VARCHAR(255)"),
            ("yapi_turu", "VARCHAR(50) DEFAULT 'dini'"),
            ("yapi_durumu", "VARCHAR(50) DEFAULT 'kullanilabilir'"),
            ("insaat_tarihi", "VARCHAR(50)"),
            ("tescil_no", "VARCHAR(50)"),
            ("tescil_tarihi", "DATE"),
            ("koruma_grubu", "VARCHAR(20)"),
            ("bina_yuksekligi", "NUMERIC(6,2)"),
            ("kat_sayisi", "INTEGER"),
            ("bodrum_kat_sayisi", "INTEGER DEFAULT 0"),
            ("yapi_alani", "NUMERIC(12,2)"),
            ("toplam_insaat_alani", "NUMERIC(12,2)"),
            ("cephe_uzunlugu", "NUMERIC(8,2)"),
            ("building_nature", "VARCHAR(50) DEFAULT 'mosque'"),
            ("lod_seviyesi", "VARCHAR(10) DEFAULT 'LoD3'"),
            ("mulkiyet_durumu", "VARCHAR(20) DEFAULT 'vakif'"),
            ("malik_adi", "VARCHAR(255)"),
            ("ada_no", "VARCHAR(20)"),
            ("parsel_no", "VARCHAR(20)"),
            ("mahalle", "VARCHAR(100)"),
            ("sokak", "VARCHAR(255)"),
            ("kapi_no", "VARCHAR(20)"),
            ("posta_kodu", "VARCHAR(10)"),
            ("land_cover_code", "VARCHAR(10)"),
            ("land_cover_desc", "VARCHAR(255)"),
            ("building_name_en", "VARCHAR(255)"),
            ("description_en", "TEXT"),
            ("inspire_namespace", "VARCHAR(100) DEFAULT 'TR.TUCBS.BINA'"),
            ("inspire_local_id", "UUID DEFAULT gen_random_uuid()"),
            ("inspire_version_id", "VARCHAR(50)"),
            ("geom", "geometry(POINTZ, 4326)"),
            ("lod_0_footprint", "geometry(POLYGON, 4326)"),
            ("lod_0_roofedge", "geometry(POLYGON, 4326)")
        ]
        
        for col_name, col_type in yapi_columns:
            try:
                conn.execute(text(f"ALTER TABLE yapi ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                print(f"    [OK] {col_name}")
            except Exception as e:
                print(f"    [-] {col_name}: {str(e)[:50]}")
        
        conn.commit()
        
        # 3. Mevcut verileri yeni sutunlara tasi
        print("\n[3/6] Mevcut veriler yeni sutunlara tasiniyor...")
        try:
            conn.execute(text("""
                UPDATE yapi SET 
                    bina_adi = ad,
                    insaat_tarihi = yapim_yili
                WHERE bina_adi IS NULL AND ad IS NOT NULL
            """))
            conn.commit()
            print("  [OK] ad -> bina_adi, yapim_yili -> insaat_tarihi")
        except Exception as e:
            print(f"  [-] Veri tasima hatasi: {e}")
        
        # 4. YAPI_METADATA tablosuna ic mekan sutunlari ekle
        print("\n[4/6] YAPI_METADATA tablosuna yeni sutunlar ekleniyor...")
        
        metadata_columns = [
            ("ic_mekan_tileset_url", "VARCHAR(500)"),
            ("ic_mekan_ion_asset_id", "INTEGER"),
            ("merkez_nokta", "geometry(POINTZ, 4326)"),
            ("giris_noktasi", "geometry(POINTZ, 4326)")
        ]
        
        for col_name, col_type in metadata_columns:
            try:
                conn.execute(text(f"ALTER TABLE yapi_metadata ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                print(f"    [OK] {col_name}")
            except Exception as e:
                print(f"    [-] {col_name}: {str(e)[:50]}")
        
        conn.commit()
        
        # 5. Yeni tablolari olustur (varsa atla)
        print("\n[5/6] Yeni tablolar olusturuluyor...")
        
        # ic_mekan_bolge tablosu
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ic_mekan_bolge (
                    id SERIAL PRIMARY KEY,
                    yapi_id INTEGER REFERENCES yapi(id),
                    bolge_adi VARCHAR(255) NOT NULL,
                    bolge_adi_en VARCHAR(255),
                    bolge_turu VARCHAR(50),
                    aciklama TEXT,
                    geom geometry(POINTZ, 4326),
                    kamera_pozisyon geometry(POINTZ, 4326),
                    kamera_hedef geometry(POINTZ, 4326),
                    kamera_heading NUMERIC(6,2) DEFAULT 0,
                    kamera_pitch NUMERIC(6,2) DEFAULT -30,
                    kamera_roll NUMERIC(6,2) DEFAULT 0,
                    giris_noktasi BOOLEAN DEFAULT FALSE,
                    siralama INTEGER DEFAULT 0,
                    gezinti_suresi INTEGER DEFAULT 5,
                    tileset_url VARCHAR(500),
                    cesium_ion_asset_id INTEGER,
                    bagli_bolgeler INTEGER[],
                    olusturulma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    guncellenme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            print("  [OK] ic_mekan_bolge tablosu")
        except Exception as e:
            print(f"  [-] ic_mekan_bolge: {e}")
        
        # ic_mekan_rota tablosu
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ic_mekan_rota (
                    id SERIAL PRIMARY KEY,
                    yapi_id INTEGER REFERENCES yapi(id),
                    rota_adi VARCHAR(255) NOT NULL,
                    rota_adi_en VARCHAR(255),
                    aciklama TEXT,
                    bolge_siralamasi INTEGER[] NOT NULL,
                    toplam_sure INTEGER,
                    zorluk_seviyesi VARCHAR(20) DEFAULT 'kolay',
                    engelli_erisimi BOOLEAN DEFAULT TRUE,
                    olusturulma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            print("  [OK] ic_mekan_rota tablosu")
        except Exception as e:
            print(f"  [-] ic_mekan_rota: {e}")
        
        # metadata tablosu (ISO 19115)
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS metadata (
                    id SERIAL PRIMARY KEY,
                    yapi_id INTEGER REFERENCES yapi(id),
                    katman_id INTEGER,
                    ic_mekan_bolge_id INTEGER,
                    baslik VARCHAR(500) NOT NULL,
                    baslik_en VARCHAR(500),
                    ozet TEXT,
                    ozet_en TEXT,
                    amac TEXT,
                    anahtar_kelimeler TEXT[],
                    dil VARCHAR(10) DEFAULT 'tur',
                    karakter_seti VARCHAR(20) DEFAULT 'utf8',
                    konu_kategorisi VARCHAR(50) DEFAULT 'structure',
                    bbox_west NUMERIC(10,6),
                    bbox_east NUMERIC(10,6),
                    bbox_south NUMERIC(10,6),
                    bbox_north NUMERIC(10,6),
                    zamansal_baslangic DATE,
                    zamansal_bitis DATE,
                    kaynak_adi VARCHAR(255),
                    kaynak_tarihi DATE,
                    kaynak_turu VARCHAR(50),
                    kalite_seviyesi VARCHAR(50) DEFAULT 'dataset',
                    kalite_aciklama TEXT,
                    konum_dogrulugu NUMERIC(8,4),
                    tamamlanma_orani NUMERIC(5,2),
                    erisim_kisitlamasi VARCHAR(50) DEFAULT 'acik',
                    kullanim_kisitlamasi TEXT,
                    diger_kisitlamalar TEXT,
                    sorumlu_kisi VARCHAR(255),
                    sorumlu_kurum VARCHAR(255),
                    sorumlu_email VARCHAR(255),
                    sorumlu_telefon VARCHAR(50),
                    sorumlu_rol VARCHAR(50) DEFAULT 'pointOfContact',
                    guncelleme_frekansi VARCHAR(50) DEFAULT 'gerektiginde',
                    son_guncelleme_tarihi TIMESTAMP,
                    sonraki_guncelleme_tarihi DATE,
                    bakim_notu TEXT,
                    dagitim_formati VARCHAR(100),
                    dagitim_boyutu NUMERIC(12,2),
                    erisim_url VARCHAR(500),
                    inspire_tema VARCHAR(100) DEFAULT 'Buildings',
                    inspire_uyumlu BOOLEAN DEFAULT TRUE,
                    tucbs_uyumlu BOOLEAN DEFAULT TRUE,
                    metadata_olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata_guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            print("  [OK] metadata tablosu")
        except Exception as e:
            print(f"  [-] metadata: {e}")
        
        # corine_arazi_ortusi tablosu
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS corine_arazi_ortusi (
                    id SERIAL PRIMARY KEY,
                    kod VARCHAR(10) UNIQUE NOT NULL,
                    seviye_1 VARCHAR(100),
                    seviye_2 VARCHAR(100),
                    seviye_3 VARCHAR(100),
                    aciklama TEXT,
                    renk_kodu VARCHAR(7)
                );
            """))
            print("  [OK] corine_arazi_ortusi tablosu")
        except Exception as e:
            print(f"  [-] corine_arazi_ortusi: {e}")
        
        conn.commit()
        
        # 6. Index'leri olustur
        print("\n[6/6] Index'ler olusturuluyor...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_yapi_bina_adi ON yapi(bina_adi);",
            "CREATE INDEX IF NOT EXISTS idx_yapi_ilce ON yapi(ilce);",
            "CREATE INDEX IF NOT EXISTS idx_yapi_yapi_turu ON yapi(yapi_turu);",
            "CREATE INDEX IF NOT EXISTS idx_ic_mekan_bolge_yapi ON ic_mekan_bolge(yapi_id);",
            "CREATE INDEX IF NOT EXISTS idx_metadata_yapi ON metadata(yapi_id);"
        ]
        
        for idx in indexes:
            try:
                conn.execute(text(idx))
                print(f"  [OK] Index eklendi")
            except Exception as e:
                print(f"  [-] Index hatasi: {str(e)[:50]}")
        
        conn.commit()
    
    print("\n" + "=" * 60)
    print("[OK] Migration tamamlandi!")
    print("=" * 60)
    
    # Tablo durumu
    print("\nMevcut tablolar:")
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
    run_migration()

