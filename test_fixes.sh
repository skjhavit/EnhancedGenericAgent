#!/bin/bash
# Quick test to verify the fixes work

echo "🔧 Testing fixes..."
echo ""

# Test backend
echo "1️⃣ Testing backend import..."
cd backend

if python -c "from agents.state import AgentState; from agents.graph import agent_graph" 2>/dev/null; then
    echo "✅ Backend imports work!"
else
    echo "❌ Backend still has import errors"
    echo "Run: cd backend && source venv/bin/activate && pip install -r requirements.txt"
fi

echo ""

# Test frontend
echo "2️⃣ Testing frontend dependencies..."
cd ../frontend

if [ -d "node_modules" ]; then
    if [ -d "node_modules/ajv" ]; then
        ajv_version=$(node -p "require('./node_modules/ajv/package.json').version" 2>/dev/null)
        if [[ $ajv_version == 6.* ]]; then
            echo "✅ Frontend has correct ajv version: $ajv_version"
        else
            echo "❌ Frontend has wrong ajv version: $ajv_version (should be 6.x)"
            echo "Run: cd frontend && npm run reinstall"
        fi
    else
        echo "❌ ajv not installed"
        echo "Run: cd frontend && npm run reinstall"
    fi
else
    echo "⚠️  node_modules not found"
    echo "Run: cd frontend && npm install --legacy-peer-deps"
fi

echo ""
echo "Done!"
