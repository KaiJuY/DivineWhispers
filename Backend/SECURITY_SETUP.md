# Security Setup Guide for Divine Whispers

## ✅ CRITICAL Security Issues - FIXED

### 1. SECRET_KEY Security ✓
**Status**: FIXED
- Development `.env` now has a secure 64-character random key
- Production `.env.production` requires manual key generation
- `config.py` now uses environment variables with safe fallback

**Action Required for Production**:
```bash
# Generate a secure production key:
python -c "import secrets; print(secrets.token_hex(32))"

# Copy the output and update your production .env file:
SECRET_KEY=<paste_generated_key_here>
```

### 2. Password Complexity Requirements ✓
**Status**: ENABLED
- Minimum length: 12 characters (increased from 8)
- Uppercase letters: REQUIRED
- Lowercase letters: REQUIRED
- Numbers: REQUIRED
- Symbols: REQUIRED

**Current Settings**:
```python
PASSWORD_MIN_LENGTH=12
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SYMBOLS=true
```

### 3. Database Credentials ✓
**Status**: FIXED
- `config.py` now reads `DATABASE_URL` from environment variables
- No hardcoded credentials in code
- Falls back to SQLite for local development only

### 4. CORS Configuration ✓
**Status**: RESTRICTED
- Default now allows only `localhost:3000` and `127.0.0.1:3000`
- Override in `.env` with `ALLOWED_HOSTS` for production domains

**Production Example**:
```bash
ALLOWED_HOSTS=["https://divinewhispers.com", "https://www.divinewhispers.com"]
```

### 5. Refresh Token Expiration ✓
**Status**: REDUCED
- Changed from 7 days to 3 days
- Reduces risk window for stolen tokens

---

## 🔐 Production Deployment Checklist

### Before Deploying to Production:

1. **Generate New SECRET_KEY**
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Update in production `.env` file

2. **Set Strong Database Password**
   ```bash
   # Generate secure password:
   python -c "import secrets, string; chars = string.ascii_letters + string.digits + string.punctuation; print(''.join(secrets.choice(chars) for _ in range(32)))"
   ```
   Update `POSTGRES_PASSWORD` and `DATABASE_URL` in production `.env`

3. **Configure CORS for Production Domains**
   ```bash
   ALLOWED_HOSTS=["https://your-domain.com", "https://www.your-domain.com"]
   ```

4. **Disable Debug Mode**
   ```bash
   DEBUG=false
   ```

5. **Set Production LLM API Key** (if using OpenAI)
   ```bash
   OPENAI_API_KEY=sk-proj-your-real-api-key
   LLM_PROVIDER=openai
   ```

6. **Secure Email Credentials** (if using SMTP)
   - Use app-specific passwords, not account passwords
   - Store in environment variables only

---

## 🛡️ Additional Security Recommendations

### Implemented ✓
- ✅ Bcrypt password hashing
- ✅ JWT token authentication
- ✅ Token blacklist on logout
- ✅ Password complexity validation
- ✅ Environment variable configuration

### Consider Implementing:
- 🔲 Rate limiting on authentication endpoints (already configured in `.env`)
- 🔲 Multi-factor authentication (2FA)
- 🔲 IP-based login restrictions
- 🔲 Account lockout after failed login attempts
- 🔲 Security audit logging
- 🔲 HTTPS enforcement in production
- 🔲 Content Security Policy headers
- 🔲 Database connection encryption (SSL/TLS)

---

## 📝 Password Policy Enforcement

Users must now create passwords with:
- At least 12 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one number (0-9)
- At least one symbol (!@#$%^&*, etc.)

Example valid passwords:
- `MyP@ssw0rd2025!`
- `SecureF0rtune#2024`
- `Divine$Whisper9`

---

## 🚨 Never Commit These to Git:
- `.env` (development secrets)
- `.env.production` (production secrets)
- Any file containing `SECRET_KEY`, `OPENAI_API_KEY`, or database passwords

**Verify `.gitignore` includes**:
```
.env
.env.production
.env.local
*.db
*.sqlite
```

---

## 🔍 Security Testing Commands

### Test Password Validation:
```bash
# Should FAIL (too short, no symbols):
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Short123"}'

# Should SUCCEED:
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"MySecure@Pass123"}'
```

### Verify SECRET_KEY is not default:
```bash
grep -r "your-super-secret-key" Backend/.env*
# Should return NOTHING or only .env.example
```

---

## 📞 Need Help?

If you encounter any security-related issues:
1. Check the application logs in `Backend/logs/`
2. Verify all environment variables are set correctly
3. Test with development `.env` first before production

**Last Updated**: 2025-10-03
**Security Review Completed**: ✅ CRITICAL and HIGH priority issues resolved
