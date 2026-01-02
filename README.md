# 🏛️ Tarihi Yarımada CBS Platformu

İstanbul Tarihi Yarımada'daki kültürel miras yapılarının 3D modellerini ve nokta bulutu verilerini web ortamında sunan CBS platformu.

🌐 **Canlı Site:** [tarihiyarimadacbs.app](https://tarihiyarimadacbs.app)

## 📋 Proje Hakkında

Bu proje, İTÜ CBS Projeleri dersi kapsamında geliştirilmiştir. Tarihi Yarımada'daki kültürel miras yapılarının (Molla Hüsrev Camii) 3D modellerini ve point cloud verilerini interaktif bir web arayüzünde sunmayı amaçlamaktadır.

### 🎯 Özellikler

- **Cesium JS** ile 3D Tiles görselleştirme (dış cephe ve iç mekan)
- **Katman Yönetimi** - Dış cephe, iç mekan ve şadırvan katmanlarını kontrol edin
- **Anotasyon Sistemi** - 3D modeller üzerinde not ekleme
- **INSPIRE/TUCBS Uyumlu** - Standartlara uygun veri yapısı
- **PostGIS Entegrasyonu** - Mekansal veritabanı desteği

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
├── index.html              # Ana HTML sayfası
├── css/                    # Stil dosyaları
├── js/                     # JavaScript modülleri
│   ├── main.js            # Ana uygulama
│   ├── api.js             # API modülü
│   └── cesiumViewer.js    # Cesium viewer
├── backend/                # FastAPI backend
│   ├── main.py            # API endpoints
│   ├── database.py        # Veritabanı modelleri
│   └── migrations/        # Veritabanı migration'ları
├── requirements.txt        # Python bağımlılıkları
└── start-local-test.bat   # Lokal test scripti
```

## 🔗 API Endpoints

- `GET /api/v1/health` - Sağlık kontrolü
- `GET /api/v1/yapilar` - Yapı listesi
- `GET /api/v1/yapilar/{id}` - Yapı detayı
- `GET /api/v1/katmanlar` - Katman listesi
- `GET /api/cesium-config` - Cesium token yapılandırması

API dokümantasyonu: http://localhost:8000/docs

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
