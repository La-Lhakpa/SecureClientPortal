# Backend Startup Fix

## Issue
Backend is not running. Error: "ModuleNotFoundError: No module named 'fastapi'"

## Root Cause
The backend is trying to run using the system Python instead of the virtual environment where all dependencies are installed.

## Solution

### Step 1: Activate Virtual Environment

**PowerShell:**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
```

If you get an execution policy error, run this first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Alternative (Command Prompt):**
```cmd
cd backend
venv\Scripts\activate.bat
```

### Step 2: Verify Dependencies Are Installed

```powershell
# After activating venv, check if FastAPI is installed
pip list | findstr fastapi
```

If FastAPI is not listed, install dependencies:
```powershell
pip install -r requirements.txt
```

### Step 3: Start Backend Server

**On Port 8000 (Default):**
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**On Port 8010 (If 8000 is in use):**
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

**Important:** If you change the port to 8010, you MUST also update:
- `frontend/.env`: Change `VITE_API_BASE_URL=http://127.0.0.1:8000` to `http://127.0.0.1:8010`
- Restart the frontend after changing `.env`

### Step 4: Verify Backend is Running

Open a new terminal and test:
```powershell
curl http://127.0.0.1:8000/health
# Should return: {"status":"ok"}
```

Or visit in browser: `http://127.0.0.1:8000/docs` (FastAPI auto-generated docs)

## Common Issues

### Issue 1: Port Already in Use
If you get "Address already in use":
```powershell
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Issue 2: Database Connection Error
If you see database connection errors:
1. Ensure PostgreSQL is running
2. Check `backend/.env` has correct `DATABASE_URL`
3. Verify database exists: `SecureFileSharingSystemsDatabase`

### Issue 3: Import Errors
If you see import errors after activating venv:
```powershell
# Reinstall all dependencies
pip install -r requirements.txt
```

## Quick Start Commands (Copy-Paste Ready)

**PowerShell (Full Sequence):**
```powershell
cd "C:\Users\ittra\Desktop\File Sharing system\backend"
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**If Port 8000 is Busy:**
```powershell
cd "C:\Users\ittra\Desktop\File Sharing system\backend"
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

Then update `frontend/.env`:
```
VITE_API_BASE_URL=http://127.0.0.1:8010
```

## Verification Checklist

- [ ] Virtual environment activated (you should see `(venv)` in terminal prompt)
- [ ] FastAPI installed (`pip list | findstr fastapi` shows fastapi)
- [ ] Backend starts without errors
- [ ] Can access `http://127.0.0.1:8000/health` (or 8010)
- [ ] Frontend `.env` matches backend port
