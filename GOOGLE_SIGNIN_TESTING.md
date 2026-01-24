# Google Sign-In Testing Checklist

## Prerequisites

1. **Google Cloud Console Setup**:
   - Create a project in Google Cloud Console
   - Enable Google+ API (or Google Identity Services)
   - Create OAuth 2.0 credentials (Web application)
   - Add authorized JavaScript origins:
     - `http://localhost:5173`
     - `http://127.0.0.1:5173`
   - Add authorized redirect URIs:
     - `http://localhost:5173`
     - `http://127.0.0.1:5173`
   - Copy the **Client ID** (not Client Secret)

2. **Environment Variables**:
   - Set `VITE_GOOGLE_CLIENT_ID` in `frontend/.env`
   - Set `GOOGLE_CLIENT_ID` in `backend/.env`

## Windows PowerShell Commands

### Step 1: Backend Setup

```powershell
# Navigate to backend directory
cd backend

# Activate virtual environment (if using venv)
# .\venv\Scripts\Activate.ps1

# Install dependencies (including google-auth)
pip install -r requirements.txt

# Run database migration to make password_hash nullable
# Note: If alembic is not in PATH, you may need to use: python -m alembic upgrade head
alembic upgrade head

# Start backend server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Step 2: Frontend Setup

```powershell
# Open new terminal, navigate to frontend directory
cd frontend

# Install dependencies (if needed)
npm install

# Start frontend dev server
npm run dev
```

### Step 3: Verify Backend Health

```powershell
# In a new terminal, test backend health
curl http://127.0.0.1:8000/health
# Should return: {"status":"ok"}

# Test database connectivity
curl http://127.0.0.1:8000/health/db
# Should return: {"db":"ok","dialect":"postgresql"}
```

## Manual Testing Steps

### Test 1: Password Registration Still Works
1. Navigate to `http://localhost:5173/register`
2. Fill in email, password, confirm password
3. Click "Create account"
4. ✅ Should redirect to `/login` with success message
5. ✅ Should NOT auto-login

### Test 2: Password Login Still Works
1. Navigate to `http://localhost:5173/login`
2. Enter registered email and password
3. Click "Login"
4. ✅ Should navigate to `/dashboard`
5. ✅ Should show user email in dashboard

### Test 3: Google Sign-In (New User)
1. Navigate to `http://localhost:5173/login`
2. Scroll to "Or continue with" section
3. Click Google sign-in button
4. ✅ Google account picker should appear
5. Select a Google account (or sign in)
6. ✅ Should navigate to `/dashboard` after successful authentication
7. ✅ Should show user email in dashboard
8. ✅ Check browser console - should see "Login successful, token stored"
9. ✅ Check `localStorage.getItem("token")` - should have JWT token

### Test 4: Google Sign-In (Existing User)
1. Use the same Google account from Test 3
2. Logout (if logged in)
3. Navigate to `http://localhost:5173/login`
4. Click Google sign-in button
5. Select the same Google account
6. ✅ Should navigate to `/dashboard` (no new user created)
7. ✅ Should work seamlessly

### Test 5: Token Persistence
1. After Google sign-in, refresh the page (`F5`)
2. ✅ Should remain logged in
3. ✅ Should stay on `/dashboard`
4. ✅ User email should still be visible

### Test 6: `/me` Endpoint Works for Google Users
1. After Google sign-in, open browser DevTools → Network tab
2. Check for request to `/me`
3. ✅ Should return 200 with user data: `{id, email, created_at}`
4. ✅ User should have `password_hash: null` in database

### Test 7: Database Verification
1. Connect to PostgreSQL database
2. Query: `SELECT id, email, password_hash FROM users WHERE email = 'your-google-email@gmail.com';`
3. ✅ Should show user with `password_hash = NULL`
4. ✅ User should be able to use all features (send files, etc.)

### Test 8: Error Handling - Missing Client ID
1. Temporarily remove `VITE_GOOGLE_CLIENT_ID` from `frontend/.env`
2. Restart frontend dev server
3. Navigate to login page
4. ✅ Should show error: "Google login not configured. Please contact support."
5. ✅ Google button should not appear or be disabled

### Test 9: Error Handling - Invalid Token
1. Try to manually call `POST /auth/google` with invalid token
2. ✅ Should return 401 with "Invalid Google token"

### Test 10: Error Handling - Unverified Email
1. Use a Google account with unverified email (if available)
2. Try to sign in
3. ✅ Should return 401 with "Google email not verified"

## Verification Commands

### Check Database Migration
```powershell
# Connect to PostgreSQL and check users table schema
psql -U postgres -d database_name -c "\d users"
# Should show: password_hash | character varying | | |

# Check if migration was applied
# In backend directory:
alembic current
# Should show: 0005_make_password_hash_nullable (head)
```

### Check Backend Logs
- Watch backend terminal for:
  - `[GOOGLE_LOGIN] Attempting to verify Google ID token...`
  - `[GOOGLE_LOGIN] Token verified successfully`
  - `[GOOGLE_LOGIN] Email: ... Verified: True`
  - `[GOOGLE_LOGIN] JWT token created`

### Check Frontend Console
- Open browser DevTools → Console
- Should see:
  - `[GoogleSignIn] Login successful, token stored`
  - No errors related to Google Identity Services

## Common Issues

### Issue: "Google login not configured"
- **Solution**: Ensure `VITE_GOOGLE_CLIENT_ID` is set in `frontend/.env` and frontend is restarted

### Issue: "Invalid Google token"
- **Solution**: Check that `GOOGLE_CLIENT_ID` in backend matches frontend, and that authorized origins are correct in Google Cloud Console

### Issue: Google button doesn't appear
- **Solution**: Check browser console for errors, ensure Google script loaded (`window.google` should exist)

### Issue: Migration fails
- **Solution**: Ensure database connection is working, check `alembic.ini` has correct `sqlalchemy.url`

## Success Criteria

✅ Password registration/login still works  
✅ Google sign-in creates new users  
✅ Google sign-in logs in existing users  
✅ Google users have `password_hash = NULL` in database  
✅ Google users can access `/dashboard`  
✅ Token persists across page refresh  
✅ `/me` endpoint works for Google users  
✅ No "fake login" - all authentication goes through backend  
✅ Error messages are clear and helpful  
