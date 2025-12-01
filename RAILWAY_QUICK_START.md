# 🚀 Railway Deployment - Quick Reference

## ✅ Files Created (All Ready!)

| File | Purpose |
|------|---------|
| `railway.json` | Railway deployment configuration |
| `Procfile` | Tells Railway how to start your app |
| `nixpacks.toml` | Build configuration (Python 3.11) |
| `start.sh` | Startup script |
| `runtime.txt` | Python version specification |
| `.railwayignore` | Files to exclude from deployment |
| `.env.railway` | Environment variables template |
| `deploy-railway.ps1` | Windows deployment script |
| `RAILWAY_DEPLOYMENT.md` | Complete deployment guide |

---

## 🌍 Region: India (Mumbai)
**Server Location:** Asia Pacific South 1 (ap-south-1)

---

## 📦 One-Command Deployment

### Windows (PowerShell):
```powershell
.\deploy-railway.ps1
```

### Linux/Mac:
```bash
chmod +x deploy-railway.sh
./deploy-railway.sh
```

---

## 🔥 Manual Quick Deploy

### Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
gh repo create trading-dashboard --public --source=. --push
```

### Step 2: Deploy to Railway
1. Go to **https://railway.app**
2. Click **"New Project"** → **"Deploy from GitHub"**
3. Select your repository
4. Railway auto-deploys! ✨

### Step 3: Set India Region
- Dashboard → **Settings** → **Region**
- Select: **Asia Pacific (Mumbai)**
- Click **Save**

### Step 4: Get Your URL
- **Settings** → **Domains** → **Generate Domain**
- Copy: `https://your-app.up.railway.app`

### Step 5: Update Frontend
Edit `frontend/script.js` (Line 1):
```javascript
const API_BASE = 'https://your-app.up.railway.app';
```

---

## 🧪 Test Your Deployment

```bash
# Health check
curl https://your-app.up.railway.app/api/health

# Expected response:
{"status":"ok"}

# Test signal endpoint
curl https://your-app.up.railway.app/api/signal_live?symbol=NIFTY&interval=300&limit=10
```

---

## 💰 Pricing (India Region)

| Plan | Cost | Usage |
|------|------|-------|
| **Free Trial** | $5 credit | ~500 hours |
| **Hobby** | $5/month | Unlimited usage |
| **Pro** | $20/month | Higher limits + priority |

**Estimate:** ~$5-10/month for this app

---

## 🔧 Troubleshooting

### Build Fails
```bash
# Check Python version
cat runtime.txt
# Should show: python-3.11

# Check requirements
cat backend/requirements.txt
```

### Server Won't Start
- Check Railway logs: Dashboard → Deployments → View Logs
- Look for "✅ ML models loaded successfully"
- Verify PORT environment variable

### 500 Errors
- Check backend logs for Python exceptions
- Verify all dependencies installed
- Check ML model files exist in `backend/ml_model/`

---

## 📞 Support

- **Railway Docs:** https://docs.railway.app
- **Project Issues:** GitHub Issues
- **Quick Guide:** `RAILWAY_DEPLOYMENT.md`
- **Full Guide:** `DEPLOYMENT.md`

---

**🎉 You're all set! Railway will handle the rest.**
