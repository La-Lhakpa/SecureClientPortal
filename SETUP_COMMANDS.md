# Quick Setup Commands (Windows PowerShell)

## Prerequisites
- PostgreSQL database running and accessible
- Python 3.8+ installed
- Node.js and npm installed

## Backend Setup

```powershell
# 1. Navigate to backend
cd backend

# 2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify .env file exists with correct DATABASE_URL
# Example: DATABASE_URL=postgresql://postgres:password@localhost:5432/database_name
# If .env doesn't exist, copy from .env.example and update DATABASE_URL

# 5. Run database migrations
alembic upgrade head

# 6. Start backend server (port 8001)
uvicorn app.main:app --reload --port 8001
```

## Frontend Setup

```powershell
# 1. Navigate to frontend (in a new terminal)
cd frontend

# 2. Install dependencies (if not already done)
npm install

# 3. Start frontend dev server (port 5173)
npm run dev
```

## Verify Everything Works

1. **Check backend health:**
   - Open browser: `http://localhost:8001/health/db`
   - Should return: `{"db":"ok","dialect":"postgresql"}`

2. **Check frontend:**
   - Open browser: `http://localhost:5173`
   - Should show login page

3. **Test registration:**
   - Go to `/register`
   - Enter email and password
   - Select role (OWNER or CLIENT)
   - Submit form
   - Should redirect to login page

4. **Test login:**
   - Enter registered email and password
   - Should redirect based on role:
     - OWNER → `/send`
     - CLIENT → `/client`

## Troubleshooting

### Backend won't start
- Check PostgreSQL is running
- Verify `DATABASE_URL` in `.env` is correct
- Check port 8001 is not in use

### Frontend can't connect to backend
- Verify backend is running on port 8001
- Check browser console for CORS errors
- Verify `ALLOWED_ORIGINS` in backend `.env` includes `http://localhost:5173`

### Database migration fails
- Ensure PostgreSQL is running
- Verify database exists
- Check `DATABASE_URL` has correct credentials
- Try: `alembic current` to see current migration state

### Login/Register fails
- Check backend console for error messages
- Verify database connection: `http://localhost:8001/health/db`
- Check browser network tab for API errors
- Verify email format is valid (e.g., `user@example.com`)
