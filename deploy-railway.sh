#!/bin/bash

# 🚀 Quick Deploy to Railway (India Region)
# Run this script to prepare and deploy your app

echo "🚂 Railway Deployment Setup"
echo "=============================="

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

# Check if repo is initialized
if [ ! -d .git ]; then
    echo "📦 Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit - Ready for Railway deployment"
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already initialized"
fi

# Check for GitHub CLI
if command -v gh &> /dev/null; then
    echo "🐙 GitHub CLI detected"
    read -p "Create GitHub repository now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gh repo create trading-dashboard --public --source=. --push
        echo "✅ Pushed to GitHub"
    fi
else
    echo "ℹ️  GitHub CLI not found. Please manually:"
    echo "   1. Create a repo on GitHub"
    echo "   2. Run: git remote add origin YOUR_REPO_URL"
    echo "   3. Run: git push -u origin main"
fi

echo ""
echo "📋 Next Steps:"
echo "1. Go to https://railway.app"
echo "2. Click 'New Project' → 'Deploy from GitHub'"
echo "3. Select your repository"
echo "4. Set Region: Asia Pacific (Mumbai)"
echo "5. Generate domain and copy URL"
echo "6. Update frontend/script.js with your Railway URL"
echo ""
echo "✅ All deployment files are ready!"
echo "   - railway.json (deployment config)"
echo "   - Procfile (start command)"
echo "   - nixpacks.toml (build config)"
echo "   - start.sh (startup script)"
echo "   - runtime.txt (Python 3.11)"
echo ""
echo "🌍 Configured for India Region (Mumbai - ap-south-1)"
