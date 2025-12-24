#!/bin/bash

# Azure App Service Startup Script
# Bu script Azure'da uygulama başlatılırken çalışır

# Çalışma dizinine geç
cd /home/site/wwwroot

# Gunicorn ile FastAPI uygulamasını başlat
# PORT: Azure tarafından otomatik atanır (genellikle 8080)
gunicorn backend.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT:-8000} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

