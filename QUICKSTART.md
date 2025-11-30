# Quick Start Guide

Get your Trading Assistant running in 5 minutes!

## Prerequisites

- Python 3.11+ installed
- Internet connection

## Steps

### 1. Check System Health
```bash
cd D:\App\backend
python system_check.py
```

You should see:
```
[OK] ALL CHECKS PASSED!
[OK] System is ready for production.
```

### 2. Start the Backend Server

**Windows PowerShell:**
```powershell
Push-Location "D:\App\backend"
py -m uvicorn main:app --reload
```

**Command Prompt:**
```cmd
cd D:\App\backend
python -m uvicorn main:app --reload
```

**Linux/Mac:**
```bash
cd backend
python3 -m uvicorn main:app --reload
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 3. Open Application

Open your web browser and go to:
```
http://localhost:8000
```

You should see the Trading Assistant dashboard!

### 4. (Optional) Train ML Models

For ML predictions, train the models once:

```bash
cd D:\App\backend
python train_models.py
```

This takes 10-15 minutes and needs to be done only once.

After training, **restart the server** to load the models.

## Common Issues

### "uvicorn: command not found"
Use: `py -m uvicorn main:app --reload` instead

### "No module named 'xxx'"
Install dependencies: `pip install -r requirements.txt`

### Charts not loading
- Check browser console for errors (F12)
- Clear browser cache (Ctrl+Shift+Delete)
- Check internet connection (charts use CDN)

### NSE data not fetching
- This is normal - NSE rate limits requests
- System will use fallback sample data automatically
- Check network connectivity

## Production Deployment

For production deployment, see [README.md](README.md#-production-deployment) for detailed instructions including:
- Systemd service setup
- Nginx reverse proxy
- HTTPS configuration
- Monitoring setup

## Need Help?

1. Check [README.md](README.md) for full documentation
2. Read [docs/API.md](docs/API.md) for API details
3. Review [PRODUCTION_READY.md](PRODUCTION_READY.md) for system status
4. Open an issue on GitHub

---

**Happy Trading! 📈**
