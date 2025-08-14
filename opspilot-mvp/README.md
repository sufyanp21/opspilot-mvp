# OpsPilot MVP - Derivatives Data Automation Platform

A derivatives-first data automation platform for ETD and OTC derivatives workflows, featuring automated reconciliation, exception management, and SPAN margin analysis.

## Quick Start

### One Command Start with Docker Compose

```bash
# Clone and start the entire stack
git clone <repository-url>
cd opspilot-mvp
cp infra/.env.example infra/.env
docker-compose -f infra/docker-compose.yml up -d
```

Access the application:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Local Development (Without Docker)

#### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

#### Backend Setup (Windows)

```bash
# Navigate to backend
cd apps/backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
set DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/opspilot
set APP_ENV=dev
set FILE_STORAGE_DIR=C:\data\uploads

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Backend Setup (macOS/Linux)

```bash
# Navigate to backend
cd apps/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/opspilot
export APP_ENV=dev
export FILE_STORAGE_DIR=/data/uploads

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup

```bash
# Navigate to frontend
cd apps/frontend

# Install dependencies
npm install

# Set environment variables
echo "VITE_API_BASE=http://localhost:8000" > .env

# Start development server
npm run dev
```

## API Examples

### Health Check
```bash
curl http://localhost:8000/health
# Response: {"status": "ok"}
```

### Upload Files
```bash
# Upload internal trades file
curl -X POST "http://localhost:8000/api/v1/files/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@internal_trades.csv" \
  -F "kind=internal"

# Upload cleared trades file
curl -X POST "http://localhost:8000/api/v1/files/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@cleared_trades.csv" \
  -F "kind=cleared"
```

### Run Reconciliation
```bash
curl -X POST "http://localhost:8000/api/v1/reconcile" \
  -H "Content-Type: application/json" \
  -d '{
    "internal_file_id": "uuid-here",
    "cleared_file_id": "uuid-here",
    "column_map": {
      "internal": {"Trade ID": "trade_id", "Account": "account", "Symbol": "symbol"},
      "cleared": {"Trade ID": "trade_id", "Account": "account", "Symbol": "symbol"}
    },
    "match_keys": ["trade_date", "account", "symbol"],
    "tolerances": {"price_ticks": 1, "qty": 0}
  }'
```

### Upload SPAN File
```bash
curl -X POST "http://localhost:8000/api/v1/span/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@span_2025-08-08.csv"
```

### Get SPAN Changes
```bash
curl "http://localhost:8000/api/v1/span/changes?asof=2025-08-08"
```

## Frontend Environment Setup

Create `apps/frontend/.env`:
```
VITE_API_BASE=http://localhost:8000
```

## Architecture

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL + Redis
- **Frontend**: React + Vite + TypeScript + Tailwind + shadcn/ui
- **Database**: PostgreSQL with Alembic migrations
- **File Storage**: Local disk (configurable for S3)
- **Task Queue**: Celery with Redis broker

## Features

### 1. File Upload & Processing
- Support for CSV files (internal trades, cleared trades, SPAN data)
- Column mapping interface for field alignment
- File validation and error reporting

### 2. Trade Reconciliation
- ETD position reconciliation with configurable tolerances
- Multi-way matching (internal vs cleared vs CCP)
- Price tick difference calculation
- Exception detection and reporting

### 3. SPAN Margin Analysis
- SPAN file processing with date detection
- Delta calculation between snapshots
- Margin change visualization and reporting

### 4. Exception Management
- Break detection with severity classification
- Assignment and resolution workflows
- Audit trail and status tracking

## Troubleshooting

### Windows Path Length Issues
If you encounter path length issues on Windows:
```bash
# Enable long path support
git config --system core.longpaths true
```

### CSV Encoding Issues
Ensure CSV files are UTF-8 encoded. If you have encoding issues:
- Open CSV in Excel and save as "CSV UTF-8"
- Or use PowerShell: `Get-Content file.csv | Out-File -Encoding UTF8 file_utf8.csv`

### Database Connection Issues
Check PostgreSQL is running and accessible:
```bash
# Test connection
psql -h localhost -p 5432 -U postgres -d opspilot
```

### Port Conflicts
If ports 8000 or 5173 are in use:
- Backend: Change port in uvicorn command
- Frontend: Use `npm run dev -- --port 3000`

## Sample Data

The repository includes sample CSV files in `apps/backend/app/fixtures/`:
- `internal_trades.csv`: Sample internal trade data
- `cleared_trades.csv`: Sample cleared trade data with one price mismatch
- `span_2025-08-08.csv` & `span_2025-08-09.csv`: Sample SPAN margin data

## Development

### Running Tests
```bash
# Backend tests
cd apps/backend
pytest

# Frontend tests
cd apps/frontend
npm test
```

### Code Quality
```bash
# Backend formatting
cd apps/backend
black app/
ruff app/

# Frontend formatting
cd apps/frontend
npm run lint
npm run format
```

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions, please check the troubleshooting section above or create an issue in the repository.
