#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the Backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_deities_api():
    """Test the deities API endpoints"""
    try:
        print("=== Testing Deities API ===")
        
        # Import required modules
        from app.services.deity_service import deity_service
        
        print("1. Testing get_all_deities...")
        deities = await deity_service.get_all_deities()
        print(f"   Found {len(deities)} deities")
        
        for deity in deities:
            print(f"   - {deity.name} ({deity.id}): {deity.total_fortunes} fortunes")
        
        print("\n2. Testing get_deity_by_id for 'guan_yin'...")
        guan_yin = await deity_service.get_deity_by_id("guan_yin")
        if guan_yin:
            print(f"   Found: {guan_yin.deity.name}")
            print(f"   Description: {guan_yin.deity.description}")
            print(f"   Fortune categories: {guan_yin.fortune_categories}")
            print(f"   Sample fortunes: {guan_yin.sample_fortunes}")
        else:
            print("   Not found")
            
        print("\n3. Testing get_deity_fortune_numbers for 'guan_yin'...")
        numbers = await deity_service.get_deity_fortune_numbers("guan_yin")
        if numbers:
            print(f"   Deity: {numbers.deity_name}")
            print(f"   Total available: {numbers.total_available}")
            print(f"   First 10 numbers: {[n.number for n in numbers.numbers[:10] if n.is_available]}")
        else:
            print("   Not found")
        
        print("\n=== Deities API Test Complete ===")
        
    except Exception as e:
        print(f"Test failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_deities_api())