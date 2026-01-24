# Auth Flow Fixes - Protected Route Authorization

## Problem
UI showed "Login Successful" but app did NOT authorize/enter protected pages. ProtectedRoute blocked access or API calls returned 401.

## Root Causes Fixed

1. **ProtectedRoute only checked token existence** - didn't verify token validity
2. **handleAuthSuccess had role-based navigation** - tried to navigate based on non-existent role
3. **Token not properly synchronized** - apiClient might not have token when /me is called
4. **No token validation on app load** - user state not set after page refresh

## Changes Made

### Backend

#### 1. Added `/debug/auth` Endpoint (`backend/app/main.py`)
- ✅ Shows if Authorization header is present
- ✅ Decodes token and shows subject/expiry (no secrets)
- ✅ Useful for debugging why ProtectedRoute fails
- ✅ Call with: `Authorization: Bearer <token>` header

#### 2. CORS Configuration
- ✅ Already configured with `allow_headers=["*"]` which includes Authorization
- ✅ Added `expose_headers=["*"]` for completeness

### Frontend

#### 1. Fixed ProtectedRoute (`frontend/src/App.jsx`)
- ✅ Now verifies token by calling `/me` endpoint
- ✅ Shows loading state while verifying
- ✅ Redirects to login if token invalid
- ✅ Clears token and logs out on 401

#### 2. Fixed handleAuthSuccess (`frontend/src/App.jsx`)
- ✅ Removed role-based navigation (roles don't exist anymore)
- ✅ Always navigates to `/dashboard` after successful auth
- ✅ Verifies token with `/me` before navigating
- ✅ Handles errors properly (clears token, redirects to login)

#### 3. Fixed App Mount Token Validation (`frontend/src/App.jsx`)
- ✅ Validates token on app load
- ✅ Sets user state if token is valid
- ✅ Clears token if validation fails

#### 4. Added DEV Debugging
- ✅ Console logs for all auth operations
- ✅ Visual debug banner in DEV mode showing token/user state
- ✅ API client logs request details in DEV mode

#### 5. Improved API Client (`frontend/src/api.js`)
- ✅ Better logging in DEV mode
- ✅ Logs token presence and Authorization header
- ✅ Handles 401 responses by clearing token

## How to Test

### 1. Login and Confirm Token Exists
```powershell
# After logging in via frontend, check browser console:
# Should see: [AUTH] Login successful, token received
# Should see: [AUTH] Token stored in localStorage and apiClient
# Should see: [AUTH] /me call successful, user: {...}
```

**Check localStorage:**
- Open browser DevTools → Application → Local Storage
- Should see `token` key with JWT value

### 2. Call /me from Frontend
After login, the app automatically calls `/me`. Check:
- Browser console should show: `[API] GET http://127.0.0.1:8000/me`
- Should show: `hasToken: true`, `hasAuthHeader: true`
- Should return 200 with user data

### 3. Enter /dashboard
After successful login:
- Should navigate to `/dashboard`
- ProtectedRoute should verify token and allow access
- Dashboard should load with user data

### 4. Refresh Page and Remain Logged In
1. After logging in, refresh the page (F5)
2. App should:
   - Find token in localStorage
   - Call `/me` to validate
   - Set user state
   - Allow access to `/dashboard` without re-login

### 5. Test Invalid Token
1. Manually set invalid token: `localStorage.setItem("token", "invalid")`
2. Refresh page
3. App should:
   - Try to validate token
   - Get 401 from `/me`
   - Clear token
   - Redirect to `/login`

### 6. Test Debug Endpoint
```powershell
# Get token from localStorage (browser console):
# const token = localStorage.getItem("token");

# Then call debug endpoint:
$headers = @{
    "Authorization" = "Bearer <your_token_here>"
}
Invoke-WebRequest -Uri "http://127.0.0.1:8000/debug/auth" -Headers $headers | ConvertFrom-Json | Format-List
```

**Expected Response:**
```
authorization_header_present : True
token_present                 : True
token_valid                   : True
token_decoded                 : @{sub=1; exp=...}
token_subject                 : 1
```

## Files Changed

### Backend (1 file):
- ✅ `backend/app/main.py` - Added `/debug/auth` endpoint, improved CORS

### Frontend (3 files):
- ✅ `frontend/src/App.jsx` - Fixed ProtectedRoute, handleAuthSuccess, token validation
- ✅ `frontend/src/api.js` - Added DEV logging
- ✅ `frontend/src/pages/AuthPage.jsx` - Added console logs

## Key Fixes

1. **ProtectedRoute now verifies token** - Calls `/me` to ensure token is valid
2. **Token synchronization** - `setToken()` ensures apiClient has token before API calls
3. **Navigation fixed** - Always goes to `/dashboard` (no role-based routing)
4. **Token persistence** - Validates token on app mount, sets user state
5. **Error handling** - Clears invalid tokens and redirects to login
6. **Debugging tools** - Console logs and debug endpoint for troubleshooting

## Testing Checklist

- [ ] Login shows "Login Successful" and navigates to `/dashboard`
- [ ] Token exists in localStorage after login
- [ ] `/me` endpoint returns 200 with user data
- [ ] Dashboard loads successfully after login
- [ ] Refresh page → user remains logged in
- [ ] Invalid token → redirects to login
- [ ] ProtectedRoute shows "Verifying authentication..." while checking
- [ ] Browser console shows auth flow logs
- [ ] DEV debug banner shows token/user state (if in dev mode)

## Troubleshooting

### Issue: "Login Successful" but still on login page
**Check:**
1. Browser console for errors
2. Network tab - is `/me` call successful?
3. Is token in localStorage?
4. Check `handleAuthSuccess` is being called

**Fix:**
- Ensure `onAuth` callback is passed to Login component
- Check token is being stored: `localStorage.getItem("token")`

### Issue: ProtectedRoute always redirects to login
**Check:**
1. Is token in localStorage?
2. Does `/me` return 401?
3. Browser console for ProtectedRoute logs

**Fix:**
- Check token format: should be JWT string
- Verify backend `/me` endpoint works with token
- Check CORS allows Authorization header

### Issue: API calls return 401
**Check:**
1. Is Authorization header being sent? (Network tab)
2. Is token format correct? (`Bearer <token>`)
3. Is token expired?

**Fix:**
- Verify `apiClient` is used everywhere (not raw fetch)
- Check token is set: `setToken(token)` before API calls
- Check backend JWT_SECRET matches
