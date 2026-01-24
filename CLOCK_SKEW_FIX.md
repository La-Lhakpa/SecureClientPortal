# Google Token Clock Skew Fix

## Issue
Error: "Token used too early, 1769234114 < 1769234115. Check that your computer's clock is set correctly."

## Root Cause
This error occurs when there's a time difference (clock skew) between:
- Your computer's system clock
- Google's servers  
- Your backend server

The `google-auth` library is very strict about token timing and rejects tokens if the "issued at" time (iat) is in the future relative to the server's current time.

## Fix Applied

### Backend Code Change
- ✅ Added `clock_skew_in_seconds=60` parameter to `verify_oauth2_token()`
- ✅ This allows up to 60 seconds of clock difference (recommended by Google)
- ✅ Added specific error handling for "Token used too early" errors
- ✅ Provides helpful error message if clock is still out of sync

## Additional Steps Required

### 1. Sync Your System Clock (Windows)

**Option A: Automatic Sync (Recommended)**
1. Right-click on the clock in the taskbar
2. Select "Adjust date/time"
3. Toggle "Set time automatically" to ON
4. Toggle "Set time zone automatically" to ON
5. Click "Sync now" if available

**Option B: Manual Sync via Command (Run as Administrator)**
```powershell
# Sync with Windows time server
w32tm /config /manualpeerlist:"time.windows.com" /syncfromflags:manual /reliable:YES /update
w32tm /resync

# Verify sync
w32tm /query /status
```

### 2. Verify Clock Sync
```powershell
# Check current time
Get-Date

# Check time sync status
w32tm /query /status
```

### 3. Restart Backend Server
After syncing your clock, restart the backend:
```powershell
# Stop backend (Ctrl+C)
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Why This Happens

1. **System clock drift**: Computer clocks can drift over time
2. **Time zone issues**: Incorrect time zone settings
3. **Network latency**: Small delays in token transmission
4. **Virtual machines**: VMs sometimes have clock sync issues
5. **Battery issues**: Laptops with dead CMOS batteries can have clock issues

## Testing

After syncing your clock and restarting the backend:

1. Try Google Sign-In again
2. The 60-second tolerance should handle most clock differences
3. If you still get clock errors, your system clock may need more adjustment

## Long-term Solution

- ✅ Enable automatic time sync on your system (Windows does this by default)
- ✅ Use NTP (Network Time Protocol) for accurate time
- ✅ Consider using a time sync service for production servers
- ✅ The 60-second tolerance in code handles minor sync issues

## Current Status

- ✅ Code fix applied: 60-second clock skew tolerance
- ⚠️ System clock sync required: Follow steps above
- ⚠️ Backend restart required: After clock sync
