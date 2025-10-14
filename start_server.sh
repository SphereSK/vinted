#!/bin/bash

# Start Vinted Scraper Web UI
echo "🚀 Starting Vinted Scraper Dashboard..."
echo "📍 API: http://localhost:8000/api"
echo "🌐 Frontend: http://localhost:8000"
echo ""

# Activate virtual environment if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run FastAPI server
python3 -m app.api.main
