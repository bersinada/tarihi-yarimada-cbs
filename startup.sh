#!/bin/bash

# Azure App Service Startup Script
# Bu script Azure'da uygulama başlatılırken çalışır

# Çalışma dizinine geç
cd /home/site/wwwroot

# Gunicorn ile FastAPI uygulamasını başlat
# Workers: CPU sayısına göre ayarlanır (Azure'da genellikle 2-4)
gunicorn backend.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

