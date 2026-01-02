# 🧪 Lokal Test Rehberi

Bu rehber, Tarihi Yarımada CBS platformunu lokal ortamda test etmek için gerekli adımları içerir.

## 📋 Ön Gereksinimler

1. **Python 3.11+** kurulu olmalı
2. **PostgreSQL + PostGIS** kurulu ve çalışıyor olmalı
3. **Cesium Ion Access Token** (ücretsiz hesap oluşturabilirsiniz)

## 🚀 Hızlı Başlangıç

### 1. Veritabanı Hazırlığı

PostgreSQL'de veritabanı oluşturun:

```sql
-- PostgreSQL'de çalıştırın
CREATE DATABASE tarihi_yarimada_cbs;
\c tarihi_yarimada_cbs
CREATE EXTENSION postgis;
```

### 2. Environment Variables (.env)

Proje kök dizininde `.env` dosyası oluşturun:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/tarihi_yarimada_cbs
CESIUM_TOKEN=your_cesium_ion_token_here
ALLOWED_ORIGINS=*
```

**Not:** `your_cesium_ion_token_here` yerine gerçek Cesium Ion token'ınızı yazın.

### 3. Backend'i Başlatma

#### Windows:
```cmd
start-local-test.bat
```

#### Manuel (Windows):
```cmd
cd tarihi-yarimada-cbs
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

#### Linux/macOS:
```bash
cd tarihi-yarimada-cbs
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend başarıyla çalışıyorsa:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

### 4. Frontend'i Başlatma

Yeni bir terminal penceresi açın:

#### Windows:
```cmd
start-frontend.bat
```

#### Manuel:
```cmd
cd tarihi-yarimada-cbs
python -m http.server 8080
```

Frontend başarıyla çalışıyorsa:
- Web Uygulaması: http://localhost:8080

## ✅ Test Kontrol Listesi

### Backend Testleri

1. **Health Check:**
   ```
   http://localhost:8000/api/v1/health
   ```
   Beklenen: `{"status":"healthy","database":"connected","version":"1.0.0"}`

2. **Cesium Config:**
   ```
   http://localhost:8000/api/cesium-config
   ```
   Beklenen: `{"accessToken":"...","ionAssetEndpoint":"https://api.cesium.com/"}`

3. **Yapılar Listesi:**
   ```
   http://localhost:8000/api/v1/yapilar
   ```
   Beklenen: JSON array with building data

4. **Katmanlar:**
   ```
   http://localhost:8000/api/v1/katmanlar
   ```
   Beklenen: JSON array with layer data

### Frontend Testleri

1. **Sayfa Yükleniyor mu?**
   - http://localhost:8080 adresine gidin
   - Loading ekranı görünmeli, sonra ana sayfa açılmalı

2. **Cesium Viewer Çalışıyor mu?**
   - 3D model yüklenmeli (Molla Hüsrev Camii dış cephe)
   - Kamera hareket edebilmeli

3. **Katmanlar Paneli:**
   - Sağ üstteki katmanlar butonuna tıklayın
   - Sadece "Dış Cephe" checkbox'ı işaretli olmalı ✅
   - Diğer katmanlar (İç Mekan 1, İç Mekan 2, Şadırvan) işaretsiz olmalı ☐

4. **Katman Toggle:**
   - İç Mekan 1 checkbox'ını işaretleyin
   - İç mekan modeli görünür olmalı
   - Tekrar kaldırın, gizlenmeli

5. **API Bağlantısı:**
   - Sol alttaki status bar'da "API Bağlantısı" yeşil nokta ile gösterilmeli

## 🐛 Sorun Giderme

### Backend Başlamıyor

**Hata:** `ModuleNotFoundError: No module named 'backend'`
- **Çözüm:** Proje kök dizininden çalıştırdığınızdan emin olun (backend klasörü içinden değil)

**Hata:** `DATABASE_URL ortam değişkeni bulunamadı`
- **Çözüm:** `.env` dosyasının proje kök dizininde olduğundan ve `DATABASE_URL` değerinin doğru olduğundan emin olun

**Hata:** `could not connect to server`
- **Çözüm:** PostgreSQL servisinin çalıştığından ve veritabanının oluşturulduğundan emin olun

### Frontend Cesium Yüklenmiyor

**Hata:** `Cesium token yüklenirken hata`
- **Çözüm:** `.env` dosyasında `CESIUM_TOKEN` değerinin doğru olduğundan emin olun

**Hata:** `CORS error`
- **Çözüm:** Backend'in çalıştığından ve CORS ayarlarının doğru olduğundan emin olun

### Katmanlar Görünmüyor

**Sorun:** Tüm katmanlar kapalı görünüyor
- **Kontrol:** Browser console'u açın (F12) ve hata mesajlarını kontrol edin
- **Kontrol:** Network tab'ında API isteklerinin başarılı olduğunu kontrol edin

## 📝 Notlar

- Backend ve Frontend ayrı terminal pencerelerinde çalışmalı
- Backend portu: **8000**
- Frontend portu: **8080**
- Veritabanı ilk çalıştırmada otomatik olarak tabloları oluşturur ve örnek veri ekler

## 🎯 Test Senaryoları

### Senaryo 1: Başlangıç Durumu
1. Sayfayı açın
2. Sadece dış cephe katmanı görünür olmalı
3. Diğer katmanlar kapalı olmalı

### Senaryo 2: Katman Açma/Kapama
1. Katmanlar panelini açın
2. İç Mekan 1'i açın → Görünür olmalı
3. İç Mekan 1'i kapatın → Gizlenmeli
4. Şadırvan'ı açın → Görünür olmalı

### Senaryo 3: Çoklu Katman
1. Tüm katmanları açın
2. Hepsi görünür olmalı
3. Sadece dış cepheyi açık bırakın
4. Diğerleri gizlenmeli

## 🔗 Faydalı Linkler

- **Cesium Ion:** https://cesium.com/ion/
- **FastAPI Docs:** http://localhost:8000/docs
- **PostGIS Docs:** https://postgis.net/documentation/

