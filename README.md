# Medi-Tour Backend API

A production-ready REST API for medical tourism platform built with FastAPI, SQLAlchemy (async), and database-agnostic design.

## Features

- 🔄 **Database Agnostic**: Switch between PostgreSQL and MySQL by changing `DATABASE_URL`
- 📁 **File Uploads**: Local storage for dev, S3 presigned uploads for production
- 🔍 **Complete CRUD**: Full REST API for sliders, hospitals, doctors, treatments, bookings
- 🗄️ **Export/Import**: JSON export/import and SQL dump utilities
- 🧪 **Testing**: Pytest setup with async test support
- 🔒 **Security**: File validation, size limits, rate limiting ready

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env` and update database credentials:

```bash
# PostgreSQL (default)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/meditour_db

# OR MySQL
DATABASE_URL=mysql+aiomysql://user:pass@localhost:3306/meditour_db
```

### 3. Setup Database

```bash
# Initialize migrations
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 4. Run Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at: http://localhost:8000
Interactive docs at: http://localhost:8000/docs

## Project Structure

```
medi-tour/
├─ app/
│  ├─ main.py              # FastAPI app
│  ├─ core/config.py       # Settings
│  ├─ db.py               # Database connection
│  ├─ models.py           # SQLAlchemy models
│  ├─ schemas.py          # Pydantic schemas
│  ├─ api/v1/
│  │  ├─ routes.py        # Main API routes
│  │  └─ uploads.py       # Upload endpoints
│  └─ utils/
│     └─ export_import.py # JSON export/import
├─ alembic/               # Database migrations
├─ scripts/               # Database utilities
├─ media/                 # Local uploads (dev)
└─ tests/                 # Test suite
```

## API Endpoints

### Core Resources
- `POST/GET/PUT/DELETE /api/v1/sliders`
- `POST/GET/PUT/DELETE /api/v1/hospitals`
- `POST/GET/PUT/DELETE /api/v1/doctors`
- `POST/GET/PUT/DELETE /api/v1/treatments`
- `POST/GET /api/v1/bookings`

### Uploads
- `POST /api/v1/uploads/image` - Local upload (dev)
- `POST /api/v1/uploads/presign` - S3 presigned URL (prod)
- `POST /api/v1/uploads/notify` - S3 upload confirmation

## Database Operations

### Export/Import JSON (Small Datasets)
```bash
python scripts/export_json.py
python scripts/import_json.py data.json
```

### SQL Dumps

**PostgreSQL:**
```bash
# Export
pg_dump -U user -h host -p port -f meditour.sql meditour_db

# Import
psql -U user -h host -d target_db -f meditour.sql
```

**MySQL:**
```bash
# Export
mysqldump -u user -p -h host meditour_db > meditour.sql

# Import
mysql -u user -p -h host target_db < meditour.sql
```

## Configuration

### Database Switching
Simply change `DATABASE_URL` in `.env`:

```env
# PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# MySQL  
DATABASE_URL=mysql+aiomysql://user:pass@host:3306/db
```

### Upload Configuration
```env
# Local development
DEBUG=true

# Production with S3
S3_BUCKET_NAME=your-bucket
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
```

## Testing

```bash
pytest
```

## Production Deployment

1. Set `DEBUG=false` in `.env`
2. Configure S3 bucket and credentials
3. Use production database
4. Deploy with gunicorn or similar ASGI server

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```