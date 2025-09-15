#!/usr/bin/env python3
"""
Test script to check poem service directly
"""

import asyncio
import sys
from pathlib import Path

# Add Backend to path
backend_path = Path(__file__).parent / "Backend"
sys.path.insert(0, str(backend_path))

from app.services.poem_service import poem_service
from app.services.deity_service import deity_service

async def test_poem_service():
    print("=== Testing Poem Service ===")

    try:
        # Test initialization
        print("1. Initializing poem service...")
        init_success = await poem_service.initialize_system()
        print(f"   Initialization success: {init_success}")

        # Test deity service
        print("\n2. Testing deity service...")
        deity = await deity_service.get_deity_by_id("guan_yin")
        if deity:
            print(f"   Deity found: {deity.deity.name}")
        else:
            print("   ERROR: Deity not found")

        # Test temple name lookup
        temple_name = deity_service.get_temple_name("guan_yin")
        print(f"   Temple name: {temple_name}")

        # Test poem lookup
        print("\n3. Testing poem lookup...")
        poem_id = f"{temple_name}_42"
        print(f"   Looking for poem: {poem_id}")

        fortune_data = await poem_service.get_poem_by_id(poem_id)
        if fortune_data:
            print(f"   Poem found: {fortune_data.title}")
            print(f"   Poem ID: {fortune_data.id}")
        else:
            print("   WARNING: Poem not found - this could be the issue!")

        # Test health check
        print("\n4. Testing health check...")
        health = await poem_service.health_check()
        print(f"   ChromaDB Status: {health.chroma_db_status}")
        print(f"   System Status: {health.system_status}")

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_poem_service())