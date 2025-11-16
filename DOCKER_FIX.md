# Docker Build Fix

## Issues Fixed

### Frontend Docker: `craco: not found`
**Problem:** craco is in devDependencies and wasn't being executed correctly
**Solution:** Changed CMD to use `npx craco start` instead of `npm start`

### Backend Docker: `exec /app/venv/bin/uvicorn: no such file or directory`
**Problem:** You're using an old cached Docker image with the old CMD
**Solution:** Rebuild with --no-cache to get the updated CMD

### Backend Manual: `ConnectionRefusedError`
**Problem:** PostgreSQL database isn't running
**Solution:** Start PostgreSQL first before running backend

## How to Fix

### Step 1: Pull Latest Changes
```bash
git pull
```

### Step 2: Rebuild Docker Images (REQUIRED)
```bash
# IMPORTANT: Use --no-cache to avoid using old cached layers
docker compose build --no-cache

# Start all services
docker compose up
```

### Step 3: Initialize Database
```bash
# In another terminal
docker compose exec backend python init_db.py
```

## Manual Setup (Alternative)

If you want to run manually instead of Docker:

### Backend Manual:
```bash
# Option 1: Start databases with Docker, run backend manually
docker compose up postgres chromadb -d

# Then run backend
cd backend
source venv/bin/activate
uvicorn api.main:socket_app --host 0.0.0.0 --port 8000 --reload

# Option 2: If you have PostgreSQL locally
brew services start postgresql  # macOS
# or
sudo service postgresql start   # Linux

# Update .env with local database URL
DATABASE_URL=postgresql+asyncpg://YOUR_USER:YOUR_PASSWORD@localhost:5432/agent_platform
```

### Frontend Manual:
```bash
cd frontend
npm install
npm start
```

## Verification

After rebuilding, check that all containers are running:
```bash
docker compose ps

# Should show:
# NAME                         STATUS
# postgres                     Up
# chromadb                     Up
# backend                      Up
# frontend                     Up
```

Check logs if any service fails:
```bash
docker compose logs backend
docker compose logs frontend
```

## Common Issues

**Q: Frontend still shows "craco: not found"**
A: You didn't rebuild with `--no-cache`. Run: `docker compose build --no-cache frontend`

**Q: Backend still shows "exec /app/venv/bin/uvicorn: no such file"**
A: You didn't rebuild with `--no-cache`. Run: `docker compose build --no-cache backend`

**Q: Backend shows "ConnectionRefusedError" when running manually**
A: PostgreSQL isn't running. Start it with `docker compose up postgres -d` or start your local PostgreSQL service

**Q: How do I verify the images are using the new Dockerfiles?**
A: Check the CMD in the running container:
```bash
docker compose exec backend sh -c 'ps aux'
# Should show: python -m uvicorn ...

docker compose exec frontend sh -c 'ps aux'
# Should show: npx craco start
```
