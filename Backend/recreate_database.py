#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the Backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def recreate_database():
    """Recreate the database to match current models"""
    try:
        print("=== Recreating Database ===")
        
        # Import database functions
        from app.core.database import drop_tables, create_tables
        
        print("1. Dropping existing tables...")
        await drop_tables()
        print("   Tables dropped successfully")
        
        print("2. Creating new tables with current model schema...")
        await create_tables()
        print("   Tables created successfully")
        
        print("=== Database Recreation Complete ===")
        
    except Exception as e:
        print(f"Database recreation failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(recreate_database())