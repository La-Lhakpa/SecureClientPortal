# Backend (FastAPI)

FastAPI service providing JWT auth, file sharing, and audit logging.

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env
```

## Running
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Database
- Postgres (recommended): `postgresql://user:pass@host:5432/db`
- Configured via `DATABASE_URL` in `.env`.

### Alembic
```bash
alembic upgrade head          # apply migrations
alembic revision --autogenerate -m "msg"  # create new revision
```

## Auth
- Email/password with bcrypt hashing.
- JWT access tokens with configurable expiry.
- No roles.
- Google Sign-In supported via `POST /auth/google` (server-side ID token verification).

## File Storage
- Uploads saved under `STORAGE_DIR` (default: `backend/storage/`, ignored by git).
- Access control enforced in routes.

## Transfers (multi-file + access code gating)
- New flow:
  - `POST /transfers/send` (multipart) — send multiple files + one access code
  - `POST /transfers/{id}/verify` — receiver verifies access code, receives short-lived `transfer_access_token`
  - `GET /transfers/received`, `GET /transfers/sent` — transfer lists
  - `GET /transfers/{id}/files` — list transfer files (receiver requires `X-Transfer-Token`)
  - `GET /transfers/{id}/files/{file_id}/download` — stream download (receiver requires `X-Transfer-Token`)
  - `GET /transfers/{id}/download-all` — stream zip download (receiver requires `X-Transfer-Token`)

## Legacy endpoints
- Existing `/files/*` endpoints remain for backward compatibility.

## Tests
```bash
pytest
```
