# URGENT FIX - Run These Commands

## Fix Frontend (ajv error) - DO THIS FIRST

```bash
# Pull latest changes
git pull

cd frontend

# Delete everything and reinstall
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps

# Should work now
npm start
```

**What was fixed:**
- Removed conflicting `overrides` and `resolutions` sections
- ajv@6.12.6 is now a direct dependency (no conflicts)

## Fix Backend (Database Connection)

The backend error `ConnectionRefusedError` means PostgreSQL isn't running.

**Option 1: Use Docker Compose (RECOMMENDED)**
```bash
# Start just the database services
docker compose up postgres chromadb -d

# Then run backend manually
cd backend
source venv/bin/activate
uvicorn api.main:socket_app --host 0.0.0.0 --port 8000 --reload
```

**Option 2: Full Docker Build**
```bash
# Build with no cache
docker compose build --no-cache

# Start everything
docker compose up
```

**Option 3: Local PostgreSQL**
If you have PostgreSQL installed locally:
```bash
# Start PostgreSQL (example for macOS)
brew services start postgresql

# Update .env with your local database
DATABASE_URL=postgresql+asyncpg://YOUR_USER:YOUR_PASSWORD@localhost:5432/agent_platform
```

## What Was Wrong

**Frontend:**
- ❌ Had ajv as direct dependency AND in overrides (conflict)
- ✅ Removed overrides, kept only direct dependency

**Backend:**
- ✅ Fixed `add_messages` import (created custom reducer)
- ⚠️ Database not running (need to start PostgreSQL)

## After Running These Commands

- ✅ No more `npm error code EOVERRIDE`
- ✅ No more `ImportError: cannot import name 'add_messages'`
- ✅ No more `ConnectionRefusedError` (once database is running)
