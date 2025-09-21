#!/usr/bin/env python3
"""
Test the user profile update endpoint via HTTP
"""

import asyncio
import aiohttp
import json

async def test_profile_http():
    """Test the profile update via HTTP to see exact error"""
    try:
        print("Testing profile update via HTTP...")

        # First, let's try to login to get a valid token
        login_data = {
            "email": "admin@example.com",  # Default admin user
            "password": "admin123"         # Default admin password
        }

        async with aiohttp.ClientSession() as session:
            # Try to login
            print("Attempting login...")
            async with session.post('http://localhost:8000/api/v1/auth/login', json=login_data) as resp:
                if resp.status == 200:
                    login_result = await resp.json()
                    print(f"Login successful! Token type: {type(login_result.get('access_token'))}")
                    token = login_result.get('access_token')
                else:
                    print(f"Login failed with status {resp.status}")
                    text = await resp.text()
                    print(f"Login error: {text}")

                    # Try to get list of users to understand structure
                    print("Trying to get users without auth...")
                    async with session.get('http://localhost:8000/api/v1/admin/users') as resp2:
                        print(f"Users endpoint status: {resp2.status}")
                        if resp2.status != 200:
                            text2 = await resp2.text()
                            print(f"Users error: {text2}")
                    return False

            # Now test the profile update
            headers = {'Authorization': f'Bearer {token}'}
            profile_data = {"full_name": "Test Update Name"}

            print(f"Testing profile update with data: {profile_data}")
            print(f"Using token: {token[:20]}...")

            # Test with user ID 1 (assuming it exists)
            user_id = 1
            async with session.put(
                f'http://localhost:8000/api/v1/admin/users/{user_id}/profile',
                json=profile_data,
                headers=headers
            ) as resp:
                print(f"Profile update status: {resp.status}")
                text = await resp.text()
                print(f"Profile update response: {text}")

                if resp.status == 200:
                    print("SUCCESS: Profile update worked!")
                    return True
                else:
                    print(f"FAILED: Profile update failed with status {resp.status}")
                    return False

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_profile_http())
    print(f"Test result: {result}")