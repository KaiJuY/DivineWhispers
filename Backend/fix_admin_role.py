#!/usr/bin/env python3
"""
Fix admin role for admin@example.com user
"""

import asyncio
import sys
import os

# Add the Backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def fix_admin_role():
    """Fix the admin role for admin@example.com"""
    try:
        from app.core.database import async_session_maker
        from app.models.user import User, UserRole
        from sqlalchemy import select, update

        print("Fixing admin role for admin@example.com...")

        async with async_session_maker() as db:
            # Find the admin@example.com user
            result = await db.execute(
                select(User).where(User.email == "admin@example.com")
            )
            user = result.scalar_one_or_none()

            if not user:
                print("ERROR: User admin@example.com not found")
                return False

            print(f"Found user: {user.email} with current role: {user.role}")

            # Update the user's role to ADMIN
            await db.execute(
                update(User)
                .where(User.email == "admin@example.com")
                .values(role=UserRole.ADMIN)
            )

            await db.commit()
            print("SUCCESS: Updated admin@example.com role to ADMIN")

            # Verify the change
            result = await db.execute(
                select(User).where(User.email == "admin@example.com")
            )
            updated_user = result.scalar_one_or_none()
            print(f"Verified: {updated_user.email} now has role: {updated_user.role}")

            return True

    except Exception as e:
        print(f"ERROR: Failed to fix admin role: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(fix_admin_role())
    if result:
        print("\n✅ Admin role fixed successfully!")
        print("You can now use admin@example.com with admin privileges.")
    else:
        print("\n❌ Failed to fix admin role.")
    sys.exit(0 if result else 1)