#!/bin/bash

# Azure App Service Startup Script
cd /home/site/wwwroot

# Virtual environment'ı aktifleştir
source antenv/bin/activate

# Gunicorn ile FastAPI uygulamasını başlat
gunicorn backend.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT:-8000} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

