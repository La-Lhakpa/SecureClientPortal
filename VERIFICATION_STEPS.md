# Verification Steps - Login Fixes & Registration Validation

## Prerequisites
- Backend running on `http://127.0.0.1:8000`
- Frontend running on `http://localhost:5173`
- PostgreSQL database running and accessible

## Step 1: Register a User (Valid Credentials)

### Via Frontend:
1. Open `http://localhost:5173/register`
2. Enter email: `user@example.com`
3. Enter password: `testpassword123`
4. Enter confirm password: `testpassword123`
5. Click "Create account"

### Via API (PowerShell):
```powershell
$body = @{
    email = "user@example.com"
    password = "testpassword123"
    confirm_password = "testpassword123"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://127.0.0.1:8000/auth/register" -Method POST -Body $body -ContentType "application/json"
```

**Expected Result:**
- Status: 201 Created
- Response contains user data (id, email, created_at)
- Backend logs show: `[REGISTER] SUCCESS: User registered`

## Step 2: Confirm DB Row Exists

### Check User Count:
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/debug/dbinfo" | ConvertFrom-Json | Select-Object users_count
```

**Expected:** `users_count` should be 1 or higher

### Check Backend Logs:
Look for:
```
[REGISTER] VERIFIED: User exists in database with ID 1, Email: user@example.com
```

## Step 3: Login Succeeds Using Same Email/Password

### Via Frontend:
1. Go to `http://localhost:5173/login`
2. Enter email: `user@example.com`
3. Enter password: `testpassword123`
4. Click "Login"

### Via API (PowerShell):
```powershell
$body = @{
    email = "user@example.com"
    password = "testpassword123"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://127.0.0.1:8000/auth/login" -Method POST -Body $body -ContentType "application/json"
```

**Expected Result:**
- Status: 200 OK
- Response contains `access_token` and `user` object
- Backend logs show:
  ```
  [LOGIN] User found - ID: 1, Email: user@example.com
  [LOGIN] Stored hash scheme: $2b
  [LOGIN] Password verification result: True
  [LOGIN] SUCCESS: Login successful
  ```

## Step 4: Try Mismatched Confirm Password → Fails

### Via Frontend:
1. Go to `http://localhost:5173/register`
2. Enter email: `user2@example.com`
3. Enter password: `testpassword123`
4. Enter confirm password: `differentpassword`
5. Click "Create account"

**Expected Result:**
- Frontend shows: "Passwords do not match" (client-side validation)
- If API is called, backend returns: 422 Unprocessable Entity
- Error message: "Passwords do not match"

### Via API (PowerShell):
```powershell
$body = @{
    email = "user2@example.com"
    password = "testpassword123"
    confirm_password = "differentpassword"
} | ConvertTo-Json

try {
    Invoke-WebRequest -Uri "http://127.0.0.1:8000/auth/register" -Method POST -Body $body -ContentType "application/json"
} catch {
    $_.Exception.Response.StatusCode.value__
    $_.ErrorDetails.Message
}
```

**Expected:** 422 with "Passwords do not match"

## Step 5: Try Invalid Email (Bad Format) → Fails

### Via Frontend:
1. Go to `http://localhost:5173/register`
2. Enter email: `notanemail`
3. Enter password: `testpassword123`
4. Enter confirm password: `testpassword123`
5. Click "Create account"

**Expected Result:**
- Frontend shows: "Enter a valid email" (client-side validation)
- If API is called, backend returns: 422 Unprocessable Entity
- Error message: "Invalid email format"

### Via API (PowerShell):
```powershell
$body = @{
    email = "notanemail"
    password = "testpassword123"
    confirm_password = "testpassword123"
} | ConvertTo-Json

try {
    Invoke-WebRequest -Uri "http://127.0.0.1:8000/auth/register" -Method POST -Body $body -ContentType "application/json"
} catch {
    $_.Exception.Response.StatusCode.value__
    $_.ErrorDetails.Message
}
```

**Expected:** 422 with "Invalid email format"

## Step 6: Try Non-Deliverable Domain → Fails

### Via Frontend:
1. Go to `http://localhost:5173/register`
2. Enter email: `user@nonexistentdomain12345xyz.com`
3. Enter password: `testpassword123`
4. Enter confirm password: `testpassword123`
5. Click "Create account"

**Expected Result:**
- Backend checks MX record (may take 2-5 seconds)
- Returns: 422 Unprocessable Entity
- Error message: "Email domain is not deliverable"

### Via API (PowerShell):
```powershell
$body = @{
    email = "user@nonexistentdomain12345xyz.com"
    password = "testpassword123"
    confirm_password = "testpassword123"
} | ConvertTo-Json

try {
    Invoke-WebRequest -Uri "http://127.0.0.1:8000/auth/register" -Method POST -Body $body -ContentType "application/json"
} catch {
    $_.Exception.Response.StatusCode.value__
    $_.ErrorDetails.Message
}
```

**Expected:** 422 with "Email domain is not deliverable"

**Note:** This test may take a few seconds as it performs DNS/MX lookup.

## Step 7: Test Email Normalization

### Test Case: Mixed Case Email
1. Register with: `Test@EXAMPLE.COM`
2. Login with: `test@example.com`

**Expected:** Both should work (email is normalized to lowercase)

### Via API:
```powershell
# Register with mixed case
$body = @{
    email = "Test@EXAMPLE.COM"
    password = "testpassword123"
    confirm_password = "testpassword123"
} | ConvertTo-Json
Invoke-WebRequest -Uri "http://127.0.0.1:8000/auth/register" -Method POST -Body $body -ContentType "application/json"

# Login with lowercase (should work)
$body = @{
    email = "test@example.com"
    password = "testpassword123"
} | ConvertTo-Json
Invoke-WebRequest -Uri "http://127.0.0.1:8000/auth/login" -Method POST -Body $body -ContentType "application/json"
```

**Expected:** Both succeed (email normalized in both cases)

## Step 8: Test Short Password → Fails

### Via Frontend:
1. Go to `http://localhost:5173/register`
2. Enter email: `user3@example.com`
3. Enter password: `short`
4. Enter confirm password: `short`
5. Click "Create account"

**Expected Result:**
- Frontend shows: "Use at least 8 characters" (client-side validation)
- If API is called, backend returns: 422 Unprocessable Entity
- Error message: "Password must be at least 8 characters long"

### Via API (PowerShell):
```powershell
$body = @{
    email = "user3@example.com"
    password = "short"
    confirm_password = "short"
} | ConvertTo-Json

try {
    Invoke-WebRequest -Uri "http://127.0.0.1:8000/auth/register" -Method POST -Body $body -ContentType "application/json"
} catch {
    $_.Exception.Response.StatusCode.value__
    $_.ErrorDetails.Message
}
```

**Expected:** 422 with "Password must be at least 8 characters long"

## Summary Checklist

- [ ] Register with valid credentials → Success (201)
- [ ] User appears in database (check `/debug/dbinfo`)
- [ ] Login with same credentials → Success (200) with JWT token
- [ ] Mismatched confirm password → 422 "Passwords do not match"
- [ ] Invalid email format → 422 "Invalid email format"
- [ ] Non-deliverable domain → 422 "Email domain is not deliverable"
- [ ] Short password (< 8 chars) → 422 "Password must be at least 8 characters"
- [ ] Email normalization works (mixed case → lowercase)
- [ ] Backend logs show hash scheme ($2b) and verification result

## Files Changed Summary

### Backend (7 files):
1. `backend/app/core/__init__.py` - New
2. `backend/app/core/security.py` - New (centralized security)
3. `backend/app/schemas.py` - Added confirm_password + validators
4. `backend/app/routers/auth.py` - Email normalization + deliverability check
5. `backend/app/dependencies.py` - Updated import
6. `backend/app/main.py` - Updated import
7. `backend/app/cli.py` - Updated import

### Frontend (2 files):
1. `frontend/src/pages/AuthPage.jsx` - Added confirm_password field
2. `frontend/src/api.js` - Improved error message extraction
