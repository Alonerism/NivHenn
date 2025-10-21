#!/bin/bash
# Quick setup script for Real Estate Scout

set -e  # Exit on error

echo "======================================"
echo "Real Estate Scout - Quick Setup"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Check if version is 3.11 or higher
required_version="3.11"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "❌ Python 3.11+ required. You have $python_version"
    exit 1
fi
echo "✓ Python version OK"
echo ""

# Install dependencies
echo "Installing dependencies..."
if [ -f "pyproject.toml" ]; then
    echo "Using pyproject.toml..."
    pip install -e .
else
    echo "Using requirements.txt..."
    pip install -r requirements.txt
fi
echo "✓ Dependencies installed"
echo ""

# Setup .env file
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  ACTION REQUIRED: Edit .env file and add your API keys"
    echo "   - RAPIDAPI_KEY (get from https://rapidapi.com/)"
    echo "   - OPENAI_API_KEY (get from https://platform.openai.com/)"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Create output directory
if [ ! -d "out" ]; then
    mkdir out
    echo "✓ Created output directory: ./out"
else
    echo "✓ Output directory exists"
fi
echo ""

# Run verification
echo "Running setup verification..."
python3 verify_setup.py
verification_status=$?

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""

if [ $verification_status -eq 0 ]; then
    echo "✓ All checks passed!"
    echo ""
    echo "Next steps:"
    echo "1. Edit .env file with your API keys (if not done already)"
    echo "2. Test the CLI:"
    echo "   python -m src.cli analyze --location-id 41096 --size 3"
    echo ""
    echo "3. Or start the API server:"
    echo "   uvicorn src.main:app --reload"
    echo "   Then visit: http://localhost:8000/docs"
    echo ""
else
    echo "⚠️  Some checks failed. Please review the output above."
    echo ""
    echo "Common fixes:"
    echo "- Ensure .env file has valid API keys"
    echo "- Run: pip install -e ."
    echo ""
fi

echo "For detailed instructions, see SETUP.md"
echo ""
