#!/bin/bash
# Setup Script - Initialize the CDP project environment

set -e  # Exit on error

echo "=========================================="
echo "CDP Project Setup"
echo "=========================================="

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install dev dependencies
echo "Installing development dependencies..."
pip install pytest pytest-cov httpx


# Test configuration
echo "Testing configuration..."
python test_config.py

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Start Docker services: cd docker && docker-compose up -d"
echo "3. Run tests: pytest"
echo "4. Start services:"
echo "   - Producer: python run_producer.py"
echo "   - Batch Job: python run_batch.py"
echo "   - API: python run_api.py"
echo ""
