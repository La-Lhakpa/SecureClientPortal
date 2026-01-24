# Debugging Guide - Registration & Login Issues

## Overview
This guide helps verify that registration and login are working correctly with PostgreSQL.

## Step 1: Verify Backend is Connected to PostgreSQL

### Check Startup Logs
When you start the backend, you should see logs like:
```
[DATABASE] Connecting to: postgresql://postgres:***@localhost:5432/SecureFileSharingSystemsDatabase
[DATABASE] Engine created successfully. Dialect: postgresql
[DATABASE] Connected to PostgreSQL database: SecureFileSharingSystemsDatabase
[DATABASE] Connected as user: postgres
[DATABASE] PostgreSQL version: PostgreSQL 15.x...
```

**If you see "WARNING: Using SQLite instead of PostgreSQL!"** - the backend is using the wrong database!

### Check Database Info Endpoint
```powershell
# In PowerShell:
Invoke-WebRequest -Uri "http://127.0.0.1:8000/debug/dbinfo" | Select-Object -ExpandProperty Content

# Or in browser:
http://127.0.0.1:8000/debug/dbinfo
```

Expected response:
```json
{
  "database_url_masked": "postgresql://postgres:***@localhost:5432/SecureFileSharingSystemsDatabase",
  "dialect": "postgresql",
  "driver": "psycopg2",
  "current_database": "SecureFileSharingSystemsDatabase",
  "current_user": "postgres",
  "postgresql_version": "PostgreSQL 15.x...",
  "users_count": 0
}
```

**Important:** Check that:
- `dialect` is `"postgresql"` (NOT `"sqlite"`)
- `current_database` matches your expected database name
- `users_count` shows the current number of users

## Step 2: Test User Creation

### Create Test User via Debug Endpoint
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/debug/test-user" -Method POST | Select-Object -ExpandProperty Content
```

Expected response:
```json
{
  "status": "created",
  "message": "Test user created successfully",
  "user_id": 1,
  "email": "test@example.com",
  "verified": true,
  "total_users": 1
}
```

### Verify in PostgreSQL
```powershell
# Connect to PostgreSQL (adjust connection string as needed)
psql -U postgres -d SecureFileSharingSystemsDatabase

# Then run:
SELECT id, email, created_at FROM users;
```

You should see the test user.

### Check /debug/dbinfo Again
After creating test user, check `/debug/dbinfo` again - `users_count` should increase.

## Step 3: Test Registration Flow

### Register a User via Frontend
1. Go to `http://localhost:5173/register`
2. Enter email: `user@example.com`
3. Enter password: `testpassword123`
4. Click "Create account"

### Check Backend Logs
You should see detailed logs:
```
[REGISTER] Attempting to register user with email: user@example.com
[REGISTER] Checking if email exists in database...
[REGISTER] Email is available. Hashing password...
[REGISTER] Password hashed. Hash length: 60
[REGISTER] Creating User model instance...
[REGISTER] Adding user to session...
[REGISTER] Flushing session to get user ID...
[REGISTER] Flush successful. User ID assigned: 1
[REGISTER] Committing transaction...
[REGISTER] Transaction committed successfully
[REGISTER] User refreshed. ID: 1, Email: user@example.com
[REGISTER] VERIFIED: User exists in database with ID 1, Email: user@example.com
[REGISTER] SUCCESS: User registered - ID: 1, Email: user@example.com
```

### Verify User Count Increased
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/debug/dbinfo" | Select-Object -ExpandProperty Content
```

The `users_count` should have increased.

### Verify in PostgreSQL
```sql
SELECT id, email, created_at FROM users WHERE email = 'user@example.com';
```

You should see the user.

## Step 4: Test Login Flow

### Login via Frontend
1. Go to `http://localhost:5173/login`
2. Enter the same email and password you just registered
3. Click "Login"

### Check Backend Logs
You should see:
```
[LOGIN] Attempting login for email: user@example.com
[LOGIN] Querying database for user with email: user@example.com
[LOGIN] User found - ID: 1, Email: user@example.com
[LOGIN] Stored password hash length: 60
[LOGIN] Verifying password...
[LOGIN] Password verification result: True
[LOGIN] Password verified successfully. Creating JWT token...
[LOGIN] Token created. Length: 200+
[LOGIN] SUCCESS: Login successful - User ID: 1, Email: user@example.com
```

## Troubleshooting

### Issue: Registration succeeds but user not in database

**Check:**
1. Is the backend using PostgreSQL? Check `/debug/dbinfo` - `dialect` should be `"postgresql"`
2. Are there any errors in backend logs during commit?
3. Check if transaction is being rolled back - look for "ERROR: Commit failed" in logs
4. Verify the database URL in `.env` is correct

**Fix:**
- Ensure `DATABASE_URL` in `.env` starts with `postgresql://` (not `sqlite://`)
- Check PostgreSQL is running: `pg_isready -h localhost -p 5432`
- Verify database exists: `psql -U postgres -l` should list your database

### Issue: Login fails with "Invalid email or password"

**Check:**
1. Is the user actually in the database? Check `/debug/dbinfo` - `users_count`
2. Check backend logs - does it say "User not found" or "Password verification FAILED"?
3. If "User not found" - the user wasn't saved during registration
4. If "Password verification FAILED" - password hashing/verification issue

**Fix:**
- If user not found: Check registration logs for commit errors
- If password verification fails: This is rare but could indicate bcrypt version mismatch

### Issue: Backend shows "Using SQLite instead of PostgreSQL!"

**Fix:**
1. Check `backend/.env` - `DATABASE_URL` must start with `postgresql://`
2. Ensure `.env` file is in the `backend/` directory
3. Restart the backend server after changing `.env`
4. Check that `pydantic-settings` is reading the `.env` file correctly

## Windows PowerShell Commands Summary

```powershell
# 1. Start backend (in backend directory)
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# 2. Check database connection (in new terminal)
Invoke-WebRequest -Uri "http://127.0.0.1:8000/debug/dbinfo" | ConvertFrom-Json | Format-List

# 3. Create test user
Invoke-WebRequest -Uri "http://127.0.0.1:8000/debug/test-user" -Method POST | ConvertFrom-Json | Format-List

# 4. Check user count again
Invoke-WebRequest -Uri "http://127.0.0.1:8000/debug/dbinfo" | ConvertFrom-Json | Select-Object users_count

# 5. Verify in PostgreSQL (if psql is in PATH)
psql -U postgres -d SecureFileSharingSystemsDatabase -c "SELECT id, email, created_at FROM users;"
```

## Files Changed

### Backend:
- `backend/app/database.py` - Added startup logging and connection verification
- `backend/app/main.py` - Added `/debug/dbinfo` and `/debug/test-user` endpoints
- `backend/app/routers/auth.py` - Added comprehensive logging to register/login
- `backend/app/security.py` - Added error handling to password verification

### No Frontend Changes Required
The frontend is already calling the correct endpoints with the correct format.
