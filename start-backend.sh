#!/bin/bash

# Start Backend Server Script

echo "🚀 Starting Agent Platform Backend..."
echo ""

# Navigate to backend directory
cd "$(dirname "$0")/backend"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if database is accessible
echo "🔍 Checking database connection..."
python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('postgresql://postgres:postgres@localhost:5432/agent_platform').close())" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Cannot connect to database."
    echo "   Make sure PostgreSQL is running and the database exists."
    echo "   Run: createdb agent_platform"
    echo ""
fi

# Start the server
echo "🎯 Starting FastAPI server..."
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""

uvicorn api.main:socket_app --reload --host 0.0.0.0 --port 8000
