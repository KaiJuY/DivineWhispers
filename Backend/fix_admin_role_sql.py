#!/usr/bin/env python3
"""
Fix admin role for admin@example.com user using raw SQL
"""

import asyncio
import sys
import os

# Add the Backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def fix_admin_role_sql():
    """Fix the admin role for admin@example.com using raw SQL"""
    try:
        from app.core.database import async_session_maker
        from sqlalchemy import text

        print("Fixing admin role for admin@example.com using SQL...")

        async with async_session_maker() as db:
            # Check current role
            result = await db.execute(
                text("SELECT email, role FROM users WHERE email = 'admin@example.com'")
            )
            user_data = result.fetchone()

            if not user_data:
                print("ERROR: User admin@example.com not found")
                return False

            print(f"Found user: {user_data[0]} with current role: {user_data[1]}")

            # Update the user's role to ADMIN
            await db.execute(
                text("UPDATE users SET role = 'ADMIN' WHERE email = 'admin@example.com'")
            )

            await db.commit()
            print("SUCCESS: Updated admin@example.com role to ADMIN")

            # Verify the change
            result = await db.execute(
                text("SELECT email, role FROM users WHERE email = 'admin@example.com'")
            )
            updated_user = result.fetchone()
            print(f"Verified: {updated_user[0]} now has role: {updated_user[1]}")

            return True

    except Exception as e:
        print(f"ERROR: Failed to fix admin role: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(fix_admin_role_sql())
    if result:
        print("\nAdmin role fixed successfully!")
        print("You can now use admin@example.com with admin privileges.")
        print("Please log out and log back in for changes to take effect.")
    else:
        print("\nFailed to fix admin role.")
    sys.exit(0 if result else 1)