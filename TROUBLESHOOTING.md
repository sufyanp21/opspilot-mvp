# Troubleshooting (Windows-first)

## Health check hangs
- Ensure backend bound to 127.0.0.1: `(cd backend; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload)`
- Check firewall rules and that port 8000 is free

## Docker web build stalls at npm
- Use `npm ci --no-audit --no-fund`
- If peer dep conflicts persist, retry once with `--legacy-peer-deps`

## CORS / 403 on upload
- Confirm `CORS_ALLOW_ORIGINS` includes `http://localhost:5173` and `http://127.0.0.1:5173`

## CSV parse errors
- Ensure CSV has headers; try re-saving as UTF-8 (with BOM)
- Use comma `,` delimiter; semicolon `;` not supported by default

## SPA 404 on Vercel
- Add SPA rewrites to always serve `index.html` for client routes

## Reseed DB
- Stop backend; delete local SQLite/seed; re-run `scripts/demo_seed.py`

