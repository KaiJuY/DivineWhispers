#!/usr/bin/env python3

import asyncio
import sys
import os
import traceback
from datetime import datetime

# Add the Backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_auth_service():
    """Test the auth service directly"""
    try:
        print("=== Testing Auth Service Directly ===")
        
        # Import required modules
        from app.core.database import async_session_maker
        from app.services.auth_service import AuthService
        from app.schemas.auth import UserRegister
        # Import all models to ensure they're registered
        from app.models.chat_message import ChatSession, ChatMessage
        from app.models.user import User
        
        # Create test user data
        test_user = UserRegister(
            email="testuser@example.com",
            password="password123",
            confirm_password="password123",
            username="TestUser",
            birth_date="1990-01-01",
            gender="Male",
            location="Test Location"
        )
        
        print(f"Test user data: {test_user}")
        
        # Get database session
        async with async_session_maker() as db:
            print("Database session created successfully")
            
            try:
                print("Calling AuthService.register_user...")
                user, tokens = await AuthService.register_user(db, test_user, "127.0.0.1")
                print("Registration successful!")
                print(f"User ID: {user.user_id}")
                print(f"User email: {user.email}")
                print(f"Access token length: {len(tokens.access_token)}")
                print(f"Refresh token length: {len(tokens.refresh_token)}")
                
            except Exception as e:
                print(f"Registration failed with error: {type(e).__name__}: {str(e)}")
                traceback.print_exc()
                
    except Exception as e:
        print(f"Test setup failed: {type(e).__name__}: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_auth_service())