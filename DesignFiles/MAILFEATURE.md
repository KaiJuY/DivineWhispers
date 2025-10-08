# SaaS MVP Feature Checklist

This document outlines the features that a FastAPI + React SaaS developer should implement before deployment, with phased development recommendations and reuse-first approach.

---

## Phase 1: User Registration & Email Verification

### Feature Requirements

* Users can register an account (email + password)
* The system sends a verification email to the user's inbox
* Users click the verification link to activate their account

### Development Steps

1. **Backend Logic Reuse**

   * Check existing system for reusable registration or email-sending APIs
   * If reusable, integrate and adapt existing logic
   * Only implement new logic if no suitable components exist

2. **FastAPI Backend**

   * Create User model and PostgreSQL table (placeholder if DB migration is deferred)
   * Set up `/register` API
   * Generate a verification token (JWT or UUID)
   * Store token with expiration in the database
   * Send verification email via Zoho SMTP
   * Create `/verify-email` API to validate the token

3. **React Frontend**

   * Registration form (Email, Password)
   * POST request to `/register`
   * Display registration success message
   * Display verification result after clicking the email link

### Testing

* Use Mailtrap or similar service to test emails
* Validate token expiration and error handling

---

## Phase 2: Contact Us Feature

### Feature Requirements

* Users can enter Name, Email, and Message
* On form submission:

  1. Backend sends email to [support@mydomain.com](mailto:support@mydomain.com)
  2. Backend sends an automatic acknowledgment email to the user
* Frontend displays a "Successfully Sent" message

### Development Steps

1. **Backend Logic Reuse**

   * Check existing system for reusable email-sending or message-handling APIs
   * Use existing functions where possible
   * Only implement new logic if no suitable components exist

2. **FastAPI Backend**

   * Create `/contact-us` POST API
   * Validate required fields and email format
   * Send email to support using Zoho SMTP
   * Send automatic acknowledgment email
   * Optionally, store messages in DB for future admin review (placeholder if DB migration is deferred)
   * Abuse prevention:

     * Rate limit per IP/account
     * Optionally add reCAPTCHA

3. **React Frontend**

   * Contact Us form (Name, Email, Message)
   * fetch POST to `/contact-us`
   * Display loading, success, and error messages

### Testing

* Test email sending locally or via Mailtrap
* Simulate abuse scenarios for rate limiting

---

## Phase 3: Environment & Pre-Deployment Preparation

### Tasks

* **Environment Variables Setup**

  * `DATABASE_URL` → Placeholder for future DB migration
  * `ZOHO_SMTP_USER` / `ZOHO_SMTP_PASS` / `SMTP_HOST` / `SMTP_PORT`
* **Database**

  * Placeholder setup for PostgreSQL tables if DB migration is deferred
* **Testing**

  * Verify registration + email verification functionality
  * Verify Contact Us functionality
  * Validate frontend form checks and user feedback

---

## Phase 4: Deployment Preparation (Render)

### Steps

* Reserve space on Render for Web Service, Static Site, and PostgreSQL
* Configure environment variables
* Ensure placeholder database and email logic are functioning
* Final full migration to Render can be performed once all features are complete

---

## Phase 5 (Optional): Advanced Features

* Frontend real-time form validation
* Store Contact Us messages in DB + admin dashboard
* Enhance security: JWT, CSRF, XSS protection
* User behavior analytics / logging
* Future database migration to Supabase / Neon

---

> 📝 **Recommendation**: Implement features in the sequence provided. Reuse existing system logic and APIs wherever possible; only implement new logic when necessary. Focus on creating a functional MVP first, then prepare for full Render deployment and future advanced features.
