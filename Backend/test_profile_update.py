#!/usr/bin/env python3
"""
Test the user profile update endpoint directly
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the Backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_profile_update():
    """Test the profile update logic directly"""
    try:
        from app.core.database import get_db, engine, async_session_maker
        from app.models.user import User
        from app.models.audit import AuditLog, ActionType
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select

        print("Testing profile update endpoint logic...")

        # Create a test session
        async with async_session_maker() as db:

            # Get first user for testing
            result = await db.execute(select(User).limit(1))
            user = result.scalar_one_or_none()

            if not user:
                print("ERROR: No users found in database")
                return False

            print(f"SUCCESS: Found test user: {user.email} (ID: {user.user_id})")

            # Test profile data update
            profile_data = {"full_name": "Test Updated Name"}
            user_id = user.user_id

            print(f"Testing profile update with data: {profile_data}")

            # Get target user
            target_user = await db.scalar(select(User).where(User.user_id == user_id))
            if not target_user:
                print("ERROR: User not found")
                return False

            print(f"SUCCESS: Target user found: {target_user.email}")

            # Allowed profile fields (same as endpoint)
            allowed_fields = ["full_name", "phone", "birth_date", "location", "preferred_language"]
            updated_fields = []

            print(f"Allowed fields: {allowed_fields}")

            for field in allowed_fields:
                if field in profile_data:
                    old_value = getattr(target_user, field, None)
                    new_value = profile_data[field]
                    print(f"Updating {field}: '{old_value}' -> '{new_value}'")
                    setattr(target_user, field, new_value)
                    updated_fields.append(field)

            if updated_fields:
                target_user.updated_at = datetime.utcnow()
                print(f"Updated fields: {updated_fields}")
                print("Committing changes...")
                await db.commit()
                await db.refresh(target_user)
                print("SUCCESS: Changes committed")
            else:
                print("No fields to update")

            # Create audit log
            print("Creating audit log...")
            audit_log = AuditLog(
                user_id=target_user.user_id,  # Using same user as admin for test
                action=ActionType.UPDATE,
                resource_type="user_profile",
                resource_id=str(user_id),
                details={
                    "updated_fields": updated_fields,
                    "target_user": target_user.email,
                    "updated_by": target_user.email
                }
            )
            db.add(audit_log)
            await db.commit()
            print("SUCCESS: Audit log created")

            result = {
                "success": True,
                "user_id": user_id,
                "updated_fields": updated_fields,
                "updated_by": target_user.email,
                "updated_at": target_user.updated_at
            }

            print("SUCCESS: Profile update completed!")
            print(f"Result: {result}")
            return True

    except Exception as e:
        print(f"ERROR: Error testing profile update: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_profile_update())
    sys.exit(0 if result else 1)