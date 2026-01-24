# Google Token Verification Fix

## Issue
"Invalid Google token" error when trying to sign in with Google.

## Root Causes

Based on the console errors, there are two main issues:

1. **Origin Not Authorized**: `[GSI_LOGGER]: The given origin is not allowed for the given client ID.`
   - This means `http://localhost:5173` is NOT configured in Google Cloud Console
   - Google will issue tokens, but they may be invalid or fail verification

2. **Backend Token Verification Failure**: The backend's `id_token.verify_oauth2_token()` is raising a `ValueError`
   - This could be due to client ID mismatch
   - Or invalid token format due to origin mismatch

## Fixes Applied

### 1. Improved Backend Error Handling
- ✅ Added detailed logging of token length and client ID
- ✅ Enhanced error messages to show actual Google error
- ✅ Better error categorization (wrong issuer, wrong audience, etc.)

### 2. Error Messages Now Show:
- Token verification failure details
- Client ID mismatch warnings
- Origin authorization issues

## Required: Google Cloud Console Configuration

**CRITICAL**: You MUST configure the following in Google Cloud Console:

### Steps:
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
8. **Wait 1-2 minutes** for changes to propagate

## Verification

After updating Google Cloud Console:

1. **Clear browser cache** or use incognito mode
2. **Restart frontend** (to reload env vars):
   ```powershell
   # Stop frontend (Ctrl+C)
   cd frontend
   npm run dev
   ```
3. **Check backend logs** when you try to sign in - you should see:
   - `[GOOGLE_LOGIN] Token length: <number>`
   - `[GOOGLE_LOGIN] Using Client ID: 717847677426-...`
   - Either success or detailed error message

## Common Error Messages

### "Token has wrong issuer"
- **Fix**: Ensure origin is authorized in Google Cloud Console

### "Token has wrong audience" 
- **Fix**: Verify `GOOGLE_CLIENT_ID` in backend `.env` matches frontend `VITE_GOOGLE_CLIENT_ID`

### "Wrong number of segments"
- **Fix**: Token is malformed, likely due to origin mismatch

## Current Configuration

- **Frontend Client ID**: `717847677426-cht6ut819lh4vg32o80jd7epe6r8a9lf.apps.googleusercontent.com`
- **Backend Client ID**: `717847677426-cht6ut819lh4vg32o80jd7epe6r8a9lf.apps.googleusercontent.com` ✅
- **Frontend Origin**: `http://localhost:5173` (needs to be authorized in Google Cloud Console)

## Next Steps

1. ✅ Update Google Cloud Console with authorized origins
2. ✅ Wait 1-2 minutes for propagation
3. ✅ Clear browser cache
4. ✅ Restart frontend
5. ✅ Try Google Sign-In again
6. ✅ Check backend logs for detailed error if it still fails
