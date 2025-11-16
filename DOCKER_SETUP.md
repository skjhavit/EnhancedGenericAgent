# 🐳 Running with Docker PostgreSQL

Since you're using Docker for PostgreSQL, here's the quick setup:

## Start PostgreSQL in Docker

```bash
# Start PostgreSQL container
docker run --name agent_postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=agent_platform \
  -p 5432:5432 \
  -d postgres:14

# Verify it's running
docker ps | grep postgres
```

## Initialize Database Tables

```bash
cd backend
source venv/bin/activate
python init_db.py
```

## Start the Platform

**Terminal 1 - Backend:**
```bash
./start-backend.sh
```

**Terminal 2 - Frontend:**
```bash
./start-frontend.sh
```

## Access

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs

## Useful Docker Commands

```bash
# Stop PostgreSQL
docker stop agent_postgres

# Start existing container
docker start agent_postgres

# View logs
docker logs agent_postgres

# Connect to database
docker exec -it agent_postgres psql -U postgres -d agent_platform

# Remove container (if needed)
docker rm -f agent_postgres
```

## Database Connection String

The platform uses:
```
postgresql://postgres:postgres@localhost:5432/agent_platform
```

This is already configured in `.env.example`
