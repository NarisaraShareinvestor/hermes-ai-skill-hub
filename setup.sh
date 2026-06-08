#!/bin/bash

# Hermes AI Skill Hub - Setup Script
# ใช้: bash setup.sh

set -e

echo "=========================================="
echo "🚀 Hermes AI Skill Hub - Setup"
echo "=========================================="
echo ""

# Check Python
echo "✅ Checking Python..."
python --version

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating Virtual Environment..."
    python -m venv .venv
fi

# Activate venv
echo "🔌 Activating Virtual Environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing Python Dependencies..."
if [ -f "backend/requirements.txt" ]; then
    pip install -q -r backend/requirements.txt
    echo "✅ Dependencies installed"
else
    echo "⚠️  requirements.txt not found"
fi

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql://hermes_user:hermes_password@localhost:5432/hermes_db

# Backend
BACKEND_URL=http://localhost:8000
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHANNEL_ID=-100123456789

# Claude API
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Environment
ENVIRONMENT=development
DEBUG=True
EOF
    echo "⚠️  Created .env with placeholder values"
    echo "   ⚠️  Please update with real values!"
fi

echo ""
echo "=========================================="
echo "📝 Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1️⃣  Update .env with real values:"
echo "    - DATABASE_URL: PostgreSQL connection"
echo "    - ANTHROPIC_API_KEY: Your Claude API key"
echo "    - TELEGRAM_BOT_TOKEN: Your Telegram bot token"
echo ""
echo "2️⃣  Initialize Database:"
echo "    python backend/init_db.py"
echo ""
echo "3️⃣  Run Backend Server:"
echo "    python -m uvicorn backend.main:app --reload"
echo ""
echo "4️⃣  In another terminal, run Frontend:"
echo "    python -m http.server 8080"
echo ""
echo "5️⃣  Open http://localhost:8080 in your browser"
echo ""
