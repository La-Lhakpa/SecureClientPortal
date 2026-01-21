# Backend (FastAPI)

FastAPI service providing auth, role-protected file operations, and audit logging.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Running
```bash
uvicorn app.main:app --reload
```

## Database
- Default: SQLite file `app.db` in project root (configured via `DATABASE_URL`)
- Production-ready: Postgres (e.g. `postgresql+psycopg2://user:pass@host/db`)

### Alembic
```bash
alembic upgrade head          # apply migrations
alembic revision --autogenerate -m "msg"  # create new revision
```

## Auth
- Email/password with bcrypt hashing.
- JWT access tokens with configurable expiry.
- Roles: `OWNER`, `CLIENT`.

## File Storage
- Uploads saved to `storage/` (ignored by git).
- Access control enforced in routes.

## Tests
```bash
pytest
```
