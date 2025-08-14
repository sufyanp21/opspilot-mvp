# OpsPilot Backend – Security and Audit Additions

## Auth
- Endpoints:
  - POST `/auth/login` – returns access and refresh tokens (demo password: `demo`)
  - POST `/auth/refresh` – exchange refresh for new tokens
- Roles: `analyst` (default), `admin` (emails containing `+admin@`)
- Use `Authorization: Bearer <access>` header.

## Rate limiting
- Simple token-bucket limiter applied to `/auth/*` and `/upload` paths.
- Configure via ENV in `app/settings.py` (tokens per minute).

## Audit
- Immutable JSONL continues under `TMP_DIR/audit`.
- New DB table `audit_log` with helper `auditlog(...)` for structured entries.

## Migrations
```bash
alembic upgrade head
```


