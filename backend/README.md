# Tarihi Yarimada CBS - Backend

Istanbul Tarihi Yarimada Kulturel Miras CBS Platformu Backend API

## Architecture

Clean Architecture implementation with FastAPI and PostGIS.

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Settings and environment variables
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py         # Engine, SessionLocal, get_db
│   │   └── models.py           # SQLAlchemy models (7 tables)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── assets.py           # /api/v1/assets
│   │   ├── segments.py         # /api/v1/segments (SAM3D)
│   │   ├── notes.py            # /api/v1/notes
│   │   └── ogc.py              # /api/v1/ogc/wfs
│   │
│   └── schemas/
│       ├── __init__.py
│       ├── asset.py            # Asset Pydantic models
│       └── segment.py          # Segment Pydantic models
│
├── scripts/
│   └── seed_data.py            # Initial data seeding
│
├── requirements.txt
├── .env.example
└── README.md
```

## Database Schema (7 Tables)

| Table | Description | Standards |
|-------|-------------|-----------|
| `heritage_assets` | Main heritage asset table | Dublin Core + TUCBS |
| `asset_segments` | SAM3D segmented 3D model parts | - |
| `dataset_metadata` | Dataset-level metadata | ISO 19115 |
| `actors` | Architects and patrons | - |
| `asset_actors` | Asset-Actor relationships | - |
| `media` | Asset images and media | - |
| `user_notes` | User notes on assets | - |

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 3. Seed Database

```bash
python -m scripts.seed_data
```

### 4. Run Server

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## API Endpoints

### Assets

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/assets` | List all assets |
| GET | `/api/v1/assets/{id}` | Get asset by ID |
| GET | `/api/v1/assets/identifier/{identifier}` | Get by identifier (HA-0001) |
| GET | `/api/v1/assets/geojson` | Get assets as GeoJSON |
| POST | `/api/v1/assets` | Create new asset |
| PATCH | `/api/v1/assets/{id}` | Update asset |
| DELETE | `/api/v1/assets/{id}` | Delete asset |

### Segments (SAM3D)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/segments` | List all segments |
| GET | `/api/v1/segments/{id}` | Get segment by ID |
| GET | `/api/v1/segments/by-asset/{asset_id}` | Get segments for asset |
| GET | `/api/v1/segments/types` | List segment types |
| POST | `/api/v1/segments` | Create new segment |
| PATCH | `/api/v1/segments/{id}` | Update segment |
| DELETE | `/api/v1/segments/{id}` | Delete segment |

### OGC WFS 2.0

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/ogc/wfs/capabilities` | GetCapabilities |
| GET | `/api/v1/ogc/wfs` | GetFeature |
| GET | `/api/v1/ogc/wfs/describe` | DescribeFeatureType |

### Other

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/metadata` | Dataset metadata (ISO 19115) |
| GET | `/api/v1/search?q=` | Search assets |
| GET | `/api/cesium-config` | Cesium Ion token |

## Standards

- **Dublin Core**: Metadata standard for cultural heritage
- **TUCBS Koruma Alanlari**: Turkish National SDI heritage protection
- **ISO 19115**: Geographic metadata standard
- **OGC WFS 2.0**: Web Feature Service standard

## GeoJSON Output Format

```json
{
  "type": "FeatureCollection",
  "crs": {
    "type": "name",
    "properties": { "name": "EPSG:4326" }
  },
  "features": [
    {
      "type": "Feature",
      "id": "HA-0001",
      "geometry": {
        "type": "Point",
        "coordinates": [28.9639, 41.0162]
      },
      "properties": {
        "identifier": "HA-0001",
        "name_tr": "Suleymaniye Camii",
        "asset_type": "cami",
        "historical_period": "osmanli_klasik",
        "construction_year": 1557,
        "protection_status": "1. derece",
        "model_type": "SPLAT",
        "segment_count": 3
      }
    }
  ]
}
```

## Segment Types

| Code | Turkish |
|------|---------|
| dome | Kubbe |
| minaret | Minare |
| portal | Tackapi/Giris |
| wall | Duvar |
| window | Pencere |
| courtyard | Avlu |
| fountain | Sadirvan |
| column | Sutun |
| arch | Kemer |
| roof | Cati |
| other | Diger |
