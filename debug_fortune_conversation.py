#!/usr/bin/env python3
"""
Debug script for fortune-conversation API endpoint
Tests authentication and captures 500 error details
"""

import requests
import json
import sys
import traceback
from datetime import datetime

# Backend API base URL
BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def register_test_user():
    """Register a test user for debugging"""
    print_section("REGISTERING TEST USER")

    test_user_data = {
        "email": "debug_test@divinewhispers.com",
        "password": "TestPassword123!",
        "confirm_password": "TestPassword123!",
        "username": "debug_tester"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=test_user_data,
            headers={"Content-Type": "application/json"}
        )

        print(f"Registration Status Code: {response.status_code}")
        print(f"Registration Response: {response.text}")

        if response.status_code == 201:
            data = response.json()
            return data.get("tokens", {}).get("access_token")
        elif response.status_code == 400 and ("already exists" in response.text.lower() or "already registered" in response.text.lower()):
            print("User already exists, trying to login...")
            return login_test_user()
        else:
            print(f"Registration failed: {response.text}")
            return None

    except Exception as e:
        print(f"Registration error: {e}")
        traceback.print_exc()
        return None

def login_test_user():
    """Login with test user credentials"""
    print_section("LOGGING IN TEST USER")

    login_data = {
        "email": "debug_test@divinewhispers.com",
        "password": "TestPassword123!"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )

        print(f"Login Status Code: {response.status_code}")
        print(f"Login Response: {response.text}")

        if response.status_code == 200:
            data = response.json()
            return data.get("tokens", {}).get("access_token")
        else:
            print(f"Login failed: {response.text}")
            return None

    except Exception as e:
        print(f"Login error: {e}")
        traceback.print_exc()
        return None

def test_fortune_conversation_endpoint(access_token):
    """Test the fortune-conversation endpoint that's causing 500 error"""
    print_section("TESTING FORTUNE-CONVERSATION ENDPOINT")

    # Test data matching the schema
    fortune_data = {
        "deity_id": "guan_yin",
        "fortune_number": 42,
        "initial_question": "What guidance do you have for my career decisions?"
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        print(f"Making request to: {BASE_URL}/api/v1/chat/fortune-conversation")
        print(f"Request headers: {headers}")
        print(f"Request data: {json.dumps(fortune_data, indent=2)}")

        response = requests.post(
            f"{BASE_URL}/api/v1/chat/fortune-conversation",
            json=fortune_data,
            headers=headers,
            timeout=30
        )

        print(f"\nResponse Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")

        if response.status_code == 500:
            print("\n[ERROR] CONFIRMED 500 ERROR!")
            try:
                error_data = response.json()
                print(f"Error Details: {json.dumps(error_data, indent=2)}")
            except:
                print("Response is not valid JSON")
        elif response.status_code == 200:
            print("\n[SUCCESS] SUCCESS!")
            data = response.json()
            print(f"Success Data: {json.dumps(data, indent=2)}")
        else:
            print(f"\n[WARNING] Unexpected status code: {response.status_code}")

    except Exception as e:
        print(f"Request error: {e}")
        traceback.print_exc()

def test_deity_endpoint(access_token):
    """Test the deity endpoint to see if that's working"""
    print_section("TESTING DEITY ENDPOINT")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        # Test get all deities
        response = requests.get(f"{BASE_URL}/api/v1/deities", headers=headers)
        print(f"Get All Deities Status: {response.status_code}")
        print(f"Get All Deities Response: {response.text[:200]}...")

        # Test get specific deity
        response = requests.get(f"{BASE_URL}/api/v1/deities/guan_yin", headers=headers)
        print(f"Get Guan Yin Deity Status: {response.status_code}")
        print(f"Get Guan Yin Response: {response.text[:200]}...")

    except Exception as e:
        print(f"Deity endpoint error: {e}")

def test_fortune_endpoint(access_token):
    """Test the fortune endpoint to check if poem service is working"""
    print_section("TESTING FORTUNE ENDPOINT")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        # Test get daily fortune (no auth required) - check both possible paths
        response = requests.get(f"{BASE_URL}/api/v1/fortune/daily")
        print(f"Daily Fortune Status: {response.status_code}")
        print(f"Daily Fortune Response: {response.text[:200]}...")

        # Try without the double prefix
        response = requests.get(f"{BASE_URL}/api/v1/fortune/fortune/daily")
        print(f"Alt Daily Fortune Status: {response.status_code}")
        print(f"Alt Daily Fortune Response: {response.text[:200]}...")

        # Test health endpoint
        response = requests.get(f"{BASE_URL}/api/v1/fortune/health", headers=headers)
        print(f"Fortune Health Status: {response.status_code}")
        print(f"Fortune Health Response: {response.text[:200]}...")

    except Exception as e:
        print(f"Fortune endpoint error: {e}")

def verify_backend_running():
    """Verify the backend is running"""
    print_section("CHECKING BACKEND STATUS")

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Health check status: {response.status_code}")
        print(f"Health check response: {response.text}")
        return True
    except requests.exceptions.ConnectionError:
        print("[ERROR] Backend is not running on localhost:8000")
        return False
    except Exception as e:
        print(f"Health check error: {e}")
        return False

def test_auth_endpoints(access_token):
    """Test auth-related endpoints to verify token works"""
    print_section("TESTING AUTH TOKEN VALIDITY")

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        # Test /me endpoint
        response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
        print(f"/me endpoint status: {response.status_code}")
        print(f"/me response: {response.text}")

        if response.status_code == 200:
            print("[SUCCESS] Authentication token is valid")
            return True
        else:
            print("[ERROR] Authentication token is invalid")
            return False

    except Exception as e:
        print(f"Auth test error: {e}")
        return False

def main():
    print("[DEBUG] Divine Whispers Fortune-Conversation Debug Script")
    print(f"[INFO] Started at: {datetime.now()}")

    # Check if backend is running
    if not verify_backend_running():
        print("[ERROR] Backend is not accessible. Please start the backend server.")
        sys.exit(1)

    # Get access token (register or login)
    access_token = register_test_user()

    if not access_token:
        print("[ERROR] Failed to get access token")
        sys.exit(1)

    print(f"[SUCCESS] Got access token: {access_token[:20]}...")

    # Verify token works
    if not test_auth_endpoints(access_token):
        print("[ERROR] Token verification failed")
        sys.exit(1)

    # Test related endpoints first to understand the issue
    test_deity_endpoint(access_token)
    test_fortune_endpoint(access_token)

    # Test the problematic endpoint
    test_fortune_conversation_endpoint(access_token)

    print(f"\n[DONE] Debug completed at: {datetime.now()}")

if __name__ == "__main__":
    main()