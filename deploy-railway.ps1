# 🚀 Quick Deploy to Railway (India Region)
# PowerShell script for Windows

Write-Host "🚂 Railway Deployment Setup" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan
Write-Host ""

# Check if git is installed
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git is not installed. Please install Git first." -ForegroundColor Red
    Write-Host "   Download from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Check if repo is initialized
if (-not (Test-Path .git)) {
    Write-Host "📦 Initializing Git repository..." -ForegroundColor Yellow
    git init
    git add .
    git commit -m "Initial commit - Ready for Railway deployment"
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
} else {
    Write-Host "✅ Git repository already initialized" -ForegroundColor Green
}

# Check for GitHub CLI
if (Get-Command gh -ErrorAction SilentlyContinue) {
    Write-Host "🐙 GitHub CLI detected" -ForegroundColor Cyan
    $response = Read-Host "Create GitHub repository now? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        gh repo create trading-dashboard --public --source=. --push
        Write-Host "✅ Pushed to GitHub" -ForegroundColor Green
    }
} else {
    Write-Host "ℹ️  GitHub CLI not found." -ForegroundColor Yellow
    Write-Host "   Install from: https://cli.github.com/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   OR manually:" -ForegroundColor Yellow
    Write-Host "   1. Create a repo on GitHub" -ForegroundColor White
    Write-Host "   2. Run: git remote add origin YOUR_REPO_URL" -ForegroundColor White
    Write-Host "   3. Run: git push -u origin main" -ForegroundColor White
}

Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Go to https://railway.app" -ForegroundColor White
Write-Host "2. Click 'New Project' → 'Deploy from GitHub'" -ForegroundColor White
Write-Host "3. Select your repository" -ForegroundColor White
Write-Host "4. Set Region: Asia Pacific (Mumbai)" -ForegroundColor White
Write-Host "5. Generate domain and copy URL" -ForegroundColor White
Write-Host "6. Update frontend/script.js with your Railway URL" -ForegroundColor White
Write-Host ""
Write-Host "✅ All deployment files are ready!" -ForegroundColor Green
Write-Host "   - railway.json (deployment config)" -ForegroundColor White
Write-Host "   - Procfile (start command)" -ForegroundColor White
Write-Host "   - nixpacks.toml (build config)" -ForegroundColor White
Write-Host "   - start.sh (startup script)" -ForegroundColor White
Write-Host "   - runtime.txt (Python 3.11)" -ForegroundColor White
Write-Host ""
Write-Host "🌍 Configured for India Region (Mumbai - ap-south-1)" -ForegroundColor Magenta
Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
