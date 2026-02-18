#!/bin/bash
# Run tests for the crawler application

echo "🧪 Running tests..."

source venv/bin/activate

# Run pytest on tests directory
python3 -m pytest tests/ -v --tb=short

echo "✅ Tests complete!"
