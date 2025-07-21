#!/bin/bash

# YouTube Trending Analyzer MVP - Deployment Script
# This script helps deploy the application to Render and Vercel

set -e  # Exit on any error

echo "🚀 YouTube Trending Analyzer MVP Deployment Script"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    log_error "Please run this script from the project root directory"
    exit 1
fi

# Check dependencies
log_info "Checking dependencies..."

if ! command -v git &> /dev/null; then
    log_error "Git is required but not installed"
    exit 1
fi

if ! command -v node &> /dev/null; then
    log_warning "Node.js not found - required for frontend development"
fi

if ! command -v python3 &> /dev/null; then
    log_warning "Python 3 not found - required for backend development"
fi

log_success "Dependencies check completed"

# Git repository setup
log_info "Setting up Git repository..."

if [ ! -d ".git" ]; then
    git init
    log_success "Git repository initialized"
else
    log_info "Git repository already exists"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    log_info "Creating .gitignore file..."
    cat > .gitignore << 'EOF'
# See existing .gitignore content in the repository
EOF
fi

# Check for environment files
log_info "Checking environment configuration..."

if [ ! -f "backend/.env" ]; then
    log_warning "Backend .env file not found. Copy backend/.env.example and configure it."
    cp backend/.env.example backend/.env 2>/dev/null || true
fi

if [ ! -f "frontend/.env.local" ]; then
    log_warning "Frontend .env.local file not found. Copy frontend/.env.local.example and configure it."
    cp frontend/.env.local.example frontend/.env.local 2>/dev/null || true
fi

# Backend checks
log_info "Checking backend setup..."

cd backend

if [ ! -f "requirements.txt" ]; then
    log_error "Backend requirements.txt not found"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    log_warning "No virtual environment found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    log_success "Virtual environment created and dependencies installed"
else
    log_info "Virtual environment exists"
fi

cd ..

# Frontend checks
log_info "Checking frontend setup..."

cd frontend

if [ ! -f "package.json" ]; then
    log_error "Frontend package.json not found"
    exit 1
fi

if [ ! -d "node_modules" ]; then
    log_warning "Node modules not installed. Installing..."
    npm install
    log_success "Node modules installed"
else
    log_info "Node modules already installed"
fi

cd ..

# Deployment instructions
echo ""
log_info "Deployment Instructions:"
echo "========================"

echo ""
echo "📦 BACKEND DEPLOYMENT (Render):"
echo "-------------------------------"
echo "1. Create a Render account at https://render.com"
echo "2. Connect your GitHub repository"
echo "3. Use the render.yaml file for blueprint deployment, or:"
echo "4. Create a new Web Service with these settings:"
echo "   - Runtime: Python 3"
echo "   - Build Command: cd backend && pip install -r requirements.txt"
echo "   - Start Command: cd backend && uvicorn app.main:app --host 0.0.0.0 --port \$PORT"
echo "   - Auto-Deploy: Yes"
echo ""
echo "5. Add these environment variables in Render dashboard:"
echo "   - YOUTUBE_API_KEY (get from Google Cloud Console)"
echo "   - GEMINI_API_KEY (get from Google AI Studio)"
echo "   - DATABASE_URL (will be auto-populated by Render PostgreSQL)"
echo "   - REDIS_URL (will be auto-populated by Render Redis)"
echo ""
echo "6. Add PostgreSQL and Redis add-ons in Render"

echo ""
echo "🌐 FRONTEND DEPLOYMENT (Vercel):"
echo "--------------------------------"
echo "1. Create a Vercel account at https://vercel.com"
echo "2. Connect your GitHub repository"
echo "3. Import the project and it will auto-detect Next.js"
echo "4. Set these environment variables:"
echo "   - NEXT_PUBLIC_API_BASE_URL=https://your-backend.onrender.com"
echo "   - NEXT_PUBLIC_ENVIRONMENT=production"
echo ""
echo "5. Update vercel.json with your actual backend URL"
echo "6. Deploy will happen automatically on git push"

echo ""
echo "🔑 REQUIRED API KEYS:"
echo "--------------------"
echo "1. YouTube Data API v3:"
echo "   - Go to https://console.cloud.google.com"
echo "   - Enable YouTube Data API v3"
echo "   - Create API key and restrict it to YouTube Data API"
echo ""
echo "2. Google Gemini API:"
echo "   - Go to https://makersuite.google.com/app/apikey"
echo "   - Create API key for Gemini Flash"

echo ""
echo "📋 PRE-DEPLOYMENT CHECKLIST:"
echo "----------------------------"
echo "□ API keys configured"
echo "□ Environment variables set"
echo "□ Database migrations ready"
echo "□ Frontend points to correct backend URL"
echo "□ CORS settings updated"
echo "□ Health check endpoints working"
echo "□ Budget monitoring configured"

echo ""
echo "🚀 READY TO DEPLOY:"
echo "------------------"
echo "1. Commit your changes: git add . && git commit -m 'Deploy MVP'"
echo "2. Push to GitHub: git push origin main"
echo "3. Deploy backend on Render"
echo "4. Deploy frontend on Vercel"
echo "5. Test the application"

log_success "Deployment preparation completed!"
echo ""
log_info "For detailed deployment instructions, see docs/DEPLOYMENT.md"