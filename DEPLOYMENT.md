# 🚀 Deployment Guide

## Quick Deploy Options

### Option 1: Docker Compose (Recommended)

**Prerequisites:**
- Docker & Docker Compose installed

**Steps:**
```bash
# 1. Clone repository
git clone <your-repo-url>
cd App

# 2. Train ML models (first time only)
cd backend
pip install -r requirements.txt
python train_models.py
cd ..

# 3. Build and run
docker-compose up -d

# 4. Access
Frontend: http://localhost:3000
Backend API: http://localhost:8000
```

**Stop:**
```bash
docker-compose down
```

---

### Option 2: Railway (Backend)

**Prerequisites:**
- Railway account
- GitHub repository

**Steps:**
1. Fork/push code to GitHub
2. Go to [railway.app](https://railway.app)
3. Click "New Project" → "Deploy from GitHub"
4. Select your repository
5. Set root directory: `/backend`
6. Add environment variables (if needed):
   ```
   PORT=8000
   HOST=0.0.0.0
   ```
7. Railway will auto-deploy on push

**Custom Domain:**
- Settings → Generate Domain
- Or add custom domain

---

### Option 3: Vercel (Frontend) + Railway (Backend)

**Frontend (Vercel):**
1. Go to [vercel.com](https://vercel.com)
2. Import GitHub repository
3. Set root directory: `/frontend`
4. Add environment variable:
   ```
   NEXT_PUBLIC_API_URL=<your-railway-backend-url>
   ```
5. Deploy

**Backend (Railway):**
- Follow Option 2 steps

**Update Frontend API URL:**
Edit `frontend/script.js`:
```javascript
const API_BASE = 'https://your-railway-backend.up.railway.app';
```

---

### Option 4: AWS EC2

**Prerequisites:**
- AWS account
- EC2 instance (t2.medium or higher)
- SSH access

**Steps:**

1. **Launch EC2 Instance**
   ```
   - AMI: Ubuntu 22.04 LTS
   - Instance Type: t2.medium (2 vCPU, 4GB RAM)
   - Storage: 20GB
   - Security Group: Allow ports 22, 80, 443, 8000
   ```

2. **SSH into Instance**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   ```

3. **Install Docker**
   ```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose
   sudo usermod -aG docker $USER
   newgrp docker
   ```

4. **Clone and Deploy**
   ```bash
   git clone <your-repo-url>
   cd App
   
   # Train models
   cd backend
   sudo apt install -y python3.11 python3-pip
   pip install -r requirements.txt
   python3 train_models.py
   cd ..
   
   # Run with Docker
   docker-compose up -d
   ```

5. **Setup Nginx Reverse Proxy**
   ```bash
   sudo apt install -y nginx
   sudo nano /etc/nginx/sites-available/trading
   ```
   
   Add:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:3000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
       
       location /api/ {
           proxy_pass http://localhost:8000;
           proxy_http_version 1.1;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```
   
   Enable:
   ```bash
   sudo ln -s /etc/nginx/sites-available/trading /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

6. **SSL with Let's Encrypt**
   ```bash
   sudo apt install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

---

### Option 5: Render (All-in-One)

**Backend:**
1. Go to [render.com](https://render.com)
2. New Web Service
3. Connect GitHub repo
4. Settings:
   ```
   Build Command: pip install -r requirements.txt && python train_models.py
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

**Frontend:**
1. New Static Site
2. Connect GitHub repo
3. Build Command: (none)
4. Publish Directory: `/frontend`

---

## Environment Variables

### Backend (.env)

```bash
# Optional API keys for enhanced data
TWELVE_DATA_API_KEY=your_key
ALPHA_VANTAGE_KEY=your_key
NEWS_API_KEY=your_key

# Server config
HOST=0.0.0.0
PORT=8000
```

### Frontend (Update in script.js)

```javascript
// Change API base URL
const API_BASE = 'https://your-backend-url.com';
```

---

## Post-Deployment Checklist

- [ ] Backend health check: `curl http://your-backend/api/health`
- [ ] Frontend loads: `http://your-frontend/`
- [ ] ML models loaded: Check backend logs for "✅ ML models loaded"
- [ ] Charts rendering: Test on frontend
- [ ] API endpoints working: Test `/api/signal_live?symbol=NIFTY`
- [ ] Paper trading: Test `/api/paper/stats`
- [ ] WebSocket: Test live updates

---

## Monitoring & Maintenance

### Health Checks

```bash
# Backend health
curl http://localhost:8000/api/health

# Check logs
docker logs trading_backend

# Check ML models
curl http://localhost:8000/api/signal_live?symbol=NIFTY | jq '.ml_view'
```

### Updating Models

```bash
# SSH into server
cd App/backend
python train_models.py

# Restart backend
docker-compose restart backend
```

### Auto-Restart on Crash

Add to `docker-compose.yml`:
```yaml
restart: always
```

Or use systemd (non-Docker):
```bash
sudo nano /etc/systemd/system/trading-backend.service
```

```ini
[Unit]
Description=Trading Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/App/backend
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable trading-backend
sudo systemctl start trading-backend
```

---

## Performance Optimization

### Backend
- **Caching**: Redis for API responses
- **Workers**: Gunicorn with multiple workers
  ```bash
  gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
  ```
- **Database**: PostgreSQL for paper trading history
- **CDN**: CloudFlare for static assets

### Frontend
- **Minification**: Minify JS/CSS
- **Compression**: Enable gzip in nginx
- **CDN**: Serve from edge locations

---

## Scaling

### Horizontal Scaling (Multiple Instances)

1. **Load Balancer**: Nginx/HAProxy
2. **Shared State**: Redis for cache, PostgreSQL for DB
3. **Docker Swarm or Kubernetes**

### Vertical Scaling (Bigger Instance)

- t2.medium → t2.large → t2.xlarge
- 4GB RAM → 8GB → 16GB

---

## Troubleshooting

### Backend Not Starting
```bash
# Check logs
docker logs trading_backend

# Common issues:
# - Models not trained: Run train_models.py
# - Port conflict: Change port in docker-compose.yml
# - Dependencies: Rebuild Docker image
```

### Frontend Not Loading
```bash
# Check nginx logs
docker logs trading_frontend

# Test backend connection
curl http://backend:8000/api/health
```

### Charts Not Rendering
- Check browser console (F12)
- Verify Lightweight Charts CDN loaded
- Test API: `/api/signal_live?symbol=NIFTY`

### High CPU Usage
- Reduce model complexity (train with fewer estimators)
- Increase cache TTLs
- Use Redis for caching

---

## Security

### Production Checklist

- [ ] Change default ports
- [ ] Enable HTTPS (SSL certificates)
- [ ] API rate limiting
- [ ] CORS restrictions
- [ ] Environment variables (no hardcoded keys)
- [ ] Firewall rules (only open necessary ports)
- [ ] Regular updates (Docker images, dependencies)
- [ ] Backup models and data
- [ ] Monitor logs for suspicious activity

---

## Cost Estimates

### Railway (Hobby Plan)
- Backend: $5-10/month
- Auto-scaling: Pay per use

### AWS EC2
- t2.medium: ~$30/month
- t2.large: ~$60/month
- + Data transfer costs

### Render
- Free tier: Limited hours
- Paid: $7-25/month per service

### Vercel
- Free tier: Perfect for frontend
- Pro: $20/month (if needed)

---

## Support

- **Issues**: GitHub Issues
- **Docs**: README.md
- **Updates**: `git pull && docker-compose up -d --build`

---

**Happy Deploying! 🚀**
