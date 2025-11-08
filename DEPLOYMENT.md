# 🚀 Gods Ping Deployment Guide

## 📋 Prerequisites

- GitHub account
- Render account (https://render.com)
- Vercel account (https://vercel.com)
- Git installed locally

---

## 🔧 Backend Deployment (Render)

### Step 1: Prepare Repository

1. **Push to GitHub:**
   ```bash
   cd d:\git\gods-ping
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

### Step 2: Deploy on Render

1. **Go to Render Dashboard:**
   - Visit https://dashboard.render.com
   - Click **"New +"** → **"Web Service"**

2. **Connect Repository:**
   - Connect your GitHub account
   - Select `gods-ping` repository
   - Click **"Connect"**

3. **Configure Service:**
   - **Name:** `gods-ping-backend`
   - **Region:** Singapore (or closest to you)
   - **Branch:** `main`
   - **Root Directory:** Leave blank (or set to `/`)
   - **Environment:** `Python 3`
   - **Build Command:** `cd backend && pip install -r requirements.txt`
   - **Start Command:** `cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. **Set Environment Variables:**
   
   **Option 1: Use the Secret Generator (Recommended)**
   
   Run the included script to generate all secrets at once:
   ```bash
   python generate_secrets.py
   ```
   
   Copy the output and paste each variable into Render.
   
   **Option 2: Manual Generation**
   
   Click **"Advanced"** → **"Add Environment Variable"** and add each:
   
   ```
   SECRET_KEY = [Generate random 32-char string]
   ALGORITHM = HS256
   ACCESS_TOKEN_EXPIRE_MINUTES = 43200
   ENCRYPTION_KEY = [Generate random 32-char base64 string]
   CORS_ORIGINS = https://your-frontend.vercel.app,http://localhost:5173
   ```

   **Generate SECRET_KEY:**
   ```python
   import secrets
   print(secrets.token_urlsafe(32))
   ```

   **Generate ENCRYPTION_KEY:**
   ```python
   from cryptography.fernet import Fernet
   print(Fernet.generate_key().decode())
   ```
   
   > **Note:** After deploying frontend, update `CORS_ORIGINS` with your actual Vercel URL

5. **Deploy:**
   - Click **"Create Web Service"**
   - Wait for deployment (5-10 minutes)
   - Copy the service URL: `https://gods-ping-backend.onrender.com`

---

## 🎨 Frontend Deployment (Vercel)

### Step 1: Deploy on Vercel (No code changes needed!)

1. **Go to Vercel Dashboard:**
   - Visit https://vercel.com/new
   - Click **"Import Project"** or **"Add New..."** → **"Project"**

2. **Connect Repository:**
   - Connect GitHub account if not already connected
   - Select `gods-ping` repository
   - Click **"Import"**

3. **Configure Project:**
   
   **IMPORTANT - Follow these exact settings:**
   
   - **Framework Preset:** Vite (auto-detected)
   - **Root Directory:** `frontend` ⚠️ **Click Edit** and type `frontend`
   - **Build Command:** `npm run build` (default is fine)
   - **Output Directory:** `dist` (default is fine)
   - **Install Command:** `npm install` (default is fine)

4. **Set Environment Variables:**
   
   Click **"Environment Variables"** and add:
   
   ⚠️ **IMPORTANT:** Enter the value directly, do NOT use "Secret" option!
   
   - **Key:** `VITE_API_URL`
   - **Value:** `https://gods-ping-backend.onrender.com` (paste directly)
   - **Environments:** Check all three boxes ✓ Production ✓ Preview ✓ Development
   - Click **"Add"**
   
   **Common mistake:** If you see an error about "Secret api-url does not exist", delete the variable and add it again, making sure to paste the URL directly in the Value field (not as a secret reference)

5. **Deploy:**
   - Click **"Deploy"**
   - Wait for build (2-5 minutes)
   - ✅ Your app will be live!

6. **Common Vercel Deployment Issues:**

   **Problem: 404 NOT_FOUND**
   - ✅ Fix: Make sure **Root Directory** is set to `frontend`
   - Go to Project Settings → General → Root Directory → Edit → Set to `frontend`
   
   **Problem: Build fails with "vite: command not found"**
   - ✅ Fix: Vercel should auto-detect Vite. Check Framework Preset is "Vite"
   
   **Problem: App loads but API calls fail (CORS)**
   - ✅ Fix: Update Render CORS_ORIGINS (see next section)

---

## 🔄 Update Backend CORS

**IMPORTANT: Do this immediately after frontend deploys!**

After frontend is deployed, update backend environment variables on Render:

1. Go to Render Dashboard → gods-ping-backend → **Environment**
2. Find `CORS_ORIGINS` and click **Edit**
3. Update the value to:
   ```
   https://gods-ping.vercel.app,http://localhost:5173
   ```
   (Replace `gods-ping.vercel.app` with your actual Vercel domain if different)
4. Click **Save**
5. Wait for automatic redeploy (~2-3 minutes)
6. Test your frontend - login should work now! ✅

---

## ✅ Post-Deployment Checklist

### Test Backend
- [ ] Visit: `https://gods-ping-backend.onrender.com/`
- [ ] Should see: `{"app":"Gods Ping (Shichi-Fukujin)","status":"running",...}`
- [ ] Check: `https://gods-ping-backend.onrender.com/docs`
- [ ] Verify CORS: `https://gods-ping-backend.onrender.com/api/debug/cors`
  - Should show `allowed_origins` including your Vercel URL

### Test Frontend
- [ ] Visit: `https://gods-ping.vercel.app`
- [ ] Login with admin credentials (Admin / K@nph0ng69)
- [ ] Check all features work:
  - [ ] Balance loads (Account Balance section)
  - [ ] Market data displays
  - [ ] Logs tab opens (may be empty initially)
  - [ ] Settings accessible
- [ ] Test trading operations:
  - [ ] Set Binance API keys in Settings
  - [ ] Start Gods Hand bot
  - [ ] Verify trades execute (paper trading)
  - [ ] Check AI Thinking vs Action logs appear after bot runs

### Database
- [ ] Backend automatically creates SQLite database
- [ ] First deployment creates admin user
- [ ] All tables created on startup (users, trades, bot_config, logs, paper_trading_snapshots)
- [ ] For production, consider PostgreSQL:
  - Render provides free PostgreSQL
  - Update `DATABASE_URL` environment variable

**Note:** AI Thinking and AI Action logs will only appear after you've started the Gods Hand bot and it has made recommendations. If those log categories are empty, run the bot first.

---

## 🔐 Security Notes

### 1. Change Default Credentials
After first deployment, immediately change admin password!

### 2. Secure API Keys
- Never commit `.env` files
- Use Render's environment variables
- Each user sets their own Binance API keys

### 3. HTTPS Only
- Both Render and Vercel provide free SSL
- All communication is encrypted

---

## 📊 Database Migration (Optional - PostgreSQL)

If you want persistent database instead of SQLite:

### 1. Create PostgreSQL Database on Render

1. Render Dashboard → **"New +"** → **"PostgreSQL"**
2. Name: `gods-ping-db`
3. Region: Same as backend
4. Plan: Free
5. Create database

### 2. Update Backend Environment

1. Copy **Internal Database URL** from PostgreSQL dashboard
2. Update backend environment variable:
   ```
   DATABASE_URL = postgresql://user:pass@host/dbname
   ```

### 3. Update `backend/app/db.py`

```python
# Change from:
SQLALCHEMY_DATABASE_URL = "sqlite:///./gods_ping.db"

# To:
import os
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gods_ping.db")
```

### 4. Install PostgreSQL Driver

Add to `requirements.txt`:
```
psycopg2-binary>=2.9.9
```

---

## 🔄 Continuous Deployment

Both Render and Vercel auto-deploy when you push to GitHub:

```bash
# Make changes
git add .
git commit -m "Update feature"
git push origin main

# Render and Vercel automatically redeploy!
```

---

## 🐛 Troubleshooting

### Backend Issues

**Problem:** Service won't start
- Check logs in Render Dashboard
- Verify all environment variables are set
- Check `requirements.txt` syntax

**Problem:** CORS errors
- Update `CORS_ORIGINS` with frontend URL
- Don't include trailing slash

**Problem:** Database errors
- Delete `gods_ping.db` and redeploy (recreates DB)
- Or migrate to PostgreSQL

### Frontend Issues

**Problem:** Can't connect to backend
- Check `VITE_API_URL` is correct
- Verify backend is running
- Check browser console for errors

**Problem:** Build fails
- Check `package.json` dependencies
- Run `npm install` locally first
- Check Node version (should be 18+)

---

## 💰 Cost Breakdown

### Free Tier (Recommended for Testing)

**Render Free:**
- ✅ 750 hours/month (enough for 1 service)
- ✅ Auto-sleep after 15 mins inactivity
- ✅ Wakes up in ~30 seconds
- ❌ Spins down daily

**Vercel Free:**
- ✅ 100 GB bandwidth/month
- ✅ Unlimited deployments
- ✅ Always on (no sleep)
- ✅ Global CDN

**Total: $0/month** 🎉

### Production (Paid)

**Render Starter ($7/month):**
- ✅ No sleep
- ✅ Always on
- ✅ 400 build minutes

**Vercel Pro ($20/month):**
- ✅ 1 TB bandwidth
- ✅ Priority support
- ✅ Custom domains

**Total: ~$27/month**

---

## 🎯 Next Steps

1. **Deploy Backend** → Get Render URL
2. **Update Frontend** → Point to Render URL
3. **Deploy Frontend** → Get Vercel URL
4. **Update CORS** → Add Vercel URL to backend
5. **Test Everything** → Login, trade, verify
6. **Monitor** → Check logs regularly
7. **Optimize** → Consider PostgreSQL for production

---

## 📞 Support

- **Render Docs:** https://render.com/docs
- **Vercel Docs:** https://vercel.com/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **Vite Docs:** https://vitejs.dev

---

## 🎉 You're Ready!

Your trading bot will be live and accessible from anywhere in the world! 🌍🚀

Good luck with your deployment! 📈💰
