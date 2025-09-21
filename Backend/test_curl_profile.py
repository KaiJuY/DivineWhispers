#!/usr/bin/env python3
"""
Test the user profile update endpoint with curl
"""

import subprocess
import json

def test_profile_with_curl():
    """Test profile update using curl"""
    try:
        print("Testing profile update with curl...")

        # First, let's try to login to get a valid token
        login_data = {
            "email": "admin@example.com",  # Default admin user
            "password": "admin123"         # Default admin password
        }

        # Use curl to login
        login_cmd = [
            'curl', '-X', 'POST',
            'http://localhost:8000/api/v1/auth/login',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps(login_data),
            '--silent'
        ]

        print("Attempting login with curl...")
        result = subprocess.run(login_cmd, capture_output=True, text=True)

        print(f"Login curl status: {result.returncode}")
        print(f"Login response: {result.stdout}")
        if result.stderr:
            print(f"Login stderr: {result.stderr}")

        if result.returncode != 0:
            print("Login failed")
            return False

        try:
            login_response = json.loads(result.stdout)
            token = login_response.get('tokens', {}).get('access_token')
        except json.JSONDecodeError:
            print("Failed to parse login response as JSON")
            return False

        if not token:
            print("No access token in login response")
            return False

        print(f"Login successful! Token: {token[:20]}...")

        # Now test the profile update
        profile_data = {"full_name": "Test Update Name via Curl"}

        profile_cmd = [
            'curl', '-X', 'PUT',
            'http://localhost:8000/api/v1/admin/users/1/profile',
            '-H', 'Content-Type: application/json',
            '-H', f'Authorization: Bearer {token}',
            '-d', json.dumps(profile_data),
            '--silent',
            '-i'  # Include response headers
        ]

        print(f"Testing profile update with data: {profile_data}")
        result = subprocess.run(profile_cmd, capture_output=True, text=True)

        print(f"Profile update curl status: {result.returncode}")
        print(f"Profile update response: {result.stdout}")
        if result.stderr:
            print(f"Profile update stderr: {result.stderr}")

        # Check if response contains HTTP 200
        if "HTTP/1.1 200" in result.stdout:
            print("SUCCESS: Profile update worked!")
            return True
        elif "HTTP/1.1 500" in result.stdout:
            print("FAILED: Still getting 500 error")
            return False
        else:
            print("UNKNOWN: Unexpected response")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = test_profile_with_curl()
    print(f"Test result: {result}")