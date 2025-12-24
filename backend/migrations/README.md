# Veritabanı Migration Kılavuzu

## INSPIRE/TÜCBS/ISO 19115/CORINE Uyumlu Şema Güncellemesi

Bu migration, Tarihi Yarımada CBS veritabanını uluslararası ve ulusal standartlara uyumlu hale getirir.

### Uygulanan Standartlar

| Standart | Açıklama |
|----------|----------|
| **INSPIRE Annex III** | Avrupa Birliği Mekansal Veri Altyapısı - Buildings teması |
| **TÜCBS Bina Teması v2.0** | Türkiye Ulusal Coğrafi Bilgi Sistemi standartları |
| **ISO 19115/19139** | Uluslararası coğrafi metadata standardı |
| **CORINE** | Avrupa arazi örtüsü sınıflandırma sistemi |

---

## Migration Çalıştırma

### 1. Önkoşullar

```bash
# PostgreSQL ve PostGIS yüklü olmalı
# PostGIS sürümü: 3.0+
# PostgreSQL sürümü: 12+
```

### 2. Backup Alın (ÖNEMLİ!)

```bash
# Veritabanı yedeği al
pg_dump -Fc tarihi_yarimada > backup_pre_migration.dump
```

### 3. Migration'ı Çalıştır

```bash
# psql ile çalıştır
psql -d tarihi_yarimada -f V001__inspire_tucbs_corine_schema.sql

# Veya Python ile
python -c "
from sqlalchemy import create_engine, text
import os

engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    with open('V001__inspire_tucbs_corine_schema.sql', 'r', encoding='utf-8') as f:
        conn.execute(text(f.read()))
        conn.commit()
print('Migration başarıyla tamamlandı!')
"
```

---

## Yapılan Değişiklikler

### 1. Yeni Tablolar

| Tablo | Açıklama |
|-------|----------|
| `ic_mekan_bolge` | İç mekan bölgeleri/odaları (Cesium navigasyon) |
| `ic_mekan_rota` | Önceden tanımlı tur rotaları |
| `metadata` | ISO 19115 uyumlu üstveri tablosu |
| `corine_arazi_ortusi` | CORINE arazi örtüsü referans tablosu |

### 2. Yapi Tablosu Yeni Sütunlar

#### INSPIRE ID
- `inspire_namespace` - Namespace (varsayılan: TR.TUCBS.BINA)
- `inspire_local_id` - UUID benzersiz tanımlayıcı
- `inspire_version_id` - Versiyon

#### TÜCBS SoyutYapi
- `yapi_turu` - Yapı türü enum (konut, ticari, dini, vb.)
- `yapi_durumu` - Yapı durumu enum
- `tescil_no` - Kültür varlığı tescil numarası
- `koruma_grubu` - I. Grup, II. Grup vb.

#### TÜCBS SoyutBina
- `bina_yuksekligi` - Metre cinsinden
- `kat_sayisi` - Kat sayısı
- `yapi_alani` - m² cinsinden

#### INSPIRE Building
- `building_nature` - Yapı niteliği enum (mosque, church, vb.)
- `lod_seviyesi` - 3B detay seviyesi (LoD0-LoD4)

#### CORINE
- `land_cover_code` - CORINE arazi kodu (1.1.1, 1.2.1, vb.)
- `land_cover_desc` - Açıklama

### 3. Geometri Dönüşümü

```sql
-- Eski: x, y, z ayrı sütunlar
-- Yeni: PostGIS geometry(PointZ, 4326)

ALTER TABLE aciklamalar ADD COLUMN geom geometry(PointZ, 4326);

UPDATE aciklamalar 
SET geom = ST_SetSRID(ST_MakePoint(x, y, COALESCE(z, 0)), 4326)
WHERE x IS NOT NULL AND y IS NOT NULL;
```

### 4. Yeni Görünümler (Views)

- `v_inspire_buildings` - INSPIRE uyumlu yapı görünümü
- `v_tucbs_binalar` - TÜCBS uyumlu bina görünümü
- `v_ic_mekan_navigasyon` - İç mekan navigasyon görünümü

### 5. Yardımcı Fonksiyonlar

- `generate_inspire_id(namespace, local_id)` - INSPIRE ID oluşturur
- `get_ic_mekan_giris(yapi_id)` - İç mekan giriş noktası
- `get_ic_mekan_tur(yapi_id)` - İç mekan tur rotası

---

## API Endpoint'leri

Migration sonrası kullanılabilir yeni endpoint'ler:

```
GET /api/v1/inspire/buildings          # INSPIRE formatında yapılar
GET /api/v1/tucbs/binalar              # TÜCBS formatında binalar
GET /api/v1/yapilar/{id}/ic-mekan-bolgeler   # İç mekan bölgeleri
GET /api/v1/yapilar/{id}/ic-mekan-giris      # Giriş noktası
```

---

## Rollback

Hata durumunda:

```bash
# Backup'tan geri yükle
pg_restore -d tarihi_yarimada -c backup_pre_migration.dump
```

---

## Örnek CORINE Kodları

| Kod | Açıklama |
|-----|----------|
| 1.1.1 | Sürekli Kentsel Yapı (yapı oranı >%80) |
| 1.1.2 | Süreksiz Kentsel Yapı (yapı oranı %30-%80) |
| 1.2.1 | Sanayi veya Ticari Birimler |
| 1.4.2 | Spor ve Dinlenme Alanları |

---

## İletişim

Sorularınız için: cbs@itu.edu.tr

