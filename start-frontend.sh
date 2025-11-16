#!/bin/bash

# Start Frontend Server Script

echo "🎨 Starting Agent Platform Frontend..."
echo ""

# Navigate to frontend directory
cd "$(dirname "$0")/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "❌ Node modules not found. Please run: npm install --legacy-peer-deps"
    exit 1
fi

# Start the development server
echo "🎯 Starting React development server..."
echo "   Frontend: http://localhost:3000"
echo ""

npm start
