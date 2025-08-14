# OpsPilot MVP - RegTech Platform for Derivatives Post-Trade Automation

AI-powered platform for derivatives reconciliation, exception management, SPAN/margin analysis, regulatory exports, and audit trails.

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

### Development Setup

1. **Clone and start services**:
   ```bash
   git clone <repo-url>
   cd opspilot-mvp
   docker-compose up --build
   ```

2. **Access applications**:
   - Backend API: http://localhost:8000/docs
   - Vite dashboard: http://localhost:5173
   - Next.js modules: http://localhost:3000
   - Metrics: http://localhost:8000/metrics

3. **Database migrations**:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

### Authentication & Demo

- **Login**: Use any email with password `"demo"`
- **Admin role**: Include `"+admin@"` in email (e.g., `user+admin@example.com`)
- **Demo flow**: Click "Run Demo" in dashboard → triggers reconciliation with sample data

## Architecture

### Backend (FastAPI)
- **Location**: `backend/app/`
- **Key modules**: ingestion, reconciliation, risk/SPAN, margin, reports, audit
- **Auth**: JWT with access/refresh tokens, RBAC (analyst/admin)
- **Database**: PostgreSQL with Alembic migrations
- **Queue**: Celery + Redis for async tasks

### Frontend
- **Investor Dashboard**: Vite + React + Tailwind (`apps/web/`)
- **Module Pages**: Next.js (`frontend/`)
- **Auth**: Token-based with automatic refresh

## Environment Variables

**Backend**:
```bash
# Core
DATABASE_URL=postgresql+psycopg2://user:pass@db:5432/opspilot
REDIS_URL=redis://redis:6379/0
CORS_ALLOW_ORIGINS=http://localhost:5173,http://localhost:3000

# Security
JWT_SECRET=your-secret-key
ACCESS_TOKEN_TTL=900
REFRESH_TOKEN_TTL=2592000

# Rate limiting
RATE_LIMIT_AUTH_PER_MINUTE=30
RATE_LIMIT_UPLOAD_PER_MINUTE=10

# Reconciliation
RECON_CONFIG_PATH=/path/to/recon.yml

# SFTP polling (optional)
SFTP_LOCAL_DIRS=/data/incoming,/data/sftp

# Features
AI_ENABLED=false
USE_CELERY=true
OTEL_ENABLED=false
```

**Frontend**:
```bash
VITE_API_BASE=http://localhost:8000
```
