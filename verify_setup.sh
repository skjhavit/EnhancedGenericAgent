#!/bin/bash
# Quick verification script for EnhancedGenericAgent setup

# Don't exit on error - we want to check everything
set +e

echo "🔍 EnhancedGenericAgent Build Verification"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is available
echo "📦 Checking Docker availability..."
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker is installed: $(docker --version)"
else
    echo -e "${YELLOW}⚠${NC} Docker is not installed (required for Docker builds)"
fi

if command -v docker compose &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker Compose is available"
else
    echo -e "${YELLOW}⚠${NC} Docker Compose is not available (required for Docker builds)"
fi

echo ""

# Check critical files exist
echo "📄 Checking critical files..."
files=(
    "docker-compose.yml"
    "backend/Dockerfile"
    "backend/requirements.txt"
    "backend/agents/graph.py"
    "frontend/Dockerfile"
    "frontend/package.json"
    ".env.example"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (missing)"
    fi
done

echo ""

# Check .env file
echo "🔐 Checking environment configuration..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"

    # Check for required variables
    required_vars=("DATABASE_URL" "SECRET_KEY")
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env; then
            echo -e "${GREEN}✓${NC} $var is set"
        else
            echo -e "${YELLOW}⚠${NC} $var may not be set (check .env file)"
        fi
    done
else
    echo -e "${YELLOW}⚠${NC} .env file not found"
    echo "   Copy .env.example to .env and configure it:"
    echo "   cp .env.example .env"
fi

echo ""

# Check Python syntax for critical backend files
echo "🐍 Checking Python syntax..."
if command -v python &> /dev/null || command -v python3 &> /dev/null; then
    PYTHON_CMD=$(command -v python3 || command -v python)

    python_files=(
        "backend/agents/graph.py"
        "backend/agents/nodes.py"
        "backend/agents/state.py"
        "backend/api/main.py"
    )

    all_valid=true
    for file in "${python_files[@]}"; do
        if $PYTHON_CMD -m py_compile "$file" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} $file"
        else
            echo -e "${RED}✗${NC} $file (syntax error)"
            all_valid=false
        fi
    done

    if [ "$all_valid" = true ]; then
        echo -e "${GREEN}✓${NC} All Python files have valid syntax"
    fi
else
    echo -e "${YELLOW}⚠${NC} Python not found, skipping syntax check"
fi

echo ""

# Check for common issues in requirements.txt
echo "📦 Checking backend dependencies..."
if grep -q "langgraph-checkpoint" backend/requirements.txt; then
    echo -e "${GREEN}✓${NC} langgraph-checkpoint is in requirements.txt"
else
    echo -e "${RED}✗${NC} langgraph-checkpoint missing from requirements.txt"
fi

if grep -q "langchain-core>=0.3.0,<0.4.0" backend/requirements.txt; then
    echo -e "${GREEN}✓${NC} langchain-core has version constraints"
else
    echo -e "${YELLOW}⚠${NC} langchain-core version constraints may be missing"
fi

echo ""

# Check for LangGraph import issues
echo "🔧 Checking for fixed import issues..."
if grep -q "langgraph.checkpoint.postgres" backend/agents/graph.py; then
    echo -e "${RED}✗${NC} Old PostgresSaver import found (should be removed)"
else
    echo -e "${GREEN}✓${NC} No PostgresSaver import (correct)"
fi

if grep -q "langgraph.checkpoint.memory" backend/agents/graph.py; then
    echo -e "${GREEN}✓${NC} MemorySaver import found (correct)"
else
    echo -e "${YELLOW}⚠${NC} MemorySaver import not found"
fi

echo ""

# Check frontend package.json
echo "📦 Checking frontend dependencies..."
if grep -q '"ajv"' frontend/package.json; then
    ajv_version=$(grep -o '"ajv": *"[^"]*"' frontend/package.json | cut -d'"' -f4)
    if [[ $ajv_version == ^6* ]]; then
        echo -e "${GREEN}✓${NC} ajv version is v6 (correct for react-scripts 5.0.1)"
    else
        echo -e "${YELLOW}⚠${NC} ajv version is $ajv_version (should be ^6.12.6)"
    fi
fi

if grep -q '"typescript"' frontend/package.json; then
    ts_version=$(grep -o '"typescript": *"[^"]*"' frontend/package.json | cut -d'"' -f4)
    if [[ $ts_version == ^4* ]]; then
        echo -e "${GREEN}✓${NC} TypeScript version is v4 (correct)"
    else
        echo -e "${YELLOW}⚠${NC} TypeScript version is $ts_version (should be ^4.9.5)"
    fi
fi

echo ""
echo "=========================================="
echo "🎯 Verification Summary"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Ensure .env file is configured (copy from .env.example)"
echo "2. Build containers: docker compose build --no-cache"
echo "3. Start services: docker compose up"
echo "4. Initialize database: docker compose exec backend python init_db.py"
echo "5. Access frontend: http://localhost:3000"
echo ""
echo "For detailed instructions, see BUILD_VERIFICATION.md"
echo ""
