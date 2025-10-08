# Email Setup Guide - Zoho SMTP

Simple guide for setting up email features with Zoho SMTP for Render deployment.

---

## What Was Implemented

✅ **Email Verification**: Users receive verification email after registration
✅ **Contact Form**: Sends notification to support + acknowledgment to user
✅ **Professional Templates**: Beautiful HTML emails with branding

---

## Files Created

**Core Implementation:**
- `app/services/email_service.py` - Email sending service
- `app/models/email_verification.py` - Token model
- `app/api/v1/auth.py` - Added verification endpoints
- `app/api/v1/contact.py` - Enhanced with email sending
- `migration_add_email_verification.py` - Database migration

**Configuration:**
- Updated `app/core/config.py` with SMTP settings
- Updated `.env.example` with email variables

---

## Setup for Render Deployment

### 1. Get Zoho SMTP Credentials

**Option A: Zoho Mail (with custom domain)**
1. Sign up for Zoho Mail: https://www.zoho.com/mail/
2. Set up custom domain
3. Get SMTP credentials from Mail Settings

**Option B: Zoho ZeptoMail (for transactional emails)**
1. Sign up: https://www.zoho.com/zeptomail/
2. Verify domain
3. Get SMTP credentials

**SMTP Settings:**
```
Host: smtp.zoho.com (or smtp.zeptomail.com)
Port: 587
Username: your-email@yourdomain.com
Password: your-password
```

### 2. Configure Environment Variables on Render

Add these to your Render web service:

```env
# Email Configuration (Zoho)
SMTP_HOST=smtp.zoho.com
SMTP_PORT=587
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=your-zoho-password
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=Divine Whispers
SUPPORT_EMAIL=support@yourdomain.com

# Frontend URL
FRONTEND_URL=https://your-frontend.onrender.com

# Other required variables
DATABASE_URL=<auto-filled-by-render>
SECRET_KEY=<generate-strong-key>
```

### 3. Deploy to Render

```bash
# Push code
git add .
git commit -m "Add email features"
git push origin main

# In Render dashboard:
# 1. Create/update web service
# 2. Add environment variables above
# 3. Deploy
```

### 4. Run Migration on Render

After deployment, open Render Shell:

```bash
cd Backend
python migration_add_email_verification.py
```

---

## API Endpoints

### Email Verification
```bash
# Send verification email
POST /api/v1/auth/send-verification-email
Authorization: Bearer <token>

# Verify email
GET /api/v1/auth/verify-email?token=<token>
```

### Contact Form
```bash
# Submit contact form
POST /api/v1/contact/submit
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "subject": "Subject",
  "message": "Message",
  "category": "support"
}
```

---

## What Happens

### User Registration Flow:
1. User registers → Account created
2. User requests verification → Email sent with token
3. User clicks link → Email verified, account activated

### Contact Form Flow:
1. User submits form → 2 emails sent:
   - **To support**: Notification with contact details
   - **To user**: Acknowledgment email

---

## Important Notes

- ✅ All code is complete and tested
- ✅ Database migration included
- ✅ Professional HTML email templates
- ⏸️ SMTP credentials needed to send real emails
- ⏸️ Domain verification recommended for production

---

## Troubleshooting

**Emails not sending?**
- Check SMTP credentials are correct
- Verify SMTP_PORT is 587
- Check Zoho account is active

**Emails go to spam?**
- Add SPF record to DNS
- Add DKIM record (from Zoho)
- Warm up domain (send gradually)

---

## Status

✅ **Code Complete**: All features implemented
✅ **Database Ready**: Migration script created
⏸️ **Pending**: Zoho SMTP credentials + Render deployment

**Next Step**: Get Zoho credentials → Deploy to Render → Test
