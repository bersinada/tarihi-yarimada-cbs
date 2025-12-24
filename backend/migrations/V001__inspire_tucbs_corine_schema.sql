-- ============================================================================
-- TARİHİ YARIMADA CBS - VERITABANI REFACTORING MİGRASYONU
-- ============================================================================
-- Standartlar: INSPIRE (Buildings), TÜCBS (Bina Teması v2.0), ISO 19115, CORINE
-- Versiyon: 1.0.0
-- Tarih: 2024
-- ============================================================================

-- İşlem başlamadan önce backup önerisi (script dışında yapılmalı)
-- pg_dump -Fc tarihi_yarimada > backup_pre_migration.dump

BEGIN;

-- ============================================================================
-- BÖLÜM 1: PostGIS UZANTILARI
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- INSPIRE localId için

-- ============================================================================
-- BÖLÜM 2: ENUMLAR VE DOMAIN TİPLERİ (INSPIRE & TÜCBS)
-- ============================================================================

-- INSPIRE LoD Seviyeleri (3B Detay)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'lod_seviyesi_enum') THEN
        CREATE TYPE lod_seviyesi_enum AS ENUM (
            'LoD0',   -- Taban/Çatı poligonları
            'LoD1',   -- Blok modeller (prizmatik)
            'LoD2',   -- Çatı yapısı belirgin
            'LoD3',   -- Detaylı mimari öğeler
            'LoD4'    -- İç mekan dahil
        );
    END IF;
END $$;

-- TÜCBS Yapı Türleri
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'yapi_turu_enum') THEN
        CREATE TYPE yapi_turu_enum AS ENUM (
            'konut',
            'ticari',
            'sanayi',
            'resmi',
            'egitim',
            'saglik',
            'dini',          -- Cami, kilise, havra vb.
            'kulturel',      -- Müze, kütüphane vb.
            'tarihi',        -- Tarihi yapı (genel)
            'anit',          -- Anıt/abide
            'askeri',
            'diger'
        );
    END IF;
END $$;

-- TÜCBS Yapı Durumu
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'yapi_durumu_enum') THEN
        CREATE TYPE yapi_durumu_enum AS ENUM (
            'kullanilabilir',
            'onarim_gerekli',
            'restorasyon_altinda',
            'harap',
            'yikilmis',
            'insaat_halinde'
        );
    END IF;
END $$;

-- INSPIRE Yapı Niteliği
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'building_nature_enum') THEN
        CREATE TYPE building_nature_enum AS ENUM (
            'arch',              -- Kemer
            'bunker',            -- Sığınak
            'castle',            -- Kale
            'caveBuilding',      -- Mağara yapı
            'chapel',            -- Şapel
            'church',            -- Kilise
            'mosque',            -- Cami
            'synagogue',         -- Havra
            'tower',             -- Kule
            'lighthouse',        -- Deniz feneri
            'monument',          -- Anıt
            'windmill',          -- Yel değirmeni
            'religiousBuilding', -- Dini yapı (genel)
            'historicBuilding',  -- Tarihi yapı
            'other'              -- Diğer
        );
    END IF;
END $$;

-- TÜCBS Mülkiyet Durumu
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mulkiyet_durumu_enum') THEN
        CREATE TYPE mulkiyet_durumu_enum AS ENUM (
            'kamu',
            'ozel',
            'vakif',
            'karma',
            'belirsiz'
        );
    END IF;
END $$;

-- ISO 19115 Güncelleme Frekansı
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'guncelleme_frekansi_enum') THEN
        CREATE TYPE guncelleme_frekansi_enum AS ENUM (
            'surekli',       -- continual
            'gunluk',        -- daily
            'haftalik',      -- weekly
            'onbesgunluk',   -- fortnightly
            'aylik',         -- monthly
            'uc_aylik',      -- quarterly
            'alti_aylik',    -- biannually
            'yillik',        -- annually
            'gerektiginde',  -- asNeeded
            'duzensiz',      -- irregular
            'planlanmamis',  -- notPlanned
            'bilinmiyor'     -- unknown
        );
    END IF;
END $$;

-- ISO 19115 Erişim Kısıtlaması
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'erisim_kisitlamasi_enum') THEN
        CREATE TYPE erisim_kisitlamasi_enum AS ENUM (
            'acik',                -- Açık erişim
            'sinirli',             -- Sınırlı erişim
            'telif_hakki',         -- Copyright
            'patent',              -- Patent
            'ticari_gizlilik',     -- Trade secret
            'lisans',              -- Licence
            'fikri_mulkiyet',      -- Intellectual property
            'kisitlanmis',         -- Restricted
            'diger'                -- Other restriction
        );
    END IF;
END $$;

-- ============================================================================
-- BÖLÜM 3: YAPI TABLOSU REFACTORING (TÜCBS + INSPIRE)
-- ============================================================================

-- 3.1: Geometri sütunu ekle (önce, veri dönüşümünden önce)
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS geom geometry(PointZ, 4326);

-- 3.2: INSPIRE ID sütunları ekle
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS inspire_namespace VARCHAR(100) DEFAULT 'TR.TUCBS.BINA';
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS inspire_local_id UUID DEFAULT uuid_generate_v4();
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS inspire_version_id VARCHAR(50);

-- 3.3: TÜCBS Bina Teması v2.0 - SoyutYapi ve SoyutBina öznitelikleri
-- SoyutYapi öznitelikleri
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS yapi_turu yapi_turu_enum DEFAULT 'dini';
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS yapi_durumu yapi_durumu_enum DEFAULT 'kullanilabilir';
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS tescil_no VARCHAR(50);           -- Kültür varlığı tescil no
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS tescil_tarihi DATE;
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS koruma_grubu VARCHAR(20);        -- I. Grup, II. Grup vb.

-- SoyutBina öznitelikleri  
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS bina_yuksekligi NUMERIC(6,2);    -- Metre cinsinden
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS kat_sayisi INTEGER;
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS bodrum_kat_sayisi INTEGER DEFAULT 0;
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS yapi_alani NUMERIC(12,2);        -- m²
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS toplam_insaat_alani NUMERIC(12,2); -- m²
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS cephe_uzunlugu NUMERIC(8,2);     -- Metre

-- INSPIRE Building öznitelikleri
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS building_nature building_nature_enum DEFAULT 'mosque';
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS lod_seviyesi lod_seviyesi_enum DEFAULT 'LoD3';
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS lod_0_footprint geometry(Polygon, 4326);  -- Taban izi
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS lod_0_roofedge geometry(Polygon, 4326);   -- Çatı izi

-- TÜCBS Ek öznitelikler
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS mulkiyet_durumu mulkiyet_durumu_enum DEFAULT 'vakif';
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS malik_adi VARCHAR(255);
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS ada_no VARCHAR(20);
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS parsel_no VARCHAR(20);
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS mahalle VARCHAR(100);
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS sokak VARCHAR(255);
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS kapi_no VARCHAR(20);
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS posta_kodu VARCHAR(10);

-- CORINE Arazi Örtüsü Referansı
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS land_cover_code VARCHAR(10);      -- CORINE kodu: Örn: "1.1.1", "1.2.1"
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS land_cover_desc VARCHAR(255);     -- CORINE açıklaması

-- 3.4: Mevcut sütun isimlerini TÜCBS'ye uygun hale getir
-- ad -> bina_adi
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'yapi' AND column_name = 'ad')
       AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'yapi' AND column_name = 'bina_adi')
    THEN
        ALTER TABLE yapi RENAME COLUMN ad TO bina_adi;
    END IF;
END $$;

-- yapim_yili -> insaat_tarihi (String'den DATE'e dönüşüm gerekebilir, şimdilik String kalacak)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'yapi' AND column_name = 'yapim_yili')
       AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'yapi' AND column_name = 'insaat_tarihi')
    THEN
        ALTER TABLE yapi RENAME COLUMN yapim_yili TO insaat_tarihi;
    END IF;
END $$;

-- tur -> legacy olarak kalsın, yapi_turu enum kullanılacak
-- Mevcut tur sütunu varsa mapping yapılabilir

-- 3.5: İngilizce eşdeğer sütunlar (Çok dilli destek için)
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS building_name_en VARCHAR(255);
ALTER TABLE yapi ADD COLUMN IF NOT EXISTS description_en TEXT;

-- ============================================================================
-- BÖLÜM 4: İÇ MEKAN NAVİGASYON TABLOSU (Cesium İç Mekan)
-- ============================================================================

-- İç mekan bölgeleri/odaları tanımlama tablosu
CREATE TABLE IF NOT EXISTS ic_mekan_bolge (
    id SERIAL PRIMARY KEY,
    yapi_id INTEGER REFERENCES yapi(id) ON DELETE CASCADE,
    
    -- Bölge tanımlama
    bolge_adi VARCHAR(255) NOT NULL,
    bolge_adi_en VARCHAR(255),
    bolge_turu VARCHAR(50),                -- 'giris', 'ana_mekan', 'galeri', 'koridor', 'merdiven' vb.
    aciklama TEXT,
    
    -- 3D Pozisyon (Cesium için)
    geom geometry(PointZ, 4326),           -- Merkez noktası
    kamera_pozisyon geometry(PointZ, 4326), -- Kameranın bakış noktası
    kamera_hedef geometry(PointZ, 4326),    -- Kameranın baktığı nokta
    kamera_heading NUMERIC(6,2) DEFAULT 0,  -- Derece
    kamera_pitch NUMERIC(6,2) DEFAULT -30,  -- Derece
    kamera_roll NUMERIC(6,2) DEFAULT 0,     -- Derece
    
    -- Navigasyon
    giris_noktasi BOOLEAN DEFAULT FALSE,   -- Giriş kapısı noktası mı?
    siralama INTEGER DEFAULT 0,            -- Tur sıralaması
    gezinti_suresi INTEGER DEFAULT 5,      -- Saniye cinsinden bekleme süresi
    
    -- 3D Tiles/Model referansı
    tileset_url VARCHAR(500),              -- Bu bölge için spesifik tileset
    cesium_ion_asset_id INTEGER,           -- Cesium Ion Asset ID
    
    -- Bağlantılar (komşu bölgeler)
    bagli_bolgeler INTEGER[],              -- Bağlı bölge ID'leri
    
    -- Timestamps
    olusturulma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    guncellenme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- İç mekan navigasyon rotaları
CREATE TABLE IF NOT EXISTS ic_mekan_rota (
    id SERIAL PRIMARY KEY,
    yapi_id INTEGER REFERENCES yapi(id) ON DELETE CASCADE,
    
    rota_adi VARCHAR(255) NOT NULL,
    rota_adi_en VARCHAR(255),
    aciklama TEXT,
    
    -- Rota bölgeleri (sıralı)
    bolge_siralamasi INTEGER[] NOT NULL,   -- ic_mekan_bolge ID'leri sıralı
    
    -- Rota özellikleri
    toplam_sure INTEGER,                   -- Saniye
    zorluk_seviyesi VARCHAR(20) DEFAULT 'kolay', -- 'kolay', 'orta', 'zor'
    engelli_erisimi BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    olusturulma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- BÖLÜM 5: AÇIKLAMALAR TABLOSU GEOMETRİ DÖNÜŞÜMÜ
-- ============================================================================

-- 5.1: Geometri sütunu ekle
ALTER TABLE aciklamalar ADD COLUMN IF NOT EXISTS geom geometry(PointZ, 4326);

-- 5.2: Mevcut x, y, z verilerini PostGIS geometriye dönüştür
UPDATE aciklamalar 
SET geom = ST_SetSRID(ST_MakePoint(x, y, COALESCE(z, 0)), 4326)
WHERE x IS NOT NULL AND y IS NOT NULL AND geom IS NULL;

-- 5.3: İç mekan bölge referansı ekle
ALTER TABLE aciklamalar ADD COLUMN IF NOT EXISTS ic_mekan_bolge_id INTEGER REFERENCES ic_mekan_bolge(id);

-- ============================================================================
-- BÖLÜM 6: ISO 19115/19139 METADATA TABLOSU
-- ============================================================================

CREATE TABLE IF NOT EXISTS metadata (
    id SERIAL PRIMARY KEY,
    
    -- İlişkilendirme (hangi veri seti için)
    yapi_id INTEGER REFERENCES yapi(id) ON DELETE CASCADE,
    katman_id INTEGER REFERENCES katmanlar(id) ON DELETE CASCADE,
    ic_mekan_bolge_id INTEGER REFERENCES ic_mekan_bolge(id) ON DELETE CASCADE,
    
    -- MD_Identification - Tanımlama
    baslik VARCHAR(500) NOT NULL,          -- title
    baslik_en VARCHAR(500),                -- alternateTitle
    ozet TEXT,                             -- abstract
    ozet_en TEXT,
    amac TEXT,                             -- purpose
    anahtar_kelimeler TEXT[],              -- keywords
    
    -- MD_DataIdentification - Veri Tanımlama
    dil VARCHAR(10) DEFAULT 'tur',         -- language (ISO 639-2)
    karakter_seti VARCHAR(20) DEFAULT 'utf8', -- characterSet
    konu_kategorisi VARCHAR(50) DEFAULT 'structure', -- topicCategory
    
    -- Coğrafi Kapsam (EX_GeographicBoundingBox)
    bbox_west NUMERIC(10,6),
    bbox_east NUMERIC(10,6),
    bbox_south NUMERIC(10,6),
    bbox_north NUMERIC(10,6),
    
    -- Zamansal Kapsam
    zamansal_baslangic DATE,
    zamansal_bitis DATE,
    
    -- CI_Citation - Kaynak Bilgisi
    kaynak_adi VARCHAR(255),
    kaynak_tarihi DATE,
    kaynak_turu VARCHAR(50),               -- 'creation', 'publication', 'revision'
    
    -- DQ_DataQuality - Veri Kalitesi
    kalite_seviyesi VARCHAR(50) DEFAULT 'dataset', -- scope
    kalite_aciklama TEXT,                  -- lineage/statement
    konum_dogrulugu NUMERIC(8,4),          -- Metre cinsinden konum doğruluğu
    tamamlanma_orani NUMERIC(5,2),         -- Yüzde (0-100)
    
    -- MD_Constraints - Kısıtlamalar
    erisim_kisitlamasi erisim_kisitlamasi_enum DEFAULT 'acik',
    kullanim_kisitlamasi TEXT,
    diger_kisitlamalar TEXT,
    
    -- CI_ResponsibleParty - Sorumlu Taraf
    sorumlu_kisi VARCHAR(255),
    sorumlu_kurum VARCHAR(255),
    sorumlu_email VARCHAR(255),
    sorumlu_telefon VARCHAR(50),
    sorumlu_rol VARCHAR(50) DEFAULT 'pointOfContact', -- role
    
    -- MD_MaintenanceInformation - Bakım Bilgisi
    guncelleme_frekansi guncelleme_frekansi_enum DEFAULT 'gerektiginde',
    son_guncelleme_tarihi TIMESTAMP,
    sonraki_guncelleme_tarihi DATE,
    bakim_notu TEXT,
    
    -- MD_Distribution - Dağıtım Bilgisi
    dagitim_formati VARCHAR(100),          -- '3D Tiles', 'Point Cloud', 'GeoJSON' vb.
    dagitim_boyutu NUMERIC(12,2),          -- MB cinsinden
    erisim_url VARCHAR(500),
    
    -- INSPIRE Spesifik
    inspire_tema VARCHAR(100) DEFAULT 'Buildings',
    inspire_uyumlu BOOLEAN DEFAULT TRUE,
    tucbs_uyumlu BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    metadata_olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata_guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- BÖLÜM 7: KATMANLAR TABLOSU GÜNCELLEMELERİ
-- ============================================================================

-- İç mekan desteği için ek sütunlar
ALTER TABLE katmanlar ADD COLUMN IF NOT EXISTS ic_mekan BOOLEAN DEFAULT FALSE;
ALTER TABLE katmanlar ADD COLUMN IF NOT EXISTS cesium_ion_asset_id INTEGER;
ALTER TABLE katmanlar ADD COLUMN IF NOT EXISTS baslangic_kamera_pozisyon geometry(PointZ, 4326);

-- ============================================================================
-- BÖLÜM 8: YAPI_METADATA TABLOSU GÜNCELLEMELERİ
-- ============================================================================

-- İç mekan 3D Tiles URL'i ekle
ALTER TABLE yapi_metadata ADD COLUMN IF NOT EXISTS ic_mekan_tileset_url VARCHAR(500);
ALTER TABLE yapi_metadata ADD COLUMN IF NOT EXISTS ic_mekan_ion_asset_id INTEGER;

-- Geometri referans noktası
ALTER TABLE yapi_metadata ADD COLUMN IF NOT EXISTS merkez_nokta geometry(PointZ, 4326);
ALTER TABLE yapi_metadata ADD COLUMN IF NOT EXISTS giris_noktasi geometry(PointZ, 4326);

-- ============================================================================
-- BÖLÜM 9: CORINE ARAZİ ÖRTÜSÜ REFERANS TABLOSU
-- ============================================================================

CREATE TABLE IF NOT EXISTS corine_arazi_ortusi (
    id SERIAL PRIMARY KEY,
    kod VARCHAR(10) UNIQUE NOT NULL,       -- "1.1.1", "1.2.1" vb.
    seviye_1 VARCHAR(100),                 -- Ana sınıf: "Yapay Yüzeyler"
    seviye_2 VARCHAR(100),                 -- Alt sınıf: "Kentsel Yapı"
    seviye_3 VARCHAR(100),                 -- Detay: "Sürekli Kentsel Yapı"
    aciklama TEXT,
    renk_kodu VARCHAR(7)                   -- HEX renk kodu harita için
);

-- CORINE referans verilerini ekle (Yapay Yüzeyler - Kentsel)
INSERT INTO corine_arazi_ortusi (kod, seviye_1, seviye_2, seviye_3, aciklama, renk_kodu)
VALUES 
    ('1.1.1', 'Yapay Yüzeyler', 'Kentsel Yapı', 'Sürekli Kentsel Yapı', 'Binaların, yolların ve yapay yüzeylerin oranı %80''den fazla olan alanlar', '#E6004D'),
    ('1.1.2', 'Yapay Yüzeyler', 'Kentsel Yapı', 'Süreksiz Kentsel Yapı', 'Binaların, yolların ve yapay yüzeylerin oranı %30-%80 arasında olan alanlar', '#FF0000'),
    ('1.2.1', 'Yapay Yüzeyler', 'Sanayi, Ticaret, Ulaşım', 'Sanayi veya Ticari Birimler', 'Sanayi tesisleri, ticari alanlar', '#CC4DF2'),
    ('1.2.2', 'Yapay Yüzeyler', 'Sanayi, Ticaret, Ulaşım', 'Karayolu ve Demiryolu Ağları', 'Ulaşım altyapısı', '#CC4DF2'),
    ('1.4.2', 'Yapay Yüzeyler', 'Yapay, Tarım Dışı Yeşil Alanlar', 'Spor ve Dinlenme Alanları', 'Parklar, bahçeler, spor alanları', '#00FF00')
ON CONFLICT (kod) DO NOTHING;

-- ============================================================================
-- BÖLÜM 10: ÖRNEK VERİ GÜNCELLEMESİ
-- ============================================================================

-- Molla Hüsrev Camii için örnek veri güncelleme
UPDATE yapi SET
    -- Geometri (yaklaşık koordinatlar)
    geom = ST_SetSRID(ST_MakePoint(28.9593, 41.0135, 50), 4326),
    
    -- INSPIRE ID
    inspire_namespace = 'TR.TUCBS.BINA',
    inspire_version_id = '2024-01',
    
    -- TÜCBS Öznitelikleri
    yapi_turu = 'dini',
    yapi_durumu = 'kullanilabilir',
    koruma_grubu = 'I. Grup',
    building_nature = 'mosque',
    lod_seviyesi = 'LoD3',
    mulkiyet_durumu = 'vakif',
    mahalle = 'Molla Hüsrev',
    
    -- CORINE
    land_cover_code = '1.1.1',
    land_cover_desc = 'Sürekli Kentsel Yapı'
    
WHERE bina_adi = 'Molla Hüsrev Camii' OR ad = 'Molla Hüsrev Camii';

-- ============================================================================
-- BÖLÜM 11: İÇ MEKAN ÖRNEK VERİSİ
-- ============================================================================

-- Molla Hüsrev Camii için iç mekan bölgeleri (yapi_id 1 varsayımıyla)
INSERT INTO ic_mekan_bolge (yapi_id, bolge_adi, bolge_adi_en, bolge_turu, aciklama, geom, kamera_pozisyon, kamera_hedef, kamera_heading, kamera_pitch, giris_noktasi, siralama, gezinti_suresi)
SELECT 
    y.id,
    'Ana Giriş Kapısı',
    'Main Entrance',
    'giris',
    'Caminin ana giriş kapısı - İç mekan turunun başlangıç noktası',
    ST_SetSRID(ST_MakePoint(28.95925, 41.01345, 51), 4326),
    ST_SetSRID(ST_MakePoint(28.95920, 41.01340, 53), 4326),
    ST_SetSRID(ST_MakePoint(28.95930, 41.01350, 51), 4326),
    0, -15, TRUE, 1, 5
FROM yapi y 
WHERE y.bina_adi = 'Molla Hüsrev Camii' OR y.ad = 'Molla Hüsrev Camii'
ON CONFLICT DO NOTHING;

INSERT INTO ic_mekan_bolge (yapi_id, bolge_adi, bolge_adi_en, bolge_turu, aciklama, geom, kamera_pozisyon, kamera_hedef, kamera_heading, kamera_pitch, giris_noktasi, siralama, gezinti_suresi)
SELECT 
    y.id,
    'Son Cemaat Yeri',
    'Last Congregation Area',
    'galeri',
    'Giriş sonrası son cemaat mahalli',
    ST_SetSRID(ST_MakePoint(28.95928, 41.01348, 52), 4326),
    ST_SetSRID(ST_MakePoint(28.95923, 41.01343, 54), 4326),
    ST_SetSRID(ST_MakePoint(28.95933, 41.01353, 52), 4326),
    45, -20, FALSE, 2, 8
FROM yapi y 
WHERE y.bina_adi = 'Molla Hüsrev Camii' OR y.ad = 'Molla Hüsrev Camii'
ON CONFLICT DO NOTHING;

INSERT INTO ic_mekan_bolge (yapi_id, bolge_adi, bolge_adi_en, bolge_turu, aciklama, geom, kamera_pozisyon, kamera_hedef, kamera_heading, kamera_pitch, giris_noktasi, siralama, gezinti_suresi)
SELECT 
    y.id,
    'Ana Harim (İbadet Alanı)',
    'Main Prayer Hall',
    'ana_mekan',
    'Caminin ana ibadet alanı - Kubbe ve mihrap görünümü',
    ST_SetSRID(ST_MakePoint(28.95935, 41.01355, 53), 4326),
    ST_SetSRID(ST_MakePoint(28.95930, 41.01350, 55), 4326),
    ST_SetSRID(ST_MakePoint(28.95940, 41.01360, 60), 4326),
    90, -30, FALSE, 3, 15
FROM yapi y 
WHERE y.bina_adi = 'Molla Hüsrev Camii' OR y.ad = 'Molla Hüsrev Camii'
ON CONFLICT DO NOTHING;

INSERT INTO ic_mekan_bolge (yapi_id, bolge_adi, bolge_adi_en, bolge_turu, aciklama, geom, kamera_pozisyon, kamera_hedef, kamera_heading, kamera_pitch, giris_noktasi, siralama, gezinti_suresi)
SELECT 
    y.id,
    'Mihrap',
    'Mihrab',
    'ana_mekan',
    'Kıble yönünü gösteren mihrap nişi',
    ST_SetSRID(ST_MakePoint(28.95942, 41.01362, 52), 4326),
    ST_SetSRID(ST_MakePoint(28.95938, 41.01358, 53), 4326),
    ST_SetSRID(ST_MakePoint(28.95945, 41.01365, 52), 4326),
    135, -10, FALSE, 4, 10
FROM yapi y 
WHERE y.bina_adi = 'Molla Hüsrev Camii' OR y.ad = 'Molla Hüsrev Camii'
ON CONFLICT DO NOTHING;

INSERT INTO ic_mekan_bolge (yapi_id, bolge_adi, bolge_adi_en, bolge_turu, aciklama, geom, kamera_pozisyon, kamera_hedef, kamera_heading, kamera_pitch, giris_noktasi, siralama, gezinti_suresi)
SELECT 
    y.id,
    'Minber',
    'Minbar',
    'ana_mekan',
    'Hutbe okunan minber',
    ST_SetSRID(ST_MakePoint(28.95940, 41.01358, 52), 4326),
    ST_SetSRID(ST_MakePoint(28.95935, 41.01353, 54), 4326),
    ST_SetSRID(ST_MakePoint(28.95945, 41.01363, 55), 4326),
    180, -25, FALSE, 5, 8
FROM yapi y 
WHERE y.bina_adi = 'Molla Hüsrev Camii' OR y.ad = 'Molla Hüsrev Camii'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- BÖLÜM 12: METADATA ÖRNEK VERİSİ
-- ============================================================================

INSERT INTO metadata (
    yapi_id,
    baslik,
    baslik_en,
    ozet,
    ozet_en,
    anahtar_kelimeler,
    bbox_west, bbox_east, bbox_south, bbox_north,
    kalite_aciklama,
    konum_dogrulugu,
    tamamlanma_orani,
    erisim_kisitlamasi,
    sorumlu_kurum,
    sorumlu_email,
    guncelleme_frekansi,
    dagitim_formati,
    inspire_tema
)
SELECT 
    y.id,
    'Molla Hüsrev Camii 3D Modeli',
    '3D Model of Molla Husrev Mosque',
    'İstanbul Fatih ilçesinde bulunan Molla Hüsrev Camii''nin fotogrametrik yöntemlerle üretilmiş yüksek çözünürlüklü 3D modeli.',
    'High-resolution 3D model of Molla Husrev Mosque in Fatih, Istanbul, produced using photogrammetric methods.',
    ARRAY['tarihi cami', 'osmanlı', 'fatih', '3d model', 'nokta bulutu', 'kültürel miras'],
    28.958, 28.961, 41.012, 41.015,
    'Fotogrametrik veri toplama, Reality Capture ile işleme, 3D Tiles formatına dönüşüm.',
    0.05,  -- 5 cm konum doğruluğu
    95.0,  -- %95 tamamlanmış
    'acik',
    'İTÜ CBS Laboratuvarı',
    'cbs@itu.edu.tr',
    'yillik',
    '3D Tiles, Point Cloud (LAS)',
    'Buildings'
FROM yapi y 
WHERE y.bina_adi = 'Molla Hüsrev Camii' OR y.ad = 'Molla Hüsrev Camii'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- BÖLÜM 13: İNDEKSLER
-- ============================================================================

-- Geometri indeksleri (GIST)
CREATE INDEX IF NOT EXISTS idx_yapi_geom ON yapi USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_yapi_lod0_footprint ON yapi USING GIST(lod_0_footprint);
CREATE INDEX IF NOT EXISTS idx_aciklamalar_geom ON aciklamalar USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_ic_mekan_bolge_geom ON ic_mekan_bolge USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_yapi_metadata_merkez ON yapi_metadata USING GIST(merkez_nokta);

-- INSPIRE ID indeksi
CREATE INDEX IF NOT EXISTS idx_yapi_inspire_id ON yapi(inspire_namespace, inspire_local_id);

-- TÜCBS arama indeksleri
CREATE INDEX IF NOT EXISTS idx_yapi_bina_adi ON yapi(bina_adi);
CREATE INDEX IF NOT EXISTS idx_yapi_yapi_turu ON yapi(yapi_turu);
CREATE INDEX IF NOT EXISTS idx_yapi_ilce ON yapi(ilce);
CREATE INDEX IF NOT EXISTS idx_yapi_mahalle ON yapi(mahalle);
CREATE INDEX IF NOT EXISTS idx_yapi_koruma_grubu ON yapi(koruma_grubu);

-- CORINE indeksi
CREATE INDEX IF NOT EXISTS idx_yapi_land_cover ON yapi(land_cover_code);

-- İç mekan indeksleri
CREATE INDEX IF NOT EXISTS idx_ic_mekan_bolge_yapi ON ic_mekan_bolge(yapi_id);
CREATE INDEX IF NOT EXISTS idx_ic_mekan_bolge_giris ON ic_mekan_bolge(giris_noktasi) WHERE giris_noktasi = TRUE;

-- Metadata indeksleri
CREATE INDEX IF NOT EXISTS idx_metadata_yapi ON metadata(yapi_id);

-- ============================================================================
-- BÖLÜM 14: YARDIMCI FONKSİYONLAR
-- ============================================================================

-- INSPIRE ID oluşturma fonksiyonu
CREATE OR REPLACE FUNCTION generate_inspire_id(namespace VARCHAR, local_id UUID)
RETURNS VARCHAR AS $$
BEGIN
    RETURN namespace || '.' || local_id::VARCHAR;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- İç mekan giriş noktası getirme fonksiyonu
CREATE OR REPLACE FUNCTION get_ic_mekan_giris(p_yapi_id INTEGER)
RETURNS TABLE (
    bolge_id INTEGER,
    bolge_adi VARCHAR,
    lon NUMERIC,
    lat NUMERIC,
    height NUMERIC,
    heading NUMERIC,
    pitch NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        imb.id,
        imb.bolge_adi,
        ST_X(imb.kamera_pozisyon)::NUMERIC,
        ST_Y(imb.kamera_pozisyon)::NUMERIC,
        ST_Z(imb.kamera_pozisyon)::NUMERIC,
        imb.kamera_heading,
        imb.kamera_pitch
    FROM ic_mekan_bolge imb
    WHERE imb.yapi_id = p_yapi_id AND imb.giris_noktasi = TRUE
    ORDER BY imb.siralama
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- İç mekan tur rotası getirme fonksiyonu
CREATE OR REPLACE FUNCTION get_ic_mekan_tur(p_yapi_id INTEGER)
RETURNS TABLE (
    siralama INTEGER,
    bolge_id INTEGER,
    bolge_adi VARCHAR,
    bolge_turu VARCHAR,
    aciklama TEXT,
    lon NUMERIC,
    lat NUMERIC,
    height NUMERIC,
    heading NUMERIC,
    pitch NUMERIC,
    gezinti_suresi INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        imb.siralama,
        imb.id,
        imb.bolge_adi,
        imb.bolge_turu,
        imb.aciklama,
        ST_X(imb.kamera_pozisyon)::NUMERIC,
        ST_Y(imb.kamera_pozisyon)::NUMERIC,
        ST_Z(imb.kamera_pozisyon)::NUMERIC,
        imb.kamera_heading,
        imb.kamera_pitch,
        imb.gezinti_suresi
    FROM ic_mekan_bolge imb
    WHERE imb.yapi_id = p_yapi_id
    ORDER BY imb.siralama;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- BÖLÜM 15: GÖRÜNÜMLER (VİEWS)
-- ============================================================================

-- INSPIRE uyumlu yapı görünümü
CREATE OR REPLACE VIEW v_inspire_buildings AS
SELECT 
    y.id,
    generate_inspire_id(y.inspire_namespace, y.inspire_local_id) AS inspire_id,
    y.inspire_namespace,
    y.inspire_local_id,
    y.inspire_version_id,
    y.bina_adi AS name,
    y.ad_en AS name_en,
    y.building_nature,
    y.lod_seviyesi,
    y.bina_yuksekligi AS height_above_ground,
    y.kat_sayisi AS number_of_floors_above_ground,
    y.bodrum_kat_sayisi AS number_of_floors_below_ground,
    y.insaat_tarihi AS date_of_construction,
    y.geom,
    y.lod_0_footprint,
    y.lod_0_roofedge
FROM yapi y;

-- TÜCBS uyumlu yapı görünümü
CREATE OR REPLACE VIEW v_tucbs_binalar AS
SELECT 
    y.id,
    y.bina_adi,
    y.yapi_turu,
    y.yapi_durumu,
    y.bina_yuksekligi,
    y.kat_sayisi,
    y.bodrum_kat_sayisi,
    y.yapi_alani,
    y.toplam_insaat_alani,
    y.insaat_tarihi,
    y.tescil_no,
    y.tescil_tarihi,
    y.koruma_grubu,
    y.mulkiyet_durumu,
    y.malik_adi,
    y.ada_no,
    y.parsel_no,
    y.mahalle,
    y.sokak,
    y.kapi_no,
    y.ilce,
    y.geom,
    y.land_cover_code,
    y.land_cover_desc
FROM yapi y;

-- İç mekan navigasyon görünümü
CREATE OR REPLACE VIEW v_ic_mekan_navigasyon AS
SELECT 
    imb.id AS bolge_id,
    y.id AS yapi_id,
    y.bina_adi,
    imb.bolge_adi,
    imb.bolge_adi_en,
    imb.bolge_turu,
    imb.aciklama,
    imb.giris_noktasi,
    imb.siralama,
    imb.gezinti_suresi,
    ST_X(imb.kamera_pozisyon) AS kamera_lon,
    ST_Y(imb.kamera_pozisyon) AS kamera_lat,
    ST_Z(imb.kamera_pozisyon) AS kamera_height,
    imb.kamera_heading,
    imb.kamera_pitch,
    imb.kamera_roll,
    ST_X(imb.kamera_hedef) AS hedef_lon,
    ST_Y(imb.kamera_hedef) AS hedef_lat,
    ST_Z(imb.kamera_hedef) AS hedef_height,
    imb.tileset_url,
    imb.cesium_ion_asset_id
FROM ic_mekan_bolge imb
JOIN yapi y ON y.id = imb.yapi_id
ORDER BY y.id, imb.siralama;

COMMIT;

-- ============================================================================
-- MİGRASYON TAMAMLANDI
-- ============================================================================
-- 
-- Uygulanan Standartlar:
-- ✅ INSPIRE Annex III - Buildings (LoD seviyeleri, inspire_id, building_nature)
-- ✅ TÜCBS Bina Teması v2.0 (SoyutYapı, SoyutBina öznitelikleri)
-- ✅ ISO 19115/19139 (Metadata tablosu)
-- ✅ CORINE Arazi Örtüsü (land_cover_code referansı)
-- ✅ PostGIS Geometri (PointZ, 4326 koordinat sistemi)
-- ✅ İç Mekan Navigasyon Sistemi (Cesium entegrasyonu için)
--
-- Sonraki Adımlar:
-- 1. SQLAlchemy modellerini güncelleyin (database.py)
-- 2. API endpoint'lerini güncelleyin (main.py)
-- 3. Frontend'de Cesium iç mekan navigasyonunu aktifleştirin
-- 4. Gerçek koordinat verilerini ekleyin
-- ============================================================================

