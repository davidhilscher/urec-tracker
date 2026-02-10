#!/bin/bash

# Quick Start Script for UREC Capacity Tracker
# This script sets up the development environment

set -e  # Exit on error

echo "=========================================="
echo "UREC Capacity Tracker - Quick Start"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"
else
    echo -e "${RED}✗${NC} Python 3 not found. Please install Python 3.11 or higher."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${GREEN}✓${NC} Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓${NC} Virtual environment activated"

# Install backend dependencies
echo ""
echo "Installing backend dependencies..."
cd backend
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo -e "${GREEN}✓${NC} Backend dependencies installed"
cd ..

# Check for .env file
echo ""
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}⚠${NC} No .env file found"
    echo "Copying .env.template to backend/.env..."
    cp .env.template backend/.env
    echo -e "${YELLOW}⚠${NC} Please edit backend/.env with your AWS credentials"
else
    echo -e "${GREEN}✓${NC} .env file exists"
fi

# Check AWS credentials
echo ""
echo "Checking AWS credentials..."
if command -v aws &> /dev/null; then
    if aws sts get-caller-identity &> /dev/null; then
        echo -e "${GREEN}✓${NC} AWS credentials configured"
    else
        echo -e "${YELLOW}⚠${NC} AWS credentials not configured or invalid"
        echo "Run: aws configure"
    fi
else
    echo -e "${YELLOW}⚠${NC} AWS CLI not installed"
    echo "Install from: https://aws.amazon.com/cli/"
fi

# Offer to initialize database
echo ""
read -p "Do you want to initialize the DynamoDB database? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Initializing database..."
    python3 scripts/init_database.py
fi

# Print next steps
echo ""
echo "=========================================="
echo -e "${GREEN}✓${NC} Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Start the backend:"
echo "   cd backend"
echo "   uvicorn main:app --reload --port 8000"
echo ""
echo "2. In a new terminal, serve the frontend:"
echo "   cd frontend"
echo "   python3 -m http.server 8080"
echo ""
echo "3. Open your browser:"
echo "   http://localhost:8080"
echo ""
echo "For more information, see docs/SETUP.md"
echo ""
