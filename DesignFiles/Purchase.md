🛒 Purchase Page Implementation Plan (Extended with Multi-Market Payment Strategy)
Current State Analysis

✅ Frontend UI: Purchase page exists with coin packages, payment method selection
✅ Backend Wallet System: Comprehensive wallet/transaction models & APIs
✅ I18n Support: Purchase translations available in EN/ZH/JP
❌ Payment Gateway: Only mock implementation exists
❌ Frontend Service: No purchaseService for API integration
❌ Real Balance: Currently using mock userCoins (50)

Implementation Plan
Phase 1: Frontend Service Layer

Create Purchase Service (src/services/purchaseService.ts)

Package fetching from /api/v1/wallet/packages

Purchase initiation via /api/v1/wallet/purchase

Purchase completion via /api/v1/wallet/purchase/{id}/complete

Purchase history via /api/v1/wallet/purchases

Update App Store (src/stores/appStore.ts)

Connect userCoins to real wallet balance API

Add purchase state management

Replace mock 50 coins with real balance fetching

Update Purchase Page (src/pages/PurchasePage.tsx)

Replace TODO placeholder with real purchaseService calls

Add loading states for payment processing

Implement success/error handling

Add purchase confirmation modal

Phase 2: Payment Gateway Integration (Strategy Pattern + Multi-Market)

Payment Service Architecture

Implement a PaymentStrategy interface (e.g. createPaymentIntent(), handleWebhook(), verifyPayment())

Concrete strategies:

TapPayStrategy → for Taiwan users

StripeCreditCardStrategy → for US and Japan users

Strategy selection based on user.country (or user.locale)

Future providers (PayPal, Apple Pay, Google Pay) can be added without modifying core logic

Enabled vs Disabled Payment Methods

Enabled in v1: Credit card payments only

TapPay (Taiwan)

Stripe (US/Japan)

Disabled in v1: PayPal, Apple Pay, Google Pay (UI shows "Coming Soon")

Backend Payment Service (app/services/payment_service.py)

Implement PaymentStrategy base class

Implement TapPayStrategy and StripeCreditCardStrategy

Transaction flow:

Create payment intent/session

Handle webhooks (succeeded / failed)

Verify amount vs. package price

Update transaction state (pending → success/failed)

Credit user wallet on success

Frontend Payment Integration

Integrate TapPay SDK for Taiwan users

Integrate Stripe Elements for US/Japan users

Only credit card payment available; other methods disabled

Automatically handle 3D Secure (fraud protection)

Show clear error messages for failed/cancelled payments

Phase 3: Security & Testing

Security Implementation

HTTPS enforcement for payments

Webhook signature verification

Idempotency for duplicate transactions (transaction_id + user_id)

Transaction states: pending / success / failed

PCI compliance handled by Stripe / TapPay

Testing with Playwright

Test package selection flow

Mock Stripe & TapPay responses for reliability

Test successful purchase flow

Test failed/cancelled payment scenarios

Test balance updates after purchase

Test idempotency on repeated webhook events

Ensure non-enabled payment methods are not available

Phase 4: Production Setup Requirements

Payment Accounts Setup

TapPay (Taiwan)

Create TapPay merchant account

Configure API keys, webhooks

Stripe (US/Japan)

Create Stripe account for USD transactions

Configure API keys, webhooks

Environment Variables

TAPPAY_PARTNER_KEY=...
TAPPAY_MERCHANT_ID=...
TAPPAY_APP_ID=...
TAPPAY_APP_KEY=...

STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...


Domain Configuration

SSL certificate for HTTPS

Webhook endpoints for both TapPay and Stripe

Phase 5: Reconciliation & Admin Dashboard

Immediate Reconciliation

Compare webhook event with DB record immediately

On mismatch, mark transaction as failed → user must retry

Admin Dashboard Features

Search/filter transactions by user, status, date

View wallet balance history

Audit trail for all payment attempts

Implementation Order

Development: Implement TapPayStrategy (Taiwan) + StripeCreditCardStrategy (US/Japan)

Disable all other payment methods in UI

Test TapPay & Stripe flows in sandbox/test mode

Deploy to staging with test credentials

Go live with production keys after business verification

Technical Flow

User selects package → PaymentContext selects strategy based on user.country →
Payment strategy creates payment intent/session →
User completes payment (3D Secure if required) →
Webhook notifies backend →
Backend verifies transaction →
Credits wallet →
Frontend updates balance

Files to Create/Modify

✨ New: src/services/purchaseService.ts

✨ New: Backend/app/services/payment_service.py

✨ New: Backend/app/services/payment_strategies/base.py (PaymentStrategy interface)

✨ New: Backend/app/services/payment_strategies/tappay_strategy.py

✨ New: Backend/app/services/payment_strategies/stripe_credit_card.py

✨ New: Backend/app/api/v1/webhooks.py

🔧 Modify: src/pages/PurchasePage.tsx

🔧 Modify: src/stores/appStore.ts

🔧 Modify: Backend/app/main.py (add webhook routes)

Testing Strategy

Playwright tests for TapPay (TW) & Stripe (US/Japan) flows

Mock webhook responses for consistent results

Verify transaction states (pending → success/failed)

Ensure disabled payment methods cannot be selected

Test idempotency on repeated webhook events

Test authentication failures / cancellations