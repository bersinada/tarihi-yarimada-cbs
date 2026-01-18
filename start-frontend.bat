@echo off
REM Tarihi Yarımada CBS - Frontend HTTP Sunucusu
REM Bu script frontend'i basit bir HTTP sunucusu ile başlatır

echo ========================================
echo Frontend HTTP Sunucusu Baslatiliyor...
echo ========================================
echo.
echo Frontend: http://localhost:8080
echo.
echo [CTRL+C] ile durdurmak icin
echo.

REM Proje dizinine git
cd /d "%~dp0"

REM Python kontrolü
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi! Lutfen Python 3.11+ yukleyin.
    pause
    exit /b 1
)

REM Python HTTP sunucusu başlat
echo.
echo Frontend sunucusu baslatiliyor...
echo Tarayicida http://localhost:8080 adresini acin
echo.
python -m http.server 8080

pause

