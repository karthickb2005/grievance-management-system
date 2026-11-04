# Grievance Router — Multilingual AI Civic Complaint Triage Platform

A lightweight civic complaint classification and routing system built for Indian municipal corporations. Handles multilingual complaints (Hinglish, Hindi, Kannada, Tamil), geospatial clustering, and intelligent department routing.

## Architecture (LITE Mode)

- **Backend**: FastAPI + SQLite + SpatiaLite
- **ML**: Sentence-Transformers (multilingual) + FAISS vector search
- **Frontend**: Static HTML/CSS/JS served by FastAPI
- **Geospatial**: SpatiaLite for spatial queries, 150m clustering radius
- **Languages**: English, Hinglish, Hindi, Kannada, Tamil

## Features

- ✅ Multilingual complaint classification
- ✅ Department routing (Roads, Water, Waste, Streetlights, Drainage, Trees)
- ✅ Geospatial clustering (merge similar complaints within 150m)
- ✅ Severity scoring (Low, Medium, High, Critical)
- ✅ Alert detection (spike detection for ward-level issues)
- ✅ Officer command map with hex density visualization
- ✅ Citizen portal (submit and track complaints)

## Hardware Requirements

- **RAM**: 1GB available (project uses ~400-600MB)
- **Python**: 3.11+ (3.11.9 recommended)
- **Disk**: ~500MB (models + data)

## Quick Start

```bash
# 1. Create virtual environment (Python 3.11)
py -3.11 -m venv venv
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize database and seed data
python scripts/init_db.py
python scripts/seed.py

# 4. Run the application
python app/main.py
```

**Access the application**: http://localhost:8000

## Project Structure

```
grievance_router_lite/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration
│   ├── database.py          # SQLite connection
│   ├── models.py            # SQLAlchemy models
│   ├── api/
│   │   ├── complaints.py    # Complaint endpoints
│   │   ├── issues.py        # Issue endpoints
│   │   ├── geo.py           # Geospatial endpoints
│   │   └── alerts.py        # Alert endpoints
│   └── services/
│       ├── classifier.py    # ML classification
│       ├── geocoder.py      # Geospatial clustering
│       └── alerting.py      # Alert detection
├── frontend/                # Static HTML/CSS/JS
├── data/
│   ├── wards.json          # BBMP ward boundaries
│   └── prototypes.json     # Classification prototypes
├── tests/
│   ├── test_classifier.py
│   └── test_geo.py
├── scripts/
│   ├── init_db.py          # Database initialization
│   ├── seed.py             # Seed data
│   ├── evaluate.py         # Model evaluation
│   └── demo_burst.py       # Demo spike scenario
├── alembic/                # Database migrations
├── requirements.txt
└── Makefile
```

## Available Commands

```bash
make install      # Install dependencies
make init         # Initialize database
make seed         # Seed test data
make run          # Start the application
make test         # Run unit tests
make eval         # Run model evaluation
make demo-burst   # Run demo spike scenario
make clean        # Clean up generated files
```

## API Endpoints

### Complaints
- `POST /api/complaints` — Submit a new complaint
- `GET /api/complaints` — List complaints
- `GET /api/complaints/{id}` — Get complaint details

### Issues (Merged Complaints)
- `GET /api/issues` — List issues
- `GET /api/issues/{id}` — Get issue details

### Geospatial
- `GET /api/geo/hex-density` — Get hex density GeoJSON
- `GET /api/geo/nearby` — Find nearby complaints

### Alerts
- `GET /api/alerts` — List active alerts

## Database Schema

- **complaints** — Individual complaint submissions
- **issues** — Merged/clustered complaints
- **wards** — BBMP ward boundaries (spatial)
- **departments** — Department definitions
- **alerts** — Generated alerts for spike detection

## ML Models

- **Embedding Model**: `paraphrase-multilingual-MiniLM-L12-v2` (384-dim)
  - Size: ~120MB
  - Languages: 50+ including Hindi, Kannada, Tamil
  - First run downloads from HuggingFace

- **Classification**: Prototype-based with cosine similarity
  - 6 categories × 3 examples = 18 prototypes
  - Multilingual support via embeddings

- **Severity**: Keyword-based scoring (placeholder for vision model)

## Testing

```bash
# Unit tests
python -m pytest tests/test_classifier.py -v

# Integration tests
python -m pytest tests/ -v

# Evaluation
python scripts/evaluate.py
```

## Limitations (LITE Mode)

- **No Docker**: Runs directly with Python (lower resource usage)
- **SQLite**: Not for production scale, but sufficient for demo/dev
- **No async workers**: Single-threaded processing
- **Vision severity**: Placeholder (keyword-based, not actual image analysis)
- **Simulated adapters**: WhatsApp/Twitter endpoints are stubs
- **Synthetic ward boundaries**: Approximate BBMP wards

## Ports

- `8000` — Main application (API + frontend)

## Environment Variables

Create `.env` file (optional):

```
DATABASE_URL=sqlite:///./grievance_router.db
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
```

## Troubleshooting

### SpatiaLite not found
- Windows: Install via `pip install pyspatialite` or falls back to simple geo math

### Model download fails
- Check internet connection
- Models download from HuggingFace on first run (~120MB)

### Port 8000 in use
- Change in `app/config.py`: `PORT = 8001`

## License

MIT

## Credits

Built for Bangalore BBMP (Bruhat Bengaluru Mahanagara Palike) civic complaint management.
