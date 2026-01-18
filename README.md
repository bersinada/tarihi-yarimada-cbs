# 🏛️ Tarihi Yarımada CBS Platformu

İstanbul Tarihi Yarımada'daki kültürel miras yapılarının 3D modellerini ve nokta bulutu verilerini web ortamında sunan interaktif CBS platformu.

🌐 **Canlı Site:** [tarihiyarimadacbs.app](https://tarihiyarimadacbs.app)

## 📋 Proje Hakkında

Bu proje, İTÜ CBS Projeleri dersi kapsamında geliştirilmiştir. Tarihi Yarımada'daki kültürel miras yapılarının (Molla Hüsrev Camii, Sultanahmet Camii) 3D modellerini ve point cloud verilerini interaktif bir web arayüzünde sunmayı amaçlamaktadır.

### 🎯 Özellikler

- **3D Görselleştirme** - Cesium JS ile 3D Tiles ve mesh modelleri (dış cephe, iç mekan, detaylar)
- **Katman Yönetimi** - Yapı katmanlarını (dış cephe, iç mekan, şadırvan, vb.) ayrı ayrı kontrol
- **İnteraktif Kamera Modları** - Orbit, First Person, Walking modları ile yapıyı keşfedin
- **Anotasyon Sistemi** - 3D modeller üzerinde not ekleme ve paylaşma
- **INSPIRE/TUCBS Uyumlu** - Avrupa ve Türkiye standartlarına uygun veri yapısı
- **PostGIS Entegrasyonu** - PostgreSQL + PostGIS ile mekansal veritabanı desteği
- **Modern UI/UX** - Responsive tasarım, dark tema, premium görünüm

## 🛠️ Teknolojiler

- **Frontend:** HTML5, CSS3, JavaScript, Cesium JS
- **Backend:** FastAPI (Python)
- **Veritabanı:** PostgreSQL + PostGIS
- **Standartlar:** INSPIRE, TUCBS, ISO 19115, CORINE

## 🚀 Lokal Kurulum

### Ön Gereksinimler

- Python 3.11+
- PostgreSQL + PostGIS
- Cesium Ion Access Token

### Hızlı Başlangıç

1. **Veritabanı oluşturun:**
```sql
CREATE DATABASE tarihi_yarimada_cbs;
\c tarihi_yarimada_cbs
CREATE EXTENSION postgis;
```

2. **`.env` dosyası oluşturun:**
```env
DATABASE_URL=postgresql://username:password@localhost:5432/tarihi_yarimada_cbs
CESIUM_TOKEN=your_cesium_ion_token_here
ALLOWED_ORIGINS=*
```

3. **Backend'i başlatın:**
```bash
# Windows
start-local-test.bat

# veya manuel
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

4. **Frontend'i başlatın (yeni terminal):**
```bash
# Windows
start-frontend.bat

# veya manuel
python -m http.server 8080
```

5. **Tarayıcıda açın:** http://localhost:8080

Detaylı kurulum için `TEST_REHBERI.md` dosyasına bakın.

## 📁 Proje Yapısı

```
tarihi-yarimada-cbs/
├── index.html                  # Ana HTML sayfası
├── css/
│   └── styles.css             # Modern UI stilleri (dark tema, animasyonlar)
├── js/
│   ├── main.js                # Ana uygulama mantığı
│   ├── api.js                 # Backend API modülü
│   ├── assets.js              # Varlık yönetimi
│   └── cesiumViewer.js        # Cesium 3D viewer & kamera kontrolleri
├── assets/
│   ├── logo.png               # Platform logosu
│   └── silhouette.png         # İstanbul silüeti
├── backend/
│   ├── app/
│   │   ├── api/               # API endpoints (Clean Architecture)
│   │   │   ├── assets.py
│   │   │   ├── categories.py
│   │   │   └── layers.py
│   │   ├── db/                # Veritabanı katmanı
│   │   │   ├── database.py    # PostgreSQL bağlantısı
│   │   │   └── models.py      # SQLAlchemy modelleri
│   │   └── schemas/           # Pydantic şemaları
│   ├── init_db.py             # Veritabanı başlatma
│   ├── scripts/
│   │   └── seed_data.py       # Örnek veri ekleme
│   └── main.py                # FastAPI uygulaması
├── requirements.txt           # Python bağımlılıkları
├── start-local-test.bat       # Backend başlatma (Windows)
└── start-frontend.bat         # Frontend başlatma (Windows)
```

## 🔗 API Endpoints

### Sağlık & Yapılandırma
- `GET /api/v1/health` - Sistem sağlık kontrolü
- `GET /api/cesium-config` - Cesium token yapılandırması

### Varlıklar (Assets)
- `GET /api/v1/assets` - Tüm varlıkları listele (filtreler: category, layer)
- `GET /api/v1/assets/{id}` - Varlık detayı
- `POST /api/v1/assets` - Yeni varlık ekle
- `PUT /api/v1/assets/{id}` - Varlık güncelle
- `DELETE /api/v1/assets/{id}` - Varlık sil

### Kategoriler
- `GET /api/v1/categories` - Kategori listesi

### Katmanlar
- `GET /api/v1/layers` - Katman listesi

### İnteraktif API Dokümantasyonu
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📋 Standartlar

Proje aşağıdaki standartlara uygun geliştirilmiştir:

- **INSPIRE** - Avrupa Mekansal Veri Altyapısı
- **TUCBS** - Türkiye Ulusal Coğrafi Bilgi Sistemi
- **ISO 19115/19139** - Metadata standartları
- **CORINE** - Arazi Örtüsü Sınıflandırması

## 👥 Ekip

İTÜ CBS Projeleri 2025

## 📄 Lisans

Bu proje akademik amaçlı geliştirilmiştir.
