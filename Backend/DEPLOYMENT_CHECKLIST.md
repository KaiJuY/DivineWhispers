# Divine Whispers - Render.com Deployment Checklist

## ✅ Pre-Deployment Checklist (Complete These First)

### 1. Environment Variables to Prepare

Before deploying, gather these credentials:

#### A. OpenAI API Key
- [ ] Get your OpenAI API key from https://platform.openai.com/api-keys
- [ ] Value: `sk-...` (starts with sk-)

#### B. Zoho Email Credentials (for verification emails)
- [ ] Create a Zoho Mail account or use existing one
- [ ] Enable "App Password" in Zoho settings:
  1. Go to https://accounts.zoho.com/home#security
  2. Click "App Passwords"
  3. Generate new app password for "Divine Whispers"
- [ ] SMTP_USER: `your-email@yourdomain.com`
- [ ] SMTP_PASSWORD: `<app-password-you-just-generated>`
- [ ] FROM_EMAIL: `your-email@yourdomain.com` (same as SMTP_USER)
- [ ] SUPPORT_EMAIL: `your-email@yourdomain.com`

#### C. Generated SECRET_KEY (Already done!)
```
dgV6dW54x2MKm-YANLHtxSrFZY-lwXjMRb3XDRMzZd4
```
**SAVE THIS KEY - You'll need it for Render!**

---

## 🚀 Deployment Steps

### Step 1: Commit Your Changes

```bash
cd Backend
git add Dockerfile build.sh render.yaml DEPLOYMENT_CHECKLIST.md
git commit -m "Prepare for Render.com deployment

- Updated Dockerfile to include fortune_module, Asset, and chroma_db
- Added build.sh for automated database migrations
- Created render.yaml for infrastructure as code
- Added deployment checklist"

git push origin main
```

### Step 2: Create Render Account

1. Go to https://render.com
2. Sign up using GitHub account (recommended)
3. Connect your GitHub repository

### Step 3: Deploy via Render Dashboard

#### Option A: Using Blueprint (Recommended - render.yaml)

1. In Render dashboard, click **"New +"** → **"Blueprint"**
2. Connect your Git repository
3. Render will auto-detect `render.yaml`
4. Click **"Apply"**
5. Wait for services to be created (database + web service)

#### Option B: Manual Setup

If blueprint doesn't work, create manually:

**Create PostgreSQL Database:**
1. Click **"New +"** → **"PostgreSQL"**
2. Name: `divine-whispers-db`
3. Database Name: `divine_whispers`
4. User: `divine_whispers_user`
5. Region: Oregon (or your preferred region)
6. Plan: **Starter (Free)**
7. Click **"Create Database"**

**Create Web Service:**
1. Click **"New +"** → **"Web Service"**
2. Connect your repository
3. Select branch: `main`
4. Root Directory: `Backend`
5. Runtime: **Docker**
6. Region: Same as database (Oregon)
7. Plan: **Starter (Free)**
8. Click **"Create Web Service"**

### Step 4: Configure Environment Variables

In your web service settings, go to **"Environment"** tab and add:

#### Critical Variables (MUST SET):

```env
# === SECURITY ===
SECRET_KEY=dgV6dW54x2MKm-YANLHtxSrFZY-lwXjMRb3XDRMzZd4

# === DATABASE ===
# DATABASE_URL is auto-added by Render when you link the database
# Just link the database in "Environment" → "Add Database" → Select your DB

# === OPENAI ===
OPENAI_API_KEY=sk-your-actual-openai-key-here
LLM_MODEL=gpt-3.5-turbo
LLM_PROVIDER=openai

# === EMAIL (Zoho) ===
SMTP_HOST=smtp.zoho.com
SMTP_PORT=587
SMTP_USER=your-email@yourdomain.com
SMTP_PASSWORD=your-zoho-app-password
FROM_EMAIL=your-email@yourdomain.com
FROM_NAME=Divine Whispers
SUPPORT_EMAIL=your-email@yourdomain.com

# === CHROMADB ===
CHROMA_DB_PATH=/opt/render/project/src/chroma_db
CHROMA_COLLECTION_NAME=fortune_knowledge

# === APP SETTINGS ===
DEBUG=false
LOG_LEVEL=INFO
DEFAULT_USER_POINTS=100
FORTUNE_DRAW_COST=10
FORTUNE_INTERPRET_COST=15
```

#### Variables to Update Later (After Frontend Deploys):

```env
# === CORS & FRONTEND ===
ALLOWED_HOSTS=https://your-frontend.onrender.com
FRONTEND_URL=https://your-frontend.onrender.com
```

### Step 5: Link PostgreSQL Database

1. In web service settings, go to **"Environment"** tab
2. Click **"Add Database"**
3. Select your `divine-whispers-db`
4. Render will automatically add `DATABASE_URL` variable

### Step 6: Deploy!

1. Click **"Manual Deploy"** → **"Deploy latest commit"**
2. Watch the build logs
3. Look for these success messages:
   - ✅ `Installing Python dependencies...`
   - ✅ `Running database migrations...`
   - ✅ `ChromaDB directory found`
   - ✅ `fortune_module directory found`
   - ✅ `Build completed successfully!`

### Step 7: Verify Deployment

1. Once deployed, click on your service URL (e.g., `https://divine-whispers-backend.onrender.com`)
2. You should see:
```json
{
  "message": "Welcome to Divine Whispers API",
  "docs": "/api/docs",
  "health": "/health"
}
```

3. Test health endpoint: `https://your-url.onrender.com/health`
```json
{
  "status": "healthy",
  "service": "Divine Whispers Backend",
  "version": "1.0.0"
}
```

4. Test API docs (if DEBUG=true): `https://your-url.onrender.com/api/docs`

---

## ⚠️ Important Notes

### ChromaDB Data Persistence

**FREE TIER WARNING:**
- ChromaDB data is copied into the Docker container
- On Render's free tier, containers are **ephemeral** (restarted periodically)
- Your vector database will persist **ONLY** within a container's lifetime
- When Render restarts the container, ChromaDB data is restored from your Git repo

**Solutions:**
1. **Recommended**: Keep `chroma_db/` in your Git repository (current setup)
   - ✅ Simple
   - ✅ Free
   - ✅ Data is version-controlled
   - ⚠️ Large repo size if DB grows

2. **For Production**: Upgrade to paid plan with **Persistent Disk**
   - Mount `/opt/render/project/src/chroma_db` to persistent disk
   - Cost: $1/GB/month

3. **Alternative**: Host ChromaDB separately (Chroma Cloud, self-hosted)

### Database Migrations

- Migrations run automatically via `build.sh`
- If migrations fail, check logs:
  - Render Dashboard → Your Service → Logs
- To run migrations manually:
  ```bash
  # In Render Shell
  alembic upgrade head
  ```

### First User Registration

After deployment, test user registration:
```bash
curl -X POST "https://your-url.onrender.com/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

You should receive a verification email at the registered address.

---

## 🔧 Troubleshooting

### Build Fails - ChromaDB Not Found
- **Cause**: Dockerfile couldn't copy `chroma_db/`
- **Fix**: Ensure `Backend/chroma_db/` exists and is committed to Git
- **Verify**: Run `ls -la Backend/chroma_db/` locally

### Build Fails - fortune_module Not Found
- **Cause**: Dockerfile couldn't copy `fortune_module/`
- **Fix**: Ensure `Backend/fortune_module/` exists and is committed to Git

### Database Connection Error
- **Cause**: `DATABASE_URL` not set correctly
- **Fix**:
  1. Check that PostgreSQL database is created
  2. Link database to web service in Render dashboard
  3. Verify `DATABASE_URL` starts with `postgresql+asyncpg://`

### Email Verification Not Working
- **Cause**: SMTP credentials incorrect
- **Fix**:
  1. Verify Zoho app password is correct
  2. Check SMTP_USER and FROM_EMAIL are identical
  3. Test Zoho login at https://mail.zoho.com

### CORS Errors from Frontend
- **Cause**: `ALLOWED_HOSTS` doesn't include frontend URL
- **Fix**: Update `ALLOWED_HOSTS` to include your frontend domain

---

## 📊 Monitoring

### Check Logs
```bash
# In Render Dashboard
Your Service → Logs

# Watch for errors
- "Database connection failed"
- "ChromaDB initialization failed"
- "OpenAI API key invalid"
```

### Health Check
Your service should respond to:
- `GET /health` - General health
- `GET /api/v1/admin/health` - Detailed health (admin only)

---

## 🎉 Post-Deployment

### Update Frontend
Once backend is deployed, update your frontend `.env`:

```env
NEXT_PUBLIC_API_URL=https://divine-whispers-backend.onrender.com
```

### Update Backend CORS
After frontend deploys, update backend environment variables:

```env
ALLOWED_HOSTS=https://your-frontend.onrender.com
FRONTEND_URL=https://your-frontend.onrender.com
```

### Test End-to-End
1. Register new user
2. Verify email
3. Login
4. Draw a fortune
5. Interpret fortune (uses ChromaDB + OpenAI)
6. Check chat feature

---

## 💰 Cost Breakdown

**FREE TIER:**
- PostgreSQL: 1GB storage (free)
- Web Service: 750 hours/month (free)
- Total: **$0/month**

**Limitations:**
- Spins down after 15 minutes of inactivity
- Cold start takes ~30 seconds
- No persistent disk for ChromaDB

**PAID TIER (Recommended for Production):**
- Starter Plan: $7/month (always on, no cold starts)
- PostgreSQL: $7/month (10GB storage)
- Persistent Disk: $1/GB/month (for ChromaDB)
- Total: ~$15-20/month

---

## 🆘 Need Help?

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com
- FastAPI Docs: https://fastapi.tiangolo.com

---

## ✅ Deployment Complete!

Your backend is now live! 🎉

Next steps:
1. Save your backend URL
2. Deploy frontend
3. Update CORS settings
4. Test full application

Good luck! 🚀
