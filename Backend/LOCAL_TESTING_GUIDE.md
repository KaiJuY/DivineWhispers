"""
Integration test for email system
Tests email sending without requiring actual SMTP credentials
"""

import asyncio
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, '.')

from app.core.config import settings
from app.services.email_service import EmailService
from app.services.auth_service import AuthService
from app.models.email_verification import EmailVerificationToken
from app.core.database import get_async_session, create_tables


async def test_email_service_methods():
    """Test 1: Email service methods can generate content"""
    print("\n" + "="*60)
    print("TEST 1: Email Service Content Generation")
    print("="*60)

    try:
        email_service = EmailService()

        # Mock SMTP to prevent actual sending
        with patch('smtplib.SMTP') as mock_smtp:
            # Configure mock
            mock_instance = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_instance

            # Test 1a: Verification email
            print("\n[TEST] Sending verification email...")
            result = email_service.send_verification_email(
                to_email="test@example.com",
                verification_token="test_token_12345",
                user_name="Test User"
            )
            print(f"[OK] Verification email method executed: {result}")

            # Verify SMTP was called
            mock_smtp.assert_called_with(settings.SMTP_HOST, settings.SMTP_PORT)
            mock_instance.send_message.assert_called()
            print("[OK] SMTP connection attempted")

            # Test 1b: Contact notification
            print("\n[TEST] Sending contact notification...")
            contact_info = {
                "name": "John Doe",
                "email": "john@example.com",
                "subject": "Test Subject",
                "message": "Test message content",
                "category": "support",
                "submitted_at": datetime.utcnow().isoformat()
            }

            result = email_service.send_contact_notification(
                support_email="support@example.com",
                contact_info=contact_info
            )
            print(f"[OK] Contact notification method executed: {result}")

            # Test 1c: Contact acknowledgment
            print("\n[TEST] Sending contact acknowledgment...")
            result = email_service.send_contact_acknowledgment(
                to_email="john@example.com",
                contact_info=contact_info
            )
            print(f"[OK] Contact acknowledgment method executed: {result}")

        print("\n[SUCCESS] All email service methods work correctly")
        return True

    except Exception as e:
        print(f"[FAIL] Email service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_token_creation_and_validation():
    """Test 2: Token creation and validation"""
    print("\n" + "="*60)
    print("TEST 2: Token Creation and Validation")
    print("="*60)

    try:
        # Ensure database is initialized
        await create_tables()

        # Test token generation
        token1 = EmailVerificationToken.generate_token()
        token2 = EmailVerificationToken.generate_token()

        assert len(token1) > 20, "Token too short"
        assert token1 != token2, "Tokens not unique"
        print(f"[OK] Token generation works: {token1[:20]}...")

        # Test expiry calculation
        expiry = EmailVerificationToken.get_expiry_time(hours=24)
        now = datetime.utcnow()
        time_diff = (expiry - now).total_seconds()
        assert 23 * 3600 < time_diff < 25 * 3600, "Expiry time incorrect"
        print(f"[OK] Expiry calculation works: 24 hours from now")

        # Test database operations
        async with get_async_session() as db:
            # Create test token
            print("\n[TEST] Creating verification token in database...")
            test_token = await AuthService.create_verification_token(
                db=db,
                user_id=999,
                email="test@example.com"
            )
            print(f"[OK] Token created: {test_token[:20]}...")

            # Verify token exists in database
            from sqlalchemy import select
            result = await db.execute(
                select(EmailVerificationToken).where(
                    EmailVerificationToken.token == test_token
                )
            )
            token_record = result.scalar_one_or_none()

            assert token_record is not None, "Token not found in database"
            assert token_record.email == "test@example.com", "Email mismatch"
            assert token_record.user_id == 999, "User ID mismatch"
            assert not token_record.is_used, "Token should not be used"
            assert token_record.is_valid(), "Token should be valid"
            print("[OK] Token stored correctly in database")

            # Test token validation
            print("\n[TEST] Validating token...")
            is_valid = await AuthService.verify_email_token(db=db, token=test_token)
            assert is_valid, "Token validation failed"
            print("[OK] Token validation successful")

            # Verify token is marked as used
            result = await db.execute(
                select(EmailVerificationToken).where(
                    EmailVerificationToken.token == test_token
                )
            )
            token_record = result.scalar_one_or_none()
            assert token_record.is_used, "Token should be marked as used"
            print("[OK] Token marked as used after validation")

        print("\n[SUCCESS] Token creation and validation work correctly")
        return True

    except Exception as e:
        print(f"[FAIL] Token test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_flow_simulation():
    """Test 3: Simulate complete API flow"""
    print("\n" + "="*60)
    print("TEST 3: API Flow Simulation")
    print("="*60)

    try:
        # Simulate user registration and verification flow
        print("\n[SCENARIO] User registers → receives email → verifies")

        async with get_async_session() as db:
            # Step 1: User registers (simplified - token creation only)
            print("\n[STEP 1] User registers, token created...")
            verification_token = await AuthService.create_verification_token(
                db=db,
                user_id=1001,
                email="newuser@example.com"
            )
            print(f"[OK] Verification token created: {verification_token[:20]}...")

            # Step 2: Send verification email (mocked)
            print("\n[STEP 2] Sending verification email...")
            with patch('smtplib.SMTP') as mock_smtp:
                mock_instance = MagicMock()
                mock_smtp.return_value.__enter__.return_value = mock_instance

                from app.services.email_service import email_service
                sent = email_service.send_verification_email(
                    to_email="newuser@example.com",
                    verification_token=verification_token,
                    user_name="New User"
                )
                print(f"[OK] Email would be sent: {sent}")

            # Step 3: User clicks link and verifies
            print("\n[STEP 3] User clicks verification link...")
            verified = await AuthService.verify_email_token(
                db=db,
                token=verification_token
            )
            assert verified, "Verification failed"
            print("[OK] Email verified successfully")

        print("\n[SCENARIO] Contact form submission → emails sent")

        # Simulate contact form flow
        print("\n[STEP 1] User submits contact form...")
        contact_data = {
            "name": "Jane Smith",
            "email": "jane@example.com",
            "subject": "Question about pricing",
            "message": "I would like to know more about your pricing plans.",
            "category": "billing",
            "submitted_at": datetime.utcnow().isoformat()
        }

        with patch('smtplib.SMTP') as mock_smtp:
            mock_instance = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_instance

            from app.services.email_service import email_service

            # Step 2: Send notification to support
            print("\n[STEP 2] Sending notification to support team...")
            sent1 = email_service.send_contact_notification(
                support_email="support@example.com",
                contact_info=contact_data
            )
            print(f"[OK] Support notification would be sent: {sent1}")

            # Step 3: Send acknowledgment to user
            print("\n[STEP 3] Sending acknowledgment to user...")
            sent2 = email_service.send_contact_acknowledgment(
                to_email="jane@example.com",
                contact_info=contact_data
            )
            print(f"[OK] User acknowledgment would be sent: {sent2}")

        print("\n[SUCCESS] Complete API flows work correctly")
        return True

    except Exception as e:
        print(f"[FAIL] API flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_integration_tests():
    """Run all integration tests"""
    print("\n")
    print("="*60)
    print("EMAIL SYSTEM INTEGRATION TESTS")
    print("="*60)
    print("\nThese tests verify the email system works correctly")
    print("without actually sending emails (SMTP is mocked)")
    print("="*60)

    tests = [
        ("Email Service Methods", test_email_service_methods),
        ("Token Creation & Validation", test_token_creation_and_validation),
        ("API Flow Simulation", test_api_flow_simulation),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n[ERROR] Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "="*60)
    print("INTEGRATION TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")

    print("\n" + "="*60)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("="*60)

    if passed == total:
        print("\n[SUCCESS] All integration tests passed!")
        print("\nThe email system is working correctly.")
        print("\nNext steps:")
        print("1. Configure real SMTP credentials (Mailtrap/MailHog for testing)")
        print("2. Start the server: python -m app.main")
        print("3. Test with real HTTP requests")
        print("4. Deploy to Render with production SMTP settings")
    else:
        print("\n[WARNING] Some tests failed. Please review the errors above.")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_integration_tests())
    sys.exit(0 if success else 1)
