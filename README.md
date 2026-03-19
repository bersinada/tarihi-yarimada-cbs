# Tarihi Yarımada CBS Platformu

**İstanbul Tarihi Yarımada'daki kültürel miras yapılarının 3D modellerini, konumsal verilerini ve tarihi bilgilerini bir arada sunan, Neo4j + Gemini tabanlı GraphRAG destekli uzamsal olarak akıllı CBS platformu.**

<p align="center">
  <img src="assets/silhouette.png" alt="İstanbul Silüeti" width="600">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/PostgreSQL-PostGIS-336791?style=flat&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/CesiumJS-3D%20Maps-4DB6AC?style=flat" alt="CesiumJS">
  <img src="https://img.shields.io/badge/Neo4j-GraphRAG-008CC1?style=flat&logo=neo4j&logoColor=white" alt="Neo4j">
  <img src="https://img.shields.io/badge/Gemini%202.5%20Flash-4285F4?style=flat&logo=google&logoColor=white" alt="Gemini 2.5 Flash">
  <img src="https://img.shields.io/badge/OGC-WFS%202.0-green?style=flat" alt="OGC WFS">
</p>

---

## Ekran Görüntüleri

<p align="center">
  <img src="docs/screenshots/loading-page.png" alt="Tarihi Yarımada Web Sitesi Giriş" width="800">
  <br><em>Web site açılış ekranı</em>
</p>

<p align="center">
  <img src="docs/screenshots/01-overview.png" alt="Harita Genel Görünüm" width="800">
  <br><em>Harita genel görünümü</em>
</p>

<p align="center">
  <img src="docs/screenshots/02-model-detail.png" alt="3D Model Detay" width="800">
  <br><em>Sultanahmet Camii SAM3D modeli yakın görünüm</em>
</p>

<p align="center">
  <img src="docs/screenshots/03-chatbot.png" alt="Evliya AI Chatbot" width="800">
  <br><em>Evliya AI - Uzamsal zeka ile tarihi mekanları anlamlandıran soru-cevap arayüzü</em>
</p>

---

## Nedir ve Neden Yapıldı?

Bu proje İTÜ CBS Projeleri dersi kapsamında bir ekip çalışması olarak başladı; daha sonra bireysel bir projeye dönüştürülerek geliştirilmeye devam etti.

**Başlangıç noktası:** Tek bir yapının (Molla Hüsrev Camii) fotogrametrik yöntemlerle üretilmiş nokta bulutu verilerinden oluşan, statik bir 3D görselleştirme uygulamasıydı.

**Hedef:** İstanbul Tarihi Yarımada'daki kültürel miras yapılarını kapsayan; her yapının hem uzamsal hem semantik bağlamının farkında olduğu, standart uyumlu, işlevsel bir bilgi sistemi oluşturmak.

Projenin arkasındaki temel soru şuydu: *Tarihi bir yapıyı yalnızca görselle değil, onun tarihini, mimarisini ve komşularını "bilen" bir sistem olarak nasıl temsil ederiz?*

---

## Nasıl Çalışıyor?

```
┌─────────────────────────────────────────────────────────────┐
│                        KULLANICI                            │
│               Tarayıcı (CesiumJS)                 │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP / REST
┌──────────────────────▼──────────────────────────────────────┐
│                  BACKEND — FastAPI                           │
│   ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│   │  Eser API   │  │   OGC WFS    │  │   Chatbot Proxy  │  │
│   │  (CRUD)     │  │  (ISO 19115) │  │                  │  │
│   └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘  │
└──────────┼───────────────┼──────────────────┼──────────────┘
           │               │                  │
┌──────────▼───────┐       │         ┌────────▼─────────────┐
│  PostgreSQL      │       │         │  GraphRAG Servisi    │
│  + PostGIS       │       │         │  (ayrı proje)        │
│  Mekansal veri   │       │         │  Neo4j + Gemini API  │
│  Koordinatlar    │       │         │  Graf DB + LLM       │
│  Segment bilgisi │       │         │  port: 8002          │
└──────────────────┘       │         └──────────────────────┘
                           │
                    ┌──────▼──────┐
                    │ Cesium Ion  │
                    │ 3D Tiles    │
                    │ (SAM3D)     │
                    └─────────────┘
```

### Veri ve 3D Model Yaklaşımı

Nokta bulutu verilerinin elde edilmesinin güçlüğü ve bu boyuttaki verileri taşıyabilecek altyapı kısıtları projenin en büyük teknik engeliydi. **İki seçenek vardı:**

| Yaklaşım | Doğruluk | Veri Boyutu | Ölçeklenebilirlik |
|----------|----------|-------------|-------------------|
| Fotogrametri (nokta bulutu) | Yüksek | 500 MB+ / yapı | Düşük |
| META SAM3D (segmentasyon) | Orta | **1–2 MB / yapı** | Yüksek |

13 yapı için nokta bulutu verisi toplamak hem pratik hem de altyapı açısından mümkün değildi. META'nın **SAM3D** (Segment Anything in 3D) modeli, fotogrametrik doğruluk sunmasa da bu ölçekte temsili ve yüklenebilir 3D modeller üretmenin en makul yoluydu.

### GraphRAG ve Uzamsal Zeka

Salt görsel bir platform yapmak yetmezdi. Her yapının kendisini ve komşularını "bilmesi" için **Neo4j** graf veritabanı üzerine inşa edilmiş bir **GraphRAG** sistemi geliştirildi; LLM olarak **Gemini 2.5 Flash** kullanıldı. Kullanıcılar **Evliya AI** chatbot üzerinden şu tür sorular sorabilir:

- *"Ayasofya ile Sultanahmet Camii arasındaki ilişki nedir?"*
- *"Bu meydandaki Bizans dönemi eserleri hangileri?"*
- *"Dikilitaş'ın hikayesi ne?"*

GraphRAG servisi bu repodan bağımsız ayrı bir projede çalışmaktadır.

---

## Özellikler

| Özellik | Açıklama |
|---------|----------|
| **3D Görselleştirme** | CesiumJS ile SAM3D tabanlı 3D Tiles modelleri (1–2 MB/yapı) |
| **Katman Yönetimi** | Her yapı katmanını bağımsız açıp kapama |
| **Kamera Modları** | Orbit, First Person, Walking kamera kontrolleri |
| **Evliya AI Chatbot** | GraphRAG tabanlı uzamsal-semantik doğal dil soru-cevap |
| **Not Sistemi** | Yapılar üzerine kullanıcı notları ekleme |
| **OGC WFS 2.0** | Standart uyumlu Web Feature Service endpoint'i |
| **ISO 19115 Metadata** | Avrupa ve Türkiye standartlarına uygun veri modeli |
| **PostGIS** | Mekansal sorgular için PostgreSQL + PostGIS entegrasyonu |

---

## Sistemdeki Yapılar

Platform bir **MVP** olarak tasarlandı; pilot bölge **Sultanahmet Meydanı** ve çevresi. Şu anda **13 eserin** 3D modeli ve tarihi bilgisi sistemde yer alıyor.

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

---

## Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| Frontend | HTML5, CSS3, JavaScript, CesiumJS |
| Backend | FastAPI |
| Veritabanı | PostgreSQL + PostGIS |
| 3D Modelleme | META SAM3D |
| AI / RAG | Neo4j (Graf DB) + Gemini 2.5 Flash |
| Standartlar | INSPIRE, TUCBS, ISO 19115, Dublin Core, OGC WFS 2.0 |

---

## Kurulum

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

> **Chatbot:** Evliya AI'nin çalışması için GraphRAG servisinin `http://localhost:8002` adresinde aktif olması gerekir.

---

## API

API dokümantasyonu `http://localhost:8000/docs` (Swagger UI) adresinde otomatik olarak üretilmektedir.

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

---

## Proje Yapısı

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
├── docs/
│   └── screenshots/              # README görselleri
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
│   └── requirements.txt
├── start-local-test.bat          # Windows backend başlatma
└── start-frontend.bat            # Windows frontend başlatma
```

---

## Standartlar

Bu platform, hem Avrupa hem de Türkiye ulusal CBS standartlarıyla uyumlu tasarlanmıştır:

- **INSPIRE** — Avrupa Mekansal Veri Altyapısı direktifi
- **TUCBS** — Türkiye Ulusal Coğrafi Bilgi Sistemi standartları
- **ISO 19115** — Coğrafi metadata standardı
- **Dublin Core** — Metadata standardı
- **OGC WFS 2.0** — Web Feature Service

---

Bireysel proje — İTÜ CBS Projeleri, 2025
Akademik amaçlı geliştirilmiştir.
