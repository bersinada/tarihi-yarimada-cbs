@echo off
REM Frontend HTTP Sunucusu
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

REM Python HTTP sunucusu başlat
python -m http.server 8080

pause

