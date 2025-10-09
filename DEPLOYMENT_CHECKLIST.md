# DivineWhispers - Render Deployment Checklist

## 🔴 CRITICAL - Must Complete Before Deployment

### 1. JWT Security
- [ ] Generate secure SECRET_KEY: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] Add to Render environment variables as `SECRET_KEY`
- [ ] Never use default: `INSECURE_DEFAULT_DO_NOT_USE_IN_PRODUCTION`

### 2. Zoho Email/SMTP Setup
- [ ] Create Zoho email account (or use existing domain email)
- [ ] Generate app-specific password in Zoho settings
- [ ] Add to Render environment variables:
  ```
  SMTP_HOST=smtp.zoho.com
  SMTP_PORT=587
  SMTP_USER=your-email@yourdomain.com
  SMTP_PASSWORD=your-zoho-app-password
  FROM_EMAIL=noreply@yourdomain.com
  SUPPORT_EMAIL=support@yourdomain.com
  ```

### 3. OpenAI API Configuration
- [ ] Get API key from https://platform.openai.com/api-keys
- [ ] Add to Render environment variables:
  ```
  OPENAI_API_KEY=sk-proj-...
  LLM_MODEL=gpt-3.5-turbo
  LLM_PROVIDER=openai
  ```

---

## 🟡 IMPORTANT - Required Configuration

### 4. Database Setup
- [ ] Create PostgreSQL database in Render dashboard
- [ ] Copy `DATABASE_URL` from Render (auto-provided)
- [ ] After first deployment, run migrations:
  ```bash
  # In Render Shell
  python -m alembic upgrade head
  ```

### 5. CORS & Frontend URLs
- [ ] Update `ALLOWED_HOSTS` with production frontend URLs:
  ```
  ALLOWED_HOSTS=https://your-frontend.com,https://www.your-frontend.com
  ```
- [ ] Set `FRONTEND_URL=https://your-frontend.com` (for email links)

### 6. ChromaDB Storage
- [ ] Create Persistent Disk in Render (name: `chroma-data`, size: 1GB+)
- [ ] Mount at: `/opt/render/project/chroma_db`
- [ ] Set environment variable:
  ```
  CHROMA_DB_PATH=/opt/render/project/chroma_db
  ```
- [ ] After deployment, run data ingestion:
  ```bash
  python Backend/fortune_module/data_ingestion.py
  ```

### 7. Payment Integration (Stripe & TapPay)
- [ ] **Stripe Setup:**
  - [ ] Get API keys from https://dashboard.stripe.com/apikeys
  - [ ] Add to Render environment:
    ```
    STRIPE_SECRET_KEY=sk_live_...
    STRIPE_PUBLISHABLE_KEY=pk_live_...
    STRIPE_WEBHOOK_SECRET=whsec_...
    ```
  - [ ] Configure webhook in Stripe dashboard:
    - URL: `https://your-backend.onrender.com/api/v1/webhooks/stripe`
    - Events: `payment_intent.succeeded`, `payment_intent.payment_failed`

- [ ] **TapPay Setup:**
  - [ ] Get credentials from TapPay merchant portal
  - [ ] Add to Render environment:
    ```
    TAPPAY_PARTNER_KEY=partner_...
    TAPPAY_MERCHANT_ID=your_merchant_id
    TAPPAY_APP_ID=your_app_id
    TAPPAY_APP_KEY=your_app_key
    ```

---

## 🟢 RECOMMENDED - Best Practices

### 8. Security Settings
- [ ] Verify password requirements (already configured):
  ```
  PASSWORD_MIN_LENGTH=12
  PASSWORD_REQUIRE_UPPERCASE=true
  PASSWORD_REQUIRE_LOWERCASE=true
  PASSWORD_REQUIRE_NUMBERS=true
  PASSWORD_REQUIRE_SYMBOLS=true
  ```

### 9. Logging & Monitoring
- [ ] Set production log level:
  ```
  LOG_LEVEL=INFO
  DEBUG=false
  ```
- [ ] Configure health check in Render: `/health`

### 10. Frontend Configuration
- [ ] Create `divine-whispers-frontend/.env.production`:
  ```
  REACT_APP_API_URL=https://your-backend.onrender.com
  REACT_APP_WS_URL=wss://your-backend.onrender.com
  ```
- [ ] Remove or comment out proxy in `package.json` before build

---

## 📦 Render Deployment Setup

### Backend (Docker)
1. [ ] **Create New Web Service** in Render
2. [ ] **Connect Repository**: Link your GitHub repo
3. [ ] **Configure Service:**
   - Name: `divinewhispers-backend`
   - Environment: `Docker`
   - Region: Choose closest to users
   - Branch: `main`
   - Root Directory: `Backend`
   - Dockerfile Path: `Backend/Dockerfile`
4. [ ] **Add Environment Variables** (from sections 1-7 above)
5. [ ] **Add Persistent Disk:**
   - Name: `chroma-data`
   - Mount Path: `/opt/render/project/chroma_db`
   - Size: 1GB
6. [ ] **Deploy**

### Frontend (Static Site)
1. [ ] **Create New Static Site** in Render
2. [ ] **Configure Build:**
   - Name: `divinewhispers-frontend`
   - Root Directory: `divine-whispers-frontend`
   - Build Command: `npm install && npm run build`
   - Publish Directory: `build`
3. [ ] **Add Environment Variables** (section 10)
4. [ ] **Deploy**

---

## ✅ Post-Deployment Verification

### After Backend Deploys:
- [ ] Check `/health` endpoint returns `{"status": "healthy"}`
- [ ] Run database migrations: `python -m alembic upgrade head`
- [ ] Ingest fortune data: `python Backend/fortune_module/data_ingestion.py`
- [ ] Test API docs: `https://your-backend.onrender.com/api/docs`
- [ ] Verify email sending (registration verification)
- [ ] Test payment webhooks with Stripe CLI

### After Frontend Deploys:
- [ ] Test user registration flow
- [ ] Test login and JWT refresh
- [ ] Test fortune reading generation
- [ ] Test payment integration (Stripe/TapPay)
- [ ] Test WebSocket chat connection
- [ ] Verify admin dashboard access
- [ ] Check contact form emails

---

## 🔐 Security Checklist

- [ ] `.env` files are in `.gitignore` (never committed)
- [ ] All API keys are environment variables (not hardcoded)
- [ ] HTTPS enforced (Render provides this automatically)
- [ ] CORS restricted to production domains only
- [ ] Database uses strong password
- [ ] SECRET_KEY is cryptographically random (32+ bytes)
- [ ] Admin accounts have strong passwords
- [ ] Rate limiting enabled (check `slowapi` configuration)

---

## 📊 Environment Variables Quick Reference

Copy this template to Render environment variables:

```bash
# === CRITICAL SECURITY ===
SECRET_KEY=<generate-new-random-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# === DATABASE (Auto-provided) ===
DATABASE_URL=<render-auto-fills-this>

# === EMAIL (Zoho) ===
SMTP_HOST=smtp.zoho.com
SMTP_PORT=587
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=<zoho-app-password>
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=Divine Whispers
SUPPORT_EMAIL=support@yourdomain.com
FRONTEND_URL=https://your-frontend.com

# === OPENAI ===
OPENAI_API_KEY=sk-proj-...
LLM_MODEL=gpt-3.5-turbo
LLM_PROVIDER=openai

# === PAYMENTS ===
# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# TapPay
TAPPAY_PARTNER_KEY=partner_...
TAPPAY_MERCHANT_ID=...
TAPPAY_APP_ID=...
TAPPAY_APP_KEY=...

# === CHROMADB ===
CHROMA_DB_PATH=/opt/render/project/chroma_db
CHROMA_COLLECTION_NAME=fortune_knowledge

# === CORS ===
ALLOWED_HOSTS=https://your-frontend.com,https://www.your-frontend.com

# === APP SETTINGS ===
DEBUG=false
LOG_LEVEL=INFO
DEFAULT_USER_POINTS=100
FORTUNE_DRAW_COST=10
FORTUNE_INTERPRET_COST=15
```

---

## 🚨 Common Issues & Solutions

**Issue**: ChromaDB data not persisting
- **Solution**: Ensure Persistent Disk is mounted at correct path

**Issue**: Email sending fails
- **Solution**: Verify Zoho credentials, check 2FA/app password settings

**Issue**: Payment webhook not working
- **Solution**: Check webhook URL in Stripe/TapPay dashboard, verify `WEBHOOK_SECRET`

**Issue**: Database migration fails
- **Solution**: SSH into Render shell, manually run `alembic upgrade head`

**Issue**: Frontend can't connect to backend
- **Solution**: Verify CORS settings, check `REACT_APP_API_URL` in frontend

---

## 📞 Support

- **Render Docs**: https://render.com/docs
- **Stripe Webhooks**: https://stripe.com/docs/webhooks
- **Zoho SMTP**: https://www.zoho.com/mail/help/zoho-smtp.html
- **OpenAI API**: https://platform.openai.com/docs

---

**Last Updated**: 2025-10-10
**Deployment Method**: Docker on Render (Recommended)
**Estimated First-Time Setup**: 45-60 minutes
