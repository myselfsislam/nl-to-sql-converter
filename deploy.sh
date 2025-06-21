#!/bin/bash

# NL to SQL Converter - Deployment Script
# This script helps deploy the application to various platforms

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to deploy to Streamlit Cloud
deploy_streamlit_cloud() {
    print_info "Deploying to Streamlit Community Cloud..."
    
    # Check if git repo exists
    if [ ! -d ".git" ]; then
        print_error "No git repository found. Please initialize git first:"
        echo "  git init"
        echo "  git add ."
        echo "  git commit -m 'Initial commit'"
        echo "  git remote add origin <your-repo-url>"
        echo "  git push -u origin main"
        return 1
    fi
    
    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        print_warning "You have uncommitted changes. Committing now..."
        git add .
        git commit -m "Deploy to Streamlit Cloud - $(date)"
    fi
    
    # Push to repository
    print_info "Pushing to GitHub..."
    git push
    
    print_status "Code pushed to GitHub!"
    print_info "Next steps:"
    echo "1. Go to https://share.streamlit.io/"
    echo "2. Connect your GitHub repository"
    echo "3. Select this repository and branch"
    echo "4. Set main file path to: app.py"
    echo "5. Add secrets if needed (HUGGINGFACE_TOKEN)"
    echo "6. Deploy!"
}

# Function to deploy to Vercel
deploy_vercel() {
    print_info "Deploying to Vercel..."
    
    # Check if vercel CLI is installed
    if ! command_exists vercel; then
        print_error "Vercel CLI not found. Installing..."
        npm install -g vercel || {
            print_error "Failed to install Vercel CLI. Please install Node.js first."
            return 1
        }
    fi
    
    # Check if vercel.json exists
    if [ ! -f "vercel.json" ]; then
        print_error "vercel.json not found. Make sure it exists in your project root."
        return 1
    fi
    
    # Deploy to Vercel
    print_info "Deploying to Vercel..."
    vercel --prod
    
    print_status "Deployed to Vercel successfully!"
}

# Function to prepare for Hugging Face Spaces
deploy_hf_spaces() {
    print_info "Preparing for Hugging Face Spaces deployment..."
    
    # Create app.py symlink or copy for HF Spaces
    if [ ! -f "app.py" ]; then
        print_error "app.py not found!"
        return 1
    fi
    
    # Create README for HF Spaces
    cat > README_HF.md << EOF
---
title: NL to SQL Converter
emoji: 🔍
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: 1.28.0
app_file: app.py
pinned: false
---

# Natural Language to SQL Converter

A powerful application that converts natural language questions into SQL queries using AI.

## Features
- 🤖 AI-powered SQL generation
- 📸 Schema extraction from images
- 💻 Interactive interface
- 📊 Real-time query execution

Check it out!
EOF
    
    print_status "HF Spaces files prepared!"
    print_info "Next steps:"
    echo "1. Go to https://huggingface.co/spaces"
    echo "2. Create a new Space"
    echo "3. Choose Streamlit SDK"
    echo "4. Upload these files:"
    echo "   - app.py"
    echo "   - requirements.txt"
    echo "   - README_HF.md (rename to README.md)"
    echo "5. Add secrets if needed (HUGGINGFACE_TOKEN)"
    echo "6. Your Space will build automatically!"
}

# Function to run local deployment
run_local() {
    print_info "Running application locally..."
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_warning "Virtual environment not found. Creating one..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install requirements
    print_info "Installing/updating requirements..."
    pip install -r requirements.txt
    
    # Run Streamlit
    print_status "Starting Streamlit application..."
    print_info "Application will open in your browser at http://localhost:8501"
    streamlit run app.py
}

# Function to check project structure
check_project() {
    print_info "Checking project structure..."
    
    required_files=("app.py" "requirements.txt" ".streamlit/config.toml")
    missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -eq 0 ]; then
        print_status "All required files present!"
    else
        print_error "Missing required files:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        return 1
    fi
    
    # Check optional files
    optional_files=(".streamlit/secrets.toml" "vercel.json" ".gitignore")
    for file in "${optional_files[@]}"; do
        if [ -f "$file" ]; then
            print_status "Found optional file: $file"
        else
            print_warning "Optional file missing: $file"
        fi
    done
}

# Function to show help
show_help() {
    echo "NL to SQL Converter - Deployment Script"
    echo "======================================"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  local       Run the application locally"
    echo "  streamlit   Deploy to Streamlit Community Cloud"
    echo "  vercel      Deploy to Vercel"
    echo "  hf-spaces   Prepare for Hugging Face Spaces"
    echo "  check       Check project structure"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 local          # Run locally"
    echo "  $0 streamlit      # Deploy to Streamlit Cloud"
    echo "  $0 vercel         # Deploy to Vercel"
    echo "  $0 check          # Check if all files are present"
    echo ""
}

# Main script logic
main() {
    case ${1:-help} in
        local)
            check_project && run_local
            ;;
        streamlit)
            check_project && deploy_streamlit_cloud
            ;;
        vercel)
            check_project && deploy_vercel
            ;;
        hf-spaces|huggingface)
            check_project && deploy_hf_spaces
            ;;
        check)
            check_project
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"