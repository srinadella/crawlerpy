#!/bin/bash
# Start the Web Crawler application

set -e

echo "🚀 Starting Web Crawler Application..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt

# Initialize database
echo "🗄️  Initializing database..."
python3 init_db.py

# Create storage directories
mkdir -p storage/collections storage/logs

# Start FastAPI server
echo "✅ Starting API server on http://localhost:8000"
echo "📝 Sample login credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "Other users: editor/editor123, viewer/viewer123"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
