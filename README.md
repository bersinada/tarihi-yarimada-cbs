# 🏛️ Tarihi Yarımada CBS Platformu

İstanbul Tarihi Yarımada'daki kültürel miras yapılarının 3D modellerini ve uzamsal verilerini sunan, GraphRAG destekli interaktif CBS (Coğrafi Bilgi Sistemi) platformu.

<p align="center">
  <img src="assets/silhouette.png" alt="İstanbul Silüeti" width="600">
</p>

## 📋 Proje Hakkında

Proje, İTÜ CBS Projeleri dersi kapsamında ekip çalışması olarak başlatılmış; ardından bireysel bir projeye dönüştürülerek geliştirilmeye devam etmiştir.

**Başlangıçta** tek bir yapının (Molla Hüsrev Camii) fotogrametrik yöntemlerle elde edilmiş nokta bulutu verilerinden oluşan bir 3D görselleştirme platformuydu. **Bireysel projeye dönüşümüyle birlikte** hedef, Tarihi Yarımada'daki kültürel miras yapılarını kapsayan, her yapının kendi uzamsal ve semantik bağlamının farkında olduğu işlevsel bir bilgi sistemine ulaşmaktı.

### Veri ve 3D Model Yaklaşımı

Nokta bulutu verilerinin elde edilmesinin güçlüğü ve bu boyuttaki verileri taşıyabilecek altyapı kısıtları, projenin en büyük teknik engelleriydi. Bu sorunu çözmek için META'nın **SAM3D** (Segment Anything in 3D) segmentasyon modeli tercih edildi. SAM3D, fotogrametri gibi yüksek doğruluk sağlamamakla birlikte —ki özünde bir segmentasyon modelidir— yapıların temsili 3D modellerini **1–2 MB** gibi son derece küçük veri boyutlarıyla üretebilmektedir. Sonuçlar, bu boyutlar göz önüne alındığında oldukça yeterlidir.

### GraphRAG Entegrasyonu

Modellerin yalnızca görsel değil, **uzamsal olarak da akıllı** olması amacıyla projeye Microsoft GraphRAG entegre edildi. Graf veritabanı olarak **Neo4j** kullanılmaktadır. GraphRAG servisi bu repodan bağımsız ayrı bir projede yer almakta olup `http://localhost:8002` adresinde çalışır. Siteye eklenen **Evliya AI** chatbot sayesinde kullanıcılar; yapılar hakkındaki tarihsel, mimari ve uzamsal bilgilere doğal dil arayüzüyle erişebiliyor. Artık her tarihi yapı, kendisinin ve yakın çevresinin farkında bir varlık olarak platformda yer almaktadır.

### Pilot Bölge

Platform bir **MVP** olarak tasarlandı; pilot bölge olarak **Sultanahmet Meydanı** ve çevresi seçildi. Şu anda **13 eserin** 3D modeli ve tarihi bilgisi sistemde yer almakta olup, bu eserlerden bir kısmı henüz GraphRAG'e entegre edilmemiştir. Meydan dışındaki bazı yapılar da modelleri ve bilgileriyle platformda bulunmaktadır.

### Eserler

| # | Eser | Tür | Dönem | Yapım Yılı | GraphRAG |
|---|------|-----|-------|------------|----------|
| 1 | Ayasofya | Cami / Müze | Bizans | 537 | ✅ |
| 2 | Sultanahmet Camii | Cami | Osmanlı | 1609–1616 | ✅ |
| 3 | Firuzağa Camii | Cami | Osmanlı | 1491 | ✅ |
| 4 | Süleymaniye Camii | Cami | Osmanlı | 1550–1557 | ⏳ |
| 5 | Kariye Camii | Kilise / Müze | Bizans | 534 | ⏳ |
| 6 | Aya İrini | Kilise | Bizans | 324–548 | ✅ |
| 7 | I. Ahmet Türbesi | Türbe | Osmanlı | 1617–1619 | ✅ |
| 8 | Dikilitaş | Anıt | Antik | M.Ö. 1450 | ✅ |
| 9 | Örme Dikilitaş | Anıt | Bizans | 4. yy | ✅ |
| 10 | Yılanlı Sütun | Anıt | Antik | M.Ö. 479 | ✅ |
| 11 | Alman Çeşmesi | Çeşme | Geç Osmanlı | 1898–1901 | ✅ |
| 12 | III. Ahmet Çeşmesi | Çeşme | Osmanlı | 1728 | ✅ |
| 13 | Molla Hüsrev Camii | Cami | Osmanlı | 1455 | ⏳ |

### Özellikler

- **3D Görselleştirme** — Cesium JS ile SAM3D tabanlı 3D Tiles modelleri (1–2 MB/yapı)
- **Katman Yönetimi** — Yapı katmanlarını bağımsız açıp kapama
- **Kamera Modları** — Orbit, First Person, Walking modları
- **Evliya AI Chatbot** — GraphRAG tabanlı uzamsal-semantik soru-cevap
- **Not Sistemi** — Yapılar üzerine kullanıcı notları
- **INSPIRE / TUCBS Uyumlu** — Avrupa ve Türkiye standartlarına uygun veri modeli
- **PostGIS Entegrasyonu** — Mekansal sorgular için PostgreSQL + PostGIS

## 🛠️ Teknolojiler

| Katman | Teknoloji |
|--------|-----------|
| Frontend | HTML5, CSS3, JavaScript, Cesium JS, Leaflet |
| Backend | FastAPI (Python 3.11+) |
| Veritabanı | PostgreSQL + PostGIS |
| 3D Modelleme | META SAM3D (Segment Anything in 3D) |
| AI / RAG | Microsoft GraphRAG + Neo4j |
| Standartlar | INSPIRE, TUCBS, ISO 19115, Dublin Core, OGC WFS 2.0 |

## 🚀 Kurulum

### Gereksinimler

- Python 3.11+
- PostgreSQL + PostGIS
- [Cesium Ion](https://ion.cesium.com/) Access Token
- GraphRAG servisi (chatbot için, port 8002)

### 1. Veritabanı Oluşturun

```sql
CREATE DATABASE tarihi_yarimada_cbs;
\c tarihi_yarimada_cbs
CREATE EXTENSION postgis;
```

### 2. Ortam Değişkenlerini Ayarlayın

Proje kök dizininde `.env` dosyası oluşturun:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/tarihi_yarimada_cbs
CESIUM_TOKEN=your_cesium_ion_token_here
ALLOWED_ORIGINS=*
```

### 3. Backend'i Başlatın

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

### 4. Frontend'i Başlatın (yeni terminal)

```bash
python -m http.server 8080
```

### 5. Tarayıcıda Açın

```
http://localhost:8080
```

> **Windows için kısayol:** `start-local-test.bat` (backend) ve `start-frontend.bat` (frontend) dosyalarını kullanabilirsiniz.

> **Chatbot:** Evliya AI chatbot'un çalışması için GraphRAG servisinin `http://localhost:8002` adresinde çalışıyor olması gerekir.

## 📁 Proje Yapısı

```
tarihi-yarimada-cbs/
├── index.html                    # Ana sayfa
├── css/
│   └── styles.css                # Osmanlı-Bizans temalı stiller
├── js/
│   ├── main.js                   # Ana uygulama mantığı
│   ├── api.js                    # Backend API iletişimi
│   ├── assets.js                 # Eser verileri ve yönetimi
│   ├── cesiumViewer.js           # Cesium 3D viewer ve kamera kontrolleri
│   └── chatbot-widget.js         # Evliya AI chatbot widget
├── assets/                       # Logo ve görseller
├── images/assets/                # Eser fotoğrafları
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI uygulaması
│   │   ├── config.py             # Ortam değişkenleri
│   │   ├── api/                  # API endpoint'leri
│   │   │   ├── assets.py         # Eser CRUD
│   │   │   ├── segments.py       # SAM3D segmentleri
│   │   │   ├── notes.py          # Not sistemi
│   │   │   └── ogc.py            # OGC WFS endpoint'leri
│   │   ├── db/                   # Veritabanı katmanı
│   │   │   ├── database.py       # PostgreSQL bağlantısı
│   │   │   └── models.py         # SQLAlchemy modelleri
│   │   └── schemas/              # Pydantic şemaları
│   ├── scripts/
│   │   └── seed_data.py          # Örnek veri yükleme
│   └── requirements.txt          # Python bağımlılıkları
├── start-local-test.bat          # Windows backend başlatma
└── start-frontend.bat            # Windows frontend başlatma
```

## 🔗 API

API dokümantasyonuna `http://localhost:8000/docs` (Swagger UI) veya `http://localhost:8000/redoc` adresinden erişebilirsiniz.

### Başlıca Endpoint'ler

| Metot | Endpoint | Açıklama |
|-------|----------|----------|
| `GET` | `/api/v1/health` | Sistem sağlık kontrolü |
| `GET` | `/api/cesium-config` | Cesium token |
| `GET` | `/api/v1/assets` | Tüm eserleri listele |
| `GET` | `/api/v1/assets/{id}` | Eser detayı |
| `POST` | `/api/v1/assets` | Yeni eser ekle |
| `GET` | `/api/v1/search?q=` | Eser arama |
| `GET` | `/api/v1/metadata` | Dataset metadata (ISO 19115) |
| `GET` | `/api/v1/ogc/wfs` | OGC WFS endpoint |

## 📋 Standartlar

- **INSPIRE** — Avrupa Mekansal Veri Altyapısı
- **TUCBS** — Türkiye Ulusal Coğrafi Bilgi Sistemi
- **ISO 19115** — Coğrafi metadata standardı
- **Dublin Core** — Metadata standardı
- **OGC WFS 2.0** — Web Feature Service

## � Geliştirici

Bireysel proje — İTÜ CBS Projeleri, 2025

## 📄 Lisans

Bu proje akademik amaçlı geliştirilmiştir.
