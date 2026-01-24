# Google Sign-In Configuration Fix

## Issue
Error: "Google login not configured. Please contact support."

## Root Cause
The backend `.env` file was missing the `GOOGLE_CLIENT_ID` environment variable, even though the frontend had it configured.

## Fixes Applied

### 1. Backend `.env` File
- ✅ Added `GOOGLE_CLIENT_ID=717847677426-cht6ut819lh4vg32o80jd7epe6r8a9lf.apps.googleusercontent.com`
- ✅ Updated `ALLOWED_ORIGINS` to include both `http://localhost:5173` and `http://127.0.0.1:5173`

### 2. Frontend `.env` File
- ✅ Updated `VITE_API_BASE_URL` to use `http://127.0.0.1:8000` (consistent with backend)

### 3. GoogleSignInButton Component
- ✅ Fixed button width from `"100%"` (string) to `300` (number) to resolve GSI warning

## Important: Google Cloud Console Configuration

Based on the console error `[GSI_LOGGER]: The given origin is not allowed for the given client ID`, you need to configure the following in Google Cloud Console:

### Authorized JavaScript Origins
Add these URLs to your OAuth 2.0 Client ID configuration:
- `http://localhost:5173`
- `http://127.0.0.1:5173`

### Authorized Redirect URIs
Add these URLs:
- `http://localhost:5173`
- `http://127.0.0.1:5173`

## Steps to Fix in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** → **Credentials**
3. Find your OAuth 2.0 Client ID: `717847677426-cht6ut819lh4vg32o80jd7epe6r8a9lf.apps.googleusercontent.com`
4. Click **Edit**
5. Under **Authorized JavaScript origins**, add:
   - `http://localhost:5173`
   - `http://127.0.0.1:5173`
6. Under **Authorized redirect URIs**, add:
   - `http://localhost:5173`
   - `http://127.0.0.1:5173`
7. Click **Save**

## Restart Required

After updating the `.env` files, you **must restart** both servers:

### Backend:
```powershell
# Stop the current backend server (Ctrl+C)
# Then restart:
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend:
```powershell
# Stop the current frontend server (Ctrl+C)
# Then restart:
cd frontend
npm run dev
```

## Verification

After restarting and updating Google Cloud Console:

1. Navigate to `http://localhost:5173/login`
2. Click the Google Sign-In button
3. Should see Google account picker (no "origin not allowed" error)
4. After selecting account, should successfully authenticate and navigate to `/dashboard`

## Current Configuration

- **Frontend Client ID**: `717847677426-cht6ut819lh4vg32o80jd7epe6r8a9lf.apps.googleusercontent.com`
- **Backend Client ID**: `717847677426-cht6ut819lh4vg32o80jd7epe6r8a9lf.apps.googleusercontent.com` (same)
- **API Base URL**: `http://127.0.0.1:8000`
