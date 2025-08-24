# OpsPilot MVP Demo (Windows-first)

### Quick Start (One-click)
1. Install prerequisites: Python 3.11+, Node 20+, npm 9+, Docker Desktop
2. Open PowerShell in repo root
3. Run:

```
python scripts/demo_doctor.py; python scripts/demo_run.py
```

If you prefer manual steps, use `scripts/demo_checklist.ps1`.

### URLs
- Backend: http://127.0.0.1:8000/health and http://127.0.0.1:8000/docs
- Frontend: http://localhost:5173

### Credentials
- Any email, password: `demo`
- Admin: email with `+admin@`

### Notes
- Ensure `apps/web/.env` contains `VITE_API_BASE=http://127.0.0.1:8000` for local dev.
- If ports are busy, stop other processes or update the ports accordingly.

