# 🏛️ Tarihi Yarımada CBS Platformu

İstanbul Tarihi Yarımada'daki kültürel miras yapılarının 3D modellerini ve nokta bulutu verilerini web ortamında sunan CBS platformu.

## 📋 Proje Hakkında

Bu proje, İTÜ CBS Projeleri dersi kapsamında geliştirilmiştir. Tarihi Yarımada'daki kültürel miras yapılarının (özellikle Molla Hüsrev Camii) 3D modellerini ve point cloud verilerini interaktif bir web arayüzünde sunmayı amaçlamaktadır.

### 🎯 Özellikler

- **Cesium JS** ile 3D Tiles görselleştirme (dış cephe)
- **Potree** ile Point Cloud render (iç mekan)
- **Split View** - İki viewer'ı yan yana karşılaştırma
- **LoD3 Entegrasyonu** - Çevredeki LoD0 yüzeyle birlikte detaylı dış cephe
- Ölçüm araçları (mesafe, alan, yükseklik)
- Anotasyon ekleme
- Katman yönetimi

## 🛠️ Kullanılan Teknolojiler

| Katman | Teknoloji |
|--------|-----------|
| **Frontend** | HTML5, CSS3, JavaScript |
| **3D Görselleştirme** | Cesium JS, Potree |
| **Backend** | FastAPI (Python) |
| **Veritabanı** | PostgreSQL + PostGIS |
| **Veri Formatları** | 3D Tiles, LAS/LAZ (Point Cloud) |

## 📁 Proje Yapısı

```
tarihi-yarimada-cbs/
├── index.html              # Ana HTML sayfası
├── css/
│   └── styles.css          # Stil dosyası
├── js/
│   ├── main.js             # Ana uygulama
│   ├── api.js              # API modülü
│   ├── cesiumViewer.js     # Cesium viewer
│   └── potreeViewer.js     # Potree viewer
├── backend/
│   ├── main.py             # FastAPI uygulaması
│   ├── database.py         # Veritabanı modelleri
│   └── requirements.txt    # Python bağımlılıkları
├── data/                   # 3D veriler (gitignore'da)
│   ├── 3dtiles/
│   └── pointcloud/
└── README.md
```

## 🚀 Kurulum

### Frontend

Frontend sadece statik dosyalardan oluşuyor. Bir HTTP sunucusu ile çalıştırabilirsiniz:

```bash
# Python ile basit HTTP sunucusu
cd tarihi-yarimada-cbs
python -m http.server 8080

# veya Node.js ile
npx serve .
```

Tarayıcıda `http://localhost:8080` adresine gidin.

### Backend

```bash
# Virtual environment oluştur
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Bağımlılıkları yükle
pip install -r requirements.txt

# Uygulamayı çalıştır
uvicorn main:app --reload --port 8000
```

API dokümantasyonu: `http://localhost:8000/docs`

### Veritabanı (PostGIS)

1. PostgreSQL ve PostGIS kurulu olmalı
2. Yeni bir veritabanı oluşturun:

```sql
CREATE DATABASE tarihi_yarimada_cbs;
\c tarihi_yarimada_cbs
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;
```

3. `.env` dosyası oluşturun:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/tarihi_yarimada_cbs
```

## 🎮 Kullanım

### Klavye Kısayolları

| Kısayol | İşlev |
|---------|-------|
| `Ctrl + 1` | Cesium görünümü |
| `Ctrl + 2` | Potree görünümü |
| `Ctrl + 3` | Split görünüm |
| `H` | Ana görünüme dön |
| `L` | Katmanlar paneli |
| `Esc` | Panelleri kapat |

### Viewer Kontrolleri

**Cesium (Dış Cephe):**
- Sol tık + sürükle: Döndür
- Sağ tık + sürükle: Yakınlaştır
- Orta tık + sürükle: Kaydır

**Potree (İç Mekan):**
- Sol tık + sürükle: Orbit
- Sağ tık + sürükle: Kaydır
- Scroll: Yakınlaştır/Uzaklaştır

## 📊 Veri Formatları

### 3D Tiles

```
data/3dtiles/molla-husrev/
├── tileset.json
├── tile_0_0_0.b3dm
├── tile_0_0_1.b3dm
└── ...
```

### Point Cloud (Potree)

```
data/pointcloud/molla-husrev/
├── metadata.json
├── octree.bin
└── hierarchy.bin
```

## 🔗 API Endpoints

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/v1/health` | Sağlık kontrolü |
| GET | `/api/v1/buildings` | Yapı listesi |
| GET | `/api/v1/buildings/{id}` | Yapı detayı |
| GET | `/api/v1/buildings/{id}/tileset` | 3D Tiles URL |
| GET | `/api/v1/buildings/{id}/pointcloud` | Point Cloud URL |
| GET | `/api/v1/layers` | Katman listesi |
| POST | `/api/v1/query/spatial` | Mekansal sorgu |
| POST | `/api/v1/measurements` | Ölçüm kaydet |
| POST | `/api/v1/annotations` | Anotasyon ekle |

## ⚙️ Cesium Ion Token

Cesium kullanmak için [Cesium Ion](https://cesium.com/ion/) hesabı oluşturup token almanız gerekiyor:

1. https://cesium.com/ion/ adresine gidin
2. Ücretsiz hesap oluşturun
3. Access Token alın
4. `js/cesiumViewer.js` dosyasında `YOUR_CESIUM_ION_TOKEN` yerine tokenınızı yazın

## 📋 Standartlar

Proje aşağıdaki standartlara uygun geliştirilmiştir:

- **INSPIRE** - Avrupa Mekansal Veri Altyapısı
- **TUCBS** - Türkiye Ulusal Coğrafi Bilgi Sistemi
- **ISO/TC 211** - Coğrafi Bilgi Standartları
- **CORINE** - Arazi Örtüsü Sınıflandırması

## 👥 Ekip

İTÜ CBS Projeleri 2024

## 📄 Lisans

Bu proje akademik amaçlı geliştirilmiştir.

