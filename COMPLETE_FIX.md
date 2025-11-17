# Complete Fix for CORS and Password Issues

## Issues Fixed

### 1. Password Validation Error ✅
**Error:** `ValueError: password cannot be longer than 72 bytes, truncate manually if necessary`

**Cause:** bcrypt (the password hashing library) has a hard limit of 72 bytes for passwords.

**Solution:** Added Pydantic validators to both `RegisterRequest` and `LoginRequest`:
- Minimum password length: 8 characters
- Maximum password length: 72 bytes (UTF-8 encoded)
- Clear error messages for users

### 2. Browser CORS Error ✅
**Error:** `Access to XMLHttpRequest at 'http://localhost:8000/api/auth/register' from origin 'http://localhost:3000' has been blocked by CORS policy`

**Cause:** When Socket.IO wraps the FastAPI app, the FastAPI middleware doesn't apply to all responses going through the wrapper.

**Solution:** Created `ASGICORSMiddleware` that wraps the entire `socket_app` at the ASGI level:
- Adds CORS headers to EVERY response
- Works below the Socket.IO wrapper
- Handles preflight OPTIONS requests
- Sets dynamic `Access-Control-Allow-Origin`

## How to Apply

### Step 1: Pull Latest Changes
```bash
git pull
```

### Step 2: Restart Backend

**If running manually:**
```bash
cd backend
source venv/bin/activate

# Kill the old process (Ctrl+C) then:
uvicorn api.main:socket_app --host 0.0.0.0 --port 8000 --reload
```

**If using Docker:**
```bash
docker compose restart backend
```

## Testing

### Test 1: Password Validation

**Try to register with a short password:**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "short"
  }'
```

**Expected Response:**
```json
{
  "detail": [
    {
      "type": "value_error",
      "msg": "Value error, Password must be at least 8 characters long"
    }
  ]
}
```

**Try to register with a valid password:**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "validpassword123",
    "full_name": "Test User"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Test 2: CORS Headers (curl)

```bash
curl -i -X OPTIONS http://localhost:8000/api/auth/register \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"
```

**Expected Headers:**
```
HTTP/1.1 200 OK
access-control-allow-origin: http://localhost:3000
access-control-allow-credentials: true
access-control-allow-methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
access-control-allow-headers: *
access-control-expose-headers: *
```

### Test 3: CORS in Browser

1. Open frontend at http://localhost:3000
2. Open DevTools Console (F12)
3. Try to register a new user
4. **Check Network tab:**
   - Should see OPTIONS preflight request with 200 status
   - Should see POST request with 201 status
   - Both should have CORS headers
5. **Check Console:**
   - NO CORS errors should appear
   - If you still see CORS errors, hard refresh (Ctrl+Shift+R) to clear cache

### Test 4: Clear Browser Cache

If you still see CORS errors after restarting backend:

**Chrome:**
1. Open DevTools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

**Firefox:**
1. Ctrl+Shift+R (Windows/Linux)
2. Cmd+Shift+R (Mac)

**Safari:**
1. Cmd+Option+E to empty cache
2. Cmd+R to reload

## What Changed

### backend/api/routes/auth.py
```python
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password length and encoding."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')

        # bcrypt has a 72 byte limit
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password is too long (max 72 bytes)')

        return v
```

### backend/api/main.py
```python
# New ASGI middleware that wraps the entire app
class ASGICORSMiddleware:
    """ASGI middleware to add CORS headers to all responses."""

    async def __call__(self, scope, receive, send):
        # Adds CORS headers to every response
        # Handles OPTIONS preflight requests
        # Works below Socket.IO wrapper
        ...

# Applied to socket_app (not just FastAPI app)
socket_app = ASGICORSMiddleware(socket_app)
```

## Verification Checklist

After applying the fix:

- [ ] Backend restarted successfully
- [ ] Can register with password 8+ characters
- [ ] Cannot register with password <8 characters
- [ ] Cannot register with very long password (>72 bytes)
- [ ] curl shows CORS headers
- [ ] Browser shows NO CORS errors (after hard refresh)
- [ ] Can register from frontend
- [ ] Can login from frontend
- [ ] WebSocket connects without errors

## Common Issues

**Q: Still getting "password cannot be longer than 72 bytes"**
A: The frontend might be sending a very long password. Check what the frontend is sending. The validation should now prevent this.

**Q: Still getting CORS errors in browser but curl works**
A: Your browser cached the old CORS response. Do a hard refresh (Ctrl+Shift+R). Also check that backend restarted successfully.

**Q: CORS works sometimes but not always**
A: Make sure you're using `uvicorn api.main:socket_app` (with socket_app, not just app). The ASGI middleware only applies to socket_app.

**Q: Getting "email already registered" error**
A: That email is already in the database. Use a different email or check the database:
```bash
docker compose exec backend python
>>> from core.database import get_session
>>> from core.models import User
>>> # Delete the test user if needed
```

## Frontend Changes Needed (Optional)

To improve UX, add password validation to the frontend:

**frontend/src/components/auth/Register.tsx:**
```typescript
// Add validation before submitting
if (password.length < 8) {
  setError('Password must be at least 8 characters');
  return;
}

if (new TextEncoder().encode(password).length > 72) {
  setError('Password is too long (max 72 bytes)');
  return;
}
```

This prevents the error from reaching the backend and provides immediate feedback.

---

**Summary:** Both password validation and CORS are now fixed. Pull changes and restart backend to apply!
