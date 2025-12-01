# 🚂 Railway Deployment - Quick Start

## India Region (Mumbai - ap-south-1)

This project is configured for one-click deployment to Railway with servers in India.

### Files Created for Railway:
- ✅ `railway.json` - Railway configuration
- ✅ `Procfile` - Process definition
- ✅ `nixpacks.toml` - Build configuration
- ✅ `start.sh` - Startup script
- ✅ `runtime.txt` - Python 3.11 specification
- ✅ `.railwayignore` - Exclude unnecessary files

### Deploy Now:

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

**OR Manual Steps:**

1. **Push to GitHub** (if not already):
   ```bash
   git init
   git add .
   git commit -m "Ready for Railway deployment"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/trading-dashboard.git
   git push -u origin main
   ```

2. **Deploy to Railway**:
   - Go to https://railway.app
   - Click "New Project" → "Deploy from GitHub"
   - Select this repository
   - Railway auto-detects configuration ✨

3. **Set India Region**:
   - Settings → Region → **Asia Pacific (Mumbai)**
   - Railway redeploys automatically

4. **Get Your URL**:
   - Settings → Generate Domain
   - Copy: `https://your-app.up.railway.app`

5. **Update Frontend**:
   Edit `frontend/script.js`:
   ```javascript
   const API_BASE = 'https://your-app.up.railway.app';
   ```

### Expected Build Output:
```
✓ Installing Python 3.11
✓ Installing dependencies from requirements.txt
✓ Starting uvicorn server
✓ ML models loaded successfully
✓ Server running on $PORT
```

### Health Check:
```bash
curl https://your-app.up.railway.app/api/health
# Expected: {"status":"ok"}
```

### Troubleshooting:

**Build fails?**
- Check `requirements.txt` in `backend/` folder
- Ensure Python 3.11 compatibility

**Server won't start?**
- Check logs in Railway dashboard
- Verify PORT environment variable is used

**ML models not loading?**
- Models are in `backend/ml_model/` folder
- Check backend logs for "✅ ML models loaded"

### Cost Estimate:
- **Free Tier**: $5 credit/month (sufficient for testing)
- **Hobby Plan**: $5/month (unlimited usage)
- **Pro Plan**: $20/month (higher limits)

### Support:
- Railway Docs: https://docs.railway.app
- Project Issues: GitHub Issues
