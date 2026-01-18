# 🚀 Tarihi Yarımada CBS - Başlangıç Rehberi

## 📋 İçerik

- [Yenilikler](#-yenilikler)
- [Kurulum](#-kurulum)
- [Kullanım](#-kullanım)
- [Özellikler](#-özellikler)
- [Sorun Giderme](#-sorun-giderme)

---

## ✨ Yenilikler

### Proje Dönüşümü
Bu proje, **okul ödevi** seviyesinden **kişisel/sunula hazır uygulama** seviyesine yükseltilmiştir.

**Eski Durumu:**
- Tek eser (Molla Hüsrev Camii)
- Basit navigasyon
- Sınırlı tasarım

**Yeni Durumu:**
- 5 eser (Ayasofya, Küçük Ayasofya, Süleymaniye, Sultanahmet, Topkapı)
- Profesyonel Osmanlı-Bizans teması
- Çoklu dil desteğine hazır yapı
- Production-ready kod

### Başlıca Geliştirmeler

#### 1️⃣ **Tasarım**
```
Osmanlı Teması
├── Altın aksan renkler (#c9a227)
├── Koyu arka plan (#0a1214)
├── Serif/Sans-serif font kombinasyonu
└── Cami silüeti header dekorasyonu
```

#### 2️⃣ **Navigasyon**
```
Eserler Menüsü
├── Bizans Dönemi
│   ├── Ayasofya (537)
│   └── Küçük Ayasofya (536)
└── Osmanlı Dönemi
    ├── Süleymaniye Camii (1557)
    ├── Sultanahmet Camii (1616)
    └── Topkapı Sarayı (1478)
```

#### 3️⃣ **Bilgi Paneli**
Sağ tarafta açılan panel:
- 📊 Yapı detayları (yıl, banisi, konum)
- 🎨 3D model katmanları kontrol
- 📝 Kullanıcı notları sistemi
- 🔄 Otomatik veri yükleme

#### 4️⃣ **Hakkında Sayfası**
Full-screen modal:
- 🗺️ 2D Leaflet haritası
- 📜 Tarihi bilgiler
- 📈 İstatistikler
- 🎨 Bizans-Osmanlı renklendirilmesi

---

## 🛠️ Kurulum

### Gereksinimler
- Python 3.11+
- PostgreSQL + PostGIS (backend için)
- Cesium Ion Token (3D modeller için)
- Modern Web Tarayıcı (Chrome, Firefox, Edge)

### 1. Veritabanı Hazırlanması
```bash
# PostgreSQL'de çalıştırın
CREATE DATABASE tarihi_yarimada_cbs;
\c tarihi_yarimada_cbs
CREATE EXTENSION postgis;
```

### 2. .env Dosyası
Proje kök dizininde `.env` oluşturun:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/tarihi_yarimada_cbs
CESIUM_TOKEN=your_cesium_ion_token_here
ALLOWED_ORIGINS=*
```

### 3. Backend Başlatma
```bash
# Windows
start-local-test.bat

# veya manual
python -m venv venv
venv\Scripts\activate
pip install -r backend\requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

### 4. Frontend Başlatma (Yeni Terminal)
```bash
# Windows
start-frontend.bat

# veya manual
python -m http.server 8080
```

### 5. Tarayıcıda Açma
```
http://localhost:8080
```

---

## 📖 Kullanım

### 🏛️ Eser Seçme

1. **Menu'de "Eserler" öğesine tıklayın**
   ```
   Eserler ▼
   ├── Bizans Dönemi
   │   ├── Ayasofya
   │   └── Küçük Ayasofya
   └── Osmanlı Dönemi
       ├── Süleymaniye Camii
       ├── Sultanahmet Camii
       └── Topkapı Sarayı
   ```

2. **Bir eseri seçin**
   - Dropdown menüsünden eseri tıklayın
   - Otomatik olarak sağ panelde bilgiler açılır
   - 3D model yüklenir ve kamera zoom'lanır

3. **Detayları İnceleyin**
   - **Yapı Bilgileri**: Sağ panelde temel bilgiler
   - **3D Modeller**: Katmanları aç/kapa
   - **Notlar**: Alt kısımda açıklamalar yazın

### ℹ️ Hakkında Sayfası

1. **"Hakkında" butonuna tıklayın**
   - Full-screen modal açılır
   - Sol: 2D Leaflet harita
   - Sağ: Tarihi bilgiler

2. **2D Haritayı Keşfedin**
   - Mavi noktalar: Bizans dönem eserleri
   - Turuncu noktalar: Osmanlı dönem eserleri
   - Tüm eserlerin konumları gösterilir

3. **Bilgileri Okuyun**
   - Tarihi Yarımada'nın 2500+ yıllık tarihi
   - Bizans ve Osmanlı dönemleri
   - UNESCO Dünya Mirası bilgisi

### 🏠 Ana Görünüme Dönüş

- **Home butonu** (🏠) - Tüm yarımadayı göster
- **Escape tuşu** - Panel'i kapat
- **Başka eser seçme** - Otomatik olarak değişir

### 📝 Not Ekleme

1. Sağ panelin alt kısmındaki formu doldurun
2. **Not Başlığı**: Kısa başlık (100 karakter max)
3. **Not İçeriği**: Detaylı açıklama (500 karakter max)
4. **İsim (İsteğe Bağlı)**: Yazarın adı
5. **Notu Kaydet** butonuna tıklayın

Notlar sunucu üzerinde saklanır.

---

## 🎨 Özellikler

### Teknik Özellikler

| Özellik | Teknoloji | Detay |
|---------|-----------|-------|
| 3D Viewer | Cesium JS | 3D Tiles ve interior navigation |
| 2D Harita | Leaflet | OpenStreetMap tiles |
| Stil | CSS | Osmanlı teması custom CSS |
| Veritabanı | PostGIS | Mekansal veri yönetimi |
| Backend | FastAPI | RESTful API |
| Frontend | Vanilla JS | Modüler yapı (assets.js, api.js, main.js) |

### Kullanıcı Özellikleri

✅ **Eser Gezintisi**
- Menü tabanlı eser seçimi
- Dinamik bilgi paneli
- Smooth kamera transitions

✅ **3D Model Kontrol**
- Çoklu katman desteği
- Bağımsız görünürlük kontrolü
- Interior modelleri

✅ **Not Sistemi**
- Eser-spesifik notlar
- Yazar bilgisi
- Tarih kaydı

✅ **Harita Entegrasyonu**
- 2D Leaflet haritası
- Eser konumları işaretleme
- Dönem-bazlı renklendirilme

✅ **Responsive Tasarım**
- Mobil uyumlu
- Tablet optimizasyonu
- Masaüstü full experience

---

## 🐛 Sorun Giderme

### ❌ "API Bağlantısı Başarısız"

**Sorun**: Sağ tarafta status çubuk kırmızı gösteriyor

**Çözüm**:
1. Backend'in çalıştığını kontrol edin
   ```bash
   http://localhost:8000/api/v1/health
   ```
2. `.env` dosyasının doğru olduğunu kontrol edin
3. CORS ayarlarını kontrol edin

### ❌ "3D Model Yüklenmiyor"

**Sorun**: Cesium viewer siyah kalıyor

**Çözüm**:
1. Cesium Token'ınızı kontrol edin
2. İnternet bağlantısını kontrol edin
3. Tarayıcı konsolunda hataları kontrol edin (F12)

### ❌ "Notlar Kaydedilmiyor"

**Sorun**: Not kaydetme butonu çalışmıyor

**Çözüm**:
1. Başlık ve içeriği doldurmaya dikkat edin
2. Backend'in çalıştığını kontrol edin
3. Veritabanı bağlantısını kontrol edin

### ❌ "Harita Gösterilmiyor"

**Sorun**: About sayfasında 2D harita boş

**Çözüm**:
1. Leaflet kütüphanesinin yüklendiğini kontrol edin (F12 → Network)
2. İnternet bağlantısını kontrol edin
3. CDN erişim sorununu kontrol edin

---

## 📁 Önemli Dosyalar

```
📦 Proje
├── 📄 index.html              ← HTML yapısı
├── 📄 css/styles.css          ← Tüm stiller
├── 📄 js/
│   ├── 📄 assets.js           ← Eser verileri (YENİ)
│   ├── 📄 api.js              ← API bağlantısı
│   ├── 📄 cesiumViewer.js     ← 3D viewer kontrolü
│   └── 📄 main.js             ← Ana mantık (GÜNCELLENDİ)
├── 📄 FRONTEND_UPDATES.md     ← Detaylı güncelleme dökü (YENİ)
├── 📄 CHANGELOG.md            ← Değişiklik geçmişi (YENİ)
└── 📄 BAŞLANGIÇ_REHBERİ.md    ← Bu dosya (YENİ)
```

---

## 🔗 Faydalı Linkler

- 📍 **Cesium Ion**: https://cesium.com/ion/tokens
- 🗺️ **Leaflet Docs**: https://leafletjs.com/
- 🏗️ **FastAPI Docs**: http://localhost:8000/docs
- 🐘 **PostgreSQL**: https://www.postgresql.org/
- 🌍 **OpenStreetMap**: https://www.openstreetmap.org/

---

## 📞 Destek

Sorun yaşarsanız:

1. **Browser Console'u Açın** (F12)
2. **Error Mesajını Okuyun**
3. **Sorun Giderme** bölümünü kontrol edin
4. **Backend Logs'unu Kontrol Edin**

---

## 🎯 Sonraki Adımlar (İsteğe Bağlı)

- [ ] Daha fazla eser ekleme
- [ ] Foto galerisi entegrasyonu
- [ ] Arama/filtreleme özelliği
- [ ] Eser karşılaştırması
- [ ] Mobil uygulama
- [ ] Çok dilli destek

---

**Son Güncelleme**: 17 Ocak 2025
**Versiyon**: 2.0 - Yeniden Tasarım

Keyifli kullanımlar! 🏛️✨



