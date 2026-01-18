@echo off
REM Tarihi Yarımada CBS - Lokal Test Scripti
REM Bu script backend ve frontend'i lokal ortamda başlatır

echo ========================================
echo Tarihi Yarımada CBS - Lokal Test
echo ========================================
echo.

REM Proje dizinine git
cd /d "%~dp0"

REM .env dosyası kontrolü
if not exist .env (
    echo [UYARI] .env dosyasi bulunamadi!
    echo.
    echo Lutfen .env dosyasi olusturun:
    echo local_database_url=postgresql://username:password@localhost:5432/tarihi_yarimada_cbs
    echo DATABASE_URL=postgresql://username:password@localhost:5432/tarihi_yarimada_cbs
    echo CESIUM_TOKEN=your_cesium_ion_token_here
    echo ALLOWED_ORIGINS=*
    echo.
    pause
    exit /b 1
)

REM Python kontrolü
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi! Lutfen Python 3.11+ yukleyin.
    pause
    exit /b 1
)

REM Virtual environment kontrolü
if not exist venv (
    echo [BILGI] Virtual environment olusturuluyor...
    python -m venv venv
    if errorlevel 1 (
        echo [HATA] Virtual environment olusturulamadi!
        pause
        exit /b 1
    )
)

REM Virtual environment'ı aktifleştir
echo [BILGI] Virtual environment aktiflestiriliyor...
call venv\Scripts\activate.bat

REM Bağımlılıkları yükle
echo [BILGI] Bagimliliklari yukleniyor...
pip install -r backend\requirements.txt
if errorlevel 1 (
    echo [HATA] Bagimliliklar yuklenemedi!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Backend baslatiliyor...
echo ========================================
echo.
echo Backend: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Frontend icin yeni bir terminal penceresi acin ve:
echo   python -m http.server 8080
echo.
echo Sonra tarayicida: http://localhost:8080
echo.
echo [CTRL+C] ile durdurmak icin
echo.

REM Backend'i başlat (proje kök dizininden)
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

pause

