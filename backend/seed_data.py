"""
Tarihi Yarımada CBS - Veritabanı Seed Scripti
Molla Hüsrev Camii için doğru verilerle tabloları doldurur.
"""

import os
import sys
from pathlib import Path

# Backend modüllerini import edebilmek için path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from backend.database import SessionLocal, engine, Base

def seed_database():
    """Veritabanını örnek verilerle doldur"""
    db = SessionLocal()
    
    try:
        print("Veritabanı seed işlemi başlıyor...")
        
        # 1. Mevcut verileri temizle (opsiyonel - sadece varsa)
        print("Mevcut veriler temizleniyor...")
        try:
            db.execute(text("DELETE FROM ic_mekan_bolge WHERE yapi_id = 1"))
            db.execute(text("DELETE FROM yapi_metadata WHERE yapi_id = 1"))
            db.execute(text("DELETE FROM aciklamalar WHERE yapi_id = 1"))
            db.execute(text("DELETE FROM katmanlar"))
            db.execute(text("DELETE FROM metadata WHERE yapi_id = 1"))
        except Exception as e:
            print(f"  Temizlik sırasında hata (normal olabilir): {e}")
        
        # Yapi tablosunu temizlemeden güncelle
        db.execute(text("""
            UPDATE yapi SET 
                bina_adi = 'Molla Hüsrev Camii',
                ad_en = 'Molla Husrev Mosque',
                tur = 'Cami',
                yapi_turu = 'dini',
                donem = 'Osmanlı - Fatih Dönemi',
                mimar = 'Bilinmiyor (Klasik Osmanlı Üslubu)',
                insaat_tarihi = '1460',
                konum = 'Molla Hüsrev Mahallesi, Fatih',
                ilce = 'Fatih',
                aciklama = 'Fatih Sultan Mehmed döneminin ünlü Şeyhülislamı Molla Hüsrev tarafından 1460 yılında yaptırılan bu cami, klasik Osmanlı mimarisinin erken dönem örneklerinden biridir. Molla Hüsrev, Fatih''in hocası olup İslam hukuku alanındaki eserleriyle tanınır. Cami, medrese ve türbesiyle birlikte bir külliye olarak inşa edilmiştir.',
                building_nature = 'mosque',
                lod_seviyesi = 'LoD3',
                yapi_durumu = 'kullanilabilir',
                koruma_grubu = 'I',
                mulkiyet_durumu = 'vakif',
                mahalle = 'Molla Hüsrev',
                land_cover_code = '1.1.1',
                land_cover_desc = 'Sürekli Kentsel Yapı'
            WHERE id = 1
        """))
        
        # Eğer yapi yoksa ekle
        result = db.execute(text("SELECT COUNT(*) FROM yapi WHERE id = 1"))
        if result.scalar() == 0:
            db.execute(text("""
                INSERT INTO yapi (id, bina_adi, ad_en, tur, yapi_turu, donem, mimar, insaat_tarihi, konum, ilce, aciklama, 
                    building_nature, lod_seviyesi, yapi_durumu, koruma_grubu, mulkiyet_durumu, mahalle, land_cover_code, land_cover_desc)
                VALUES (1, 'Molla Hüsrev Camii', 'Molla Husrev Mosque', 'Cami', 'dini', 'Osmanlı - Fatih Dönemi', 
                    'Bilinmiyor (Klasik Osmanlı Üslubu)', '1460', 'Molla Hüsrev Mahallesi, Fatih', 'Fatih',
                    'Fatih Sultan Mehmed döneminin ünlü Şeyhülislamı Molla Hüsrev tarafından 1460 yılında yaptırılan bu cami, klasik Osmanlı mimarisinin erken dönem örneklerinden biridir.',
                    'mosque', 'LoD3', 'kullanilabilir', 'I', 'vakif', 'Molla Hüsrev', '1.1.1', 'Sürekli Kentsel Yapı')
            """))
        
        # 2. YapiMetadata - Doğru Cesium Ion Asset ID'leri ile
        print("Yapı metadata ekleniyor...")
        db.execute(text("""
            INSERT INTO yapi_metadata (yapi_id, tileset_url, nokta_bulutu_url, ic_mekan_tileset_url, 
                ic_mekan_ion_asset_id, lod_seviyesi, nokta_sayisi, dosya_boyutu_mb)
            VALUES (1, 
                'cesium_ion:4270999',  -- Dış cephe 3D Tiles
                NULL,
                'cesium_ion:4271001',  -- İç mekan 3D Tiles
                4275532,  -- İç mekan Point Cloud
                3, 
                15000000, 
                1920.0
            )
            ON CONFLICT (yapi_id) DO UPDATE SET
                tileset_url = EXCLUDED.tileset_url,
                ic_mekan_tileset_url = EXCLUDED.ic_mekan_tileset_url,
                ic_mekan_ion_asset_id = EXCLUDED.ic_mekan_ion_asset_id
        """))
        
        # 3. İç Mekan Bölgeleri - Cesium navigasyonu için
        print("İç mekan bölgeleri ekleniyor...")
        
        # Molla Hüsrev Camii koordinatları (Cesium Ion model merkezine yakın)
        # Bu değerler 3D modelin gerçek konumuna göre ayarlanmalı
        base_lon = 28.948725
        base_lat = 41.016850
        base_height = 45
        
        ic_mekan_bolgeler = [
            # Giriş kapısı - kamera dışarıdan içeri bakacak şekilde
            ("Giriş Kapısı", "Main Entrance", "giris", "Caminin ana giriş kapısı", True, 0, 5,
             base_lon - 0.0002, base_lat, base_height + 5,  # kamera pozisyon (dışarıda)
             base_lon, base_lat, base_height + 2,  # hedef (kapıya bakıyor)
             90, -15, 0),  # heading: doğuya bakıyor
            
            # Ana ibadet salonu
            ("Ana İbadet Salonu", "Main Prayer Hall", "ana_mekan", "Caminin ana ibadet alanı", False, 1, 10,
             base_lon, base_lat, base_height + 8,
             base_lon + 0.0001, base_lat, base_height + 3,
             90, -25, 0),
            
            # Mihrap bölgesi (kıble yönü - güneydoğu)
            ("Mihrap", "Mihrab", "ana_mekan", "Kıble yönünü gösteren mihrap nişi", False, 2, 8,
             base_lon + 0.0001, base_lat - 0.00005, base_height + 4,
             base_lon + 0.00015, base_lat, base_height + 2,
             135, -10, 0),
            
            # Minber
            ("Minber", "Pulpit", "ana_mekan", "Hutbe okunan minber", False, 3, 6,
             base_lon + 0.00008, base_lat + 0.00003, base_height + 5,
             base_lon + 0.00012, base_lat, base_height + 3,
             120, -20, 0),
            
            # Kadınlar mahfili
            ("Kadınlar Mahfili", "Women's Section", "galeri", "Üst kattaki kadınlar mahfili", False, 4, 7,
             base_lon - 0.00005, base_lat, base_height + 12,
             base_lon + 0.00005, base_lat, base_height + 8,
             90, -35, 0),
            
            # Kubbe altı - yukarıdan aşağı bakış
            ("Kubbe Altı", "Under the Dome", "ana_mekan", "Ana kubbenin altındaki merkezi alan", False, 5, 10,
             base_lon + 0.00005, base_lat, base_height + 18,
             base_lon + 0.00005, base_lat, base_height + 2,
             0, -85, 0)
        ]
        
        for bolge in ic_mekan_bolgeler:
            db.execute(text("""
                INSERT INTO ic_mekan_bolge (yapi_id, bolge_adi, bolge_adi_en, bolge_turu, aciklama,
                    giris_noktasi, siralama, gezinti_suresi,
                    kamera_pozisyon, kamera_hedef, kamera_heading, kamera_pitch, kamera_roll)
                VALUES (1, :bolge_adi, :bolge_adi_en, :bolge_turu, :aciklama,
                    :giris_noktasi, :siralama, :gezinti_suresi,
                    ST_SetSRID(ST_MakePoint(:kp_lon, :kp_lat, :kp_h), 4326),
                    ST_SetSRID(ST_MakePoint(:kh_lon, :kh_lat, :kh_h), 4326),
                    :kamera_heading, :kamera_pitch, :kamera_roll)
            """), {
                "bolge_adi": bolge[0],
                "bolge_adi_en": bolge[1],
                "bolge_turu": bolge[2],
                "aciklama": bolge[3],
                "giris_noktasi": bolge[4],
                "siralama": bolge[5],
                "gezinti_suresi": bolge[6],
                "kp_lon": bolge[7],
                "kp_lat": bolge[8],
                "kp_h": bolge[9],
                "kh_lon": bolge[10],
                "kh_lat": bolge[11],
                "kh_h": bolge[12],
                "kamera_heading": bolge[13],
                "kamera_pitch": bolge[14],
                "kamera_roll": bolge[15]
            })
        
        # 4. Katmanlar - Doğru Cesium Ion Asset ID'leri ile
        print("Katmanlar ekleniyor...")
        katmanlar = [
            ("Molla Hüsrev - Dış Cephe", "3dtiles", "cesium_ion:4270999", True, 1.0, 1, False, 4270999),
            ("Molla Hüsrev - İç Mekan 1", "3dtiles", "cesium_ion:4271001", True, 1.0, 2, True, 4271001),
            ("Molla Hüsrev - İç Mekan 2", "3dtiles", "cesium_ion:4275532", True, 1.0, 3, True, 4275532)
        ]
        
        for katman in katmanlar:
            db.execute(text("""
                INSERT INTO katmanlar (ad, tur, url, gorunur, saydamlik, sira)
                VALUES (:ad, :tur, :url, :gorunur, :saydamlik, :sira)
            """), {
                "ad": katman[0],
                "tur": katman[1],
                "url": katman[2],
                "gorunur": katman[3],
                "saydamlik": katman[4],
                "sira": katman[5]
            })
        
        # 5. Metadata (ISO 19115)
        print("Metadata ekleniyor...")
        db.execute(text("""
            INSERT INTO metadata (yapi_id, baslik, baslik_en, ozet, ozet_en, amac, anahtar_kelimeler,
                dil, karakter_seti, konu_kategorisi,
                bbox_west, bbox_east, bbox_south, bbox_north,
                kaynak_adi, kaynak_turu,
                kalite_seviyesi, kalite_aciklama, konum_dogrulugu, tamamlanma_orani,
                erisim_kisitlamasi,
                sorumlu_kisi, sorumlu_kurum, sorumlu_email, sorumlu_rol,
                guncelleme_frekansi,
                dagitim_formati,
                inspire_tema, inspire_uyumlu, tucbs_uyumlu)
            VALUES (1, 
                'Molla Hüsrev Camii 3D Modeli',
                'Molla Husrev Mosque 3D Model',
                'Fatih döneminden kalma tarihi Molla Hüsrev Camii''nin detaylı 3D taraması ve modeli.',
                'Detailed 3D scan and model of the historic Molla Husrev Mosque from the Fatih period.',
                'Kültürel miras koruma ve belgeleme',
                ARRAY['Molla Hüsrev', 'Cami', 'Osmanlı', 'Fatih', '3D Model', 'Fotogrametri'],
                'tur', 'utf8', 'structure',
                28.958, 28.961, 41.012, 41.015,
                'İTÜ CBS Laboratuvarı', 'creation',
                'dataset', 'Fotogrametrik 3D modelleme, drone ve yersel tarama', 0.02, 98.5,
                'acik',
                'CBS Proje Ekibi', 'İTÜ', 'cbs@itu.edu.tr', 'pointOfContact',
                'yillik',
                '3D Tiles, Point Cloud (LAS/LAZ)',
                'Buildings', TRUE, TRUE)
        """))
        
        # 6. CORINE Arazi Örtüsü Referans Verileri
        print("CORINE referans verileri ekleniyor...")
        corine_data = [
            ("1.1.1", "Yapay yüzeyler", "Kentsel yapı", "Sürekli kentsel yapı", "#E6004D"),
            ("1.1.2", "Yapay yüzeyler", "Kentsel yapı", "Süreksiz kentsel yapı", "#FF00FF"),
            ("1.2.1", "Yapay yüzeyler", "Sanayi, ticaret", "Sanayi veya ticaret birimleri", "#A600CC"),
            ("1.4.2", "Yapay yüzeyler", "Yapay yeşil alanlar", "Spor ve eğlence tesisleri", "#CCFFCC"),
            ("3.1.1", "Orman ve yarı doğal alanlar", "Ormanlar", "Geniş yapraklı orman", "#80FF00"),
            ("5.1.2", "Su alanları", "Kara suları", "Su kütleleri", "#00CCF2")
        ]
        
        for corine in corine_data:
            db.execute(text("""
                INSERT INTO corine_arazi_ortusi (kod, seviye_1, seviye_2, seviye_3, renk_kodu)
                VALUES (:kod, :s1, :s2, :s3, :renk)
                ON CONFLICT (kod) DO NOTHING
            """), {
                "kod": corine[0],
                "s1": corine[1],
                "s2": corine[2],
                "s3": corine[3],
                "renk": corine[4]
            })
        
        db.commit()
        print("[OK] Veritabani seed islemi basariyla tamamlandi!")
        
        # Sonuclari goster
        result = db.execute(text("SELECT COUNT(*) FROM ic_mekan_bolge WHERE yapi_id = 1"))
        print(f"   - {result.scalar()} ic mekan bolgesi eklendi")
        
        result = db.execute(text("SELECT COUNT(*) FROM katmanlar"))
        print(f"   - {result.scalar()} katman eklendi")
        
        result = db.execute(text("SELECT COUNT(*) FROM metadata"))
        print(f"   - {result.scalar()} metadata kaydi eklendi")
        
    except Exception as e:
        db.rollback()
        print(f"[HATA] {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

