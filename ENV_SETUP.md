# Environment Setup Guide

## Backend Configuration

Create `backend/.env` with:

```
CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000
JWT_SECRET=change-me-in-production
DATABASE_URL=sqlite:///./opspilot.db
AI_ENABLED=false
OPENAI_API_KEY=your-openai-key-here
TMP_DIR=./tmp/opspilot
RECON_CONFIG_PATH=
```

## Frontend Configuration

Create `apps/web/.env.local` with:

```
VITE_API_BASE=http://localhost:8000
```

## Optional: Next.js Frontend

Create `frontend/.env.local` with:

```
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

## Security Notes

- **Never** put provider API keys (like `OPENAI_API_KEY`) in frontend env files
- Only `VITE_*` and `NEXT_PUBLIC_*` variables are exposed to the browser
- Keep all secrets in backend environment only
- The backend proxies external API calls to keep keys secure
