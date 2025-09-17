#!/bin/bash

# Quick setup script for Medi-Tour API
echo "🏥 Setting up Medi-Tour API..."

# Create virtual environment
echo "📦 Creating virtual environment..."
python -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo "⬇️  Installing dependencies..."
pip install -r requirements.txt

# Setup environment file
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env .env.example
    echo "⚠️  Please update .env with your actual database credentials"
fi

# Initialize database migrations
echo "🗄️  Initializing database migrations..."
alembic revision --autogenerate -m "Initial migration"

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your database credentials"
echo "2. Run: alembic upgrade head"
echo "3. Start the server: uvicorn app.main:app --reload"
echo ""
echo "📚 Documentation will be available at: http://localhost:8000/docs"