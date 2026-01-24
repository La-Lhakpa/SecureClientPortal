# Testing Checklist - Auth Flow Fixes

## Prerequisites
- Backend running: `uvicorn app.main:app --reload --port 8000`
- Frontend running: `npm run dev`
- Browser DevTools open (Console + Network tabs)

## Test 1: Login and Confirm Token Exists

### Steps:
1. Go to `http://localhost:5173/login`
2. Enter valid credentials
3. Click "Login"

### Expected Results:
- ✅ Browser console shows:
  ```
  [AUTH] Login successful, token received, length: 200+
  [AUTH] Token stored in localStorage and apiClient
  [API] GET http://127.0.0.1:8000/me hasToken: true, hasAuthHeader: true
  [AUTH] /me call successful, user: {id: 1, email: "..."}
  ```
- ✅ Navigates to `/dashboard`
- ✅ Check localStorage: `localStorage.getItem("token")` returns JWT string

### Verification:
```javascript
// In browser console:
localStorage.getItem("token")  // Should return JWT token
```

## Test 2: Call /me from Frontend

### Steps:
After successful login, check Network tab:
1. Find the `/me` request
2. Check Request Headers: Should include `Authorization: Bearer <token>`
3. Check Response: Should be 200 OK with user data

### Expected Results:
- ✅ Request includes `Authorization: Bearer <token>` header
- ✅ Response status: 200
- ✅ Response body: `{id: 1, email: "...", created_at: "..."}`

### Verification:
```javascript
// In browser console:
fetch("http://127.0.0.1:8000/me", {
  headers: {
    "Authorization": `Bearer ${localStorage.getItem("token")}`
  }
}).then(r => r.json()).then(console.log)
```

## Test 3: Enter /dashboard

### Steps:
1. After login, should automatically navigate to `/dashboard`
2. Dashboard should load

### Expected Results:
- ✅ URL changes to `/dashboard`
- ✅ Dashboard page loads (not login page)
- ✅ Shows "File Sharing Dashboard" heading
- ✅ Shows user email in welcome message
- ✅ DEV debug banner (top right) shows:
  - Token: Present (200+ chars)
  - User: user@example.com

### Verification:
- Check browser URL: should be `http://localhost:5173/dashboard`
- Check page content: should show dashboard, not login form

## Test 4: Refresh Page and Remain Logged In

### Steps:
1. After logging in and reaching dashboard
2. Press F5 to refresh page
3. Observe behavior

### Expected Results:
- ✅ Page refreshes
- ✅ Still on `/dashboard` (not redirected to login)
- ✅ User data loads automatically
- ✅ Browser console shows:
  ```
  [App] Found token on mount, validating...
  [API] GET http://127.0.0.1:8000/me
  [App] Token valid, user loaded: {...}
  [ProtectedRoute] Token found, verifying with /me endpoint
  [ProtectedRoute] Token valid, user: {...}
  ```

### Verification:
- URL remains `/dashboard` after refresh
- Dashboard content loads (not login page)
- User email still visible

## Test 5: Try Invalid Token

### Steps:
1. While logged in, open browser console
2. Set invalid token: `localStorage.setItem("token", "invalid")`
3. Refresh page (F5)

### Expected Results:
- ✅ App tries to validate token
- ✅ `/me` returns 401
- ✅ Token is cleared from localStorage
- ✅ Redirects to `/login`
- ✅ Browser console shows:
  ```
  [App] Found token on mount, validating...
  [API] Error [401]: Invalid or expired token
  [App] Token validation failed
  ```

### Verification:
- URL changes to `/login`
- `localStorage.getItem("token")` returns `null`
- Login form is displayed

## Test 6: Test Debug Endpoint

### Steps:
1. Login to get a valid token
2. In browser console, get token: `const token = localStorage.getItem("token")`
3. Call debug endpoint (via browser or PowerShell)

### Via Browser Console:
```javascript
fetch("http://127.0.0.1:8000/debug/auth", {
  headers: {
    "Authorization": `Bearer ${localStorage.getItem("token")}`
  }
}).then(r => r.json()).then(console.log)
```

### Via PowerShell:
```powershell
$token = "your_jwt_token_here"
$headers = @{
    "Authorization" = "Bearer $token"
}
Invoke-WebRequest -Uri "http://127.0.0.1:8000/debug/auth" -Headers $headers | ConvertFrom-Json | Format-List
```

### Expected Results:
```json
{
  "authorization_header_present": true,
  "token_present": true,
  "token_valid": true,
  "token_decoded": {
    "sub": "1,
    "exp": 1234567890
  },
  "token_subject": "1"
}
```

## Test 7: ProtectedRoute Verification

### Steps:
1. Logout (or clear token)
2. Manually navigate to `/dashboard` in browser
3. Observe behavior

### Expected Results:
- ✅ ProtectedRoute detects no token
- ✅ Shows "Verifying authentication..." briefly
- ✅ Redirects to `/login`
- ✅ Browser console shows:
  ```
  [ProtectedRoute] No token found, redirecting to login
  ```

### Verification:
- URL changes to `/login`
- Login form is displayed

## Test 8: API Calls Include Authorization Header

### Steps:
1. Login and navigate to dashboard
2. Open Network tab in DevTools
3. Perform actions that trigger API calls:
   - Dashboard loads (calls `/users`, `/files/sent`, `/files/received`)
   - Send a file (calls `/files/send`)

### Expected Results:
- ✅ All API requests include `Authorization: Bearer <token>` header
- ✅ Requests return 200 OK (not 401)
- ✅ Browser console shows for each request:
  ```
  [API] GET http://127.0.0.1:8000/users hasToken: true, hasAuthHeader: true
  ```

### Verification:
- Network tab → Select any API request → Headers → Request Headers
- Should see: `Authorization: Bearer eyJhbGci...`

## Common Issues & Solutions

### Issue: Token exists but /me returns 401
**Check:**
1. Is token format correct? (should be JWT string)
2. Is token expired? (check `token_decoded.exp` in debug endpoint)
3. Does backend JWT_SECRET match?

**Fix:**
- Check backend logs for JWT decode errors
- Verify token in `/debug/auth` endpoint
- Try logging in again to get fresh token

### Issue: ProtectedRoute always shows "Verifying..."
**Check:**
1. Is `/me` call completing? (Network tab)
2. Is there an error in console?

**Fix:**
- Check Network tab for `/me` request
- Look for errors in console
- Verify backend is running and accessible

### Issue: Dashboard shows "Loading user data..." forever
**Check:**
1. Is user prop being passed from App?
2. Is App's useEffect setting user state?

**Fix:**
- Check App component logs
- Verify `/me` call succeeds
- Check user state in React DevTools

## Files Changed Summary

### Backend (1 file):
- `backend/app/main.py` - Added `/debug/auth` endpoint, improved CORS

### Frontend (4 files):
- `frontend/src/App.jsx` - Fixed ProtectedRoute, handleAuthSuccess, token validation, added DEV debug banner
- `frontend/src/api.js` - Added DEV logging for requests
- `frontend/src/pages/AuthPage.jsx` - Added console logs
- `frontend/src/pages/Dashboard.jsx` - Added user null check, improved error handling
