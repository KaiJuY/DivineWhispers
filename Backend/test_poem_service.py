"""
Test poem_service in isolation
"""
import asyncio
import sys
import os

# Add the app path
sys.path.append('app')

print("=== Testing PoemService ===")
print(f"Current working directory: {os.getcwd()}")

async def test_poem_service():
    try:
        from app.services.poem_service import poem_service
        print("SUCCESS: Imported poem_service")

        # Test initialization
        print("\n--- Testing initialization ---")
        await poem_service.ensure_initialized()
        print("SUCCESS: poem_service initialized")

        # Test get_all_poems_for_admin
        print("\n--- Testing get_all_poems_for_admin ---")
        result = await poem_service.get_all_poems_for_admin(page=1, limit=5)
        print(f"SUCCESS: Got {len(result.get('poems', []))} poems")
        print(f"Total available: {result.get('pagination', {}).get('total', 0)}")
        print(f"Result structure: {list(result.keys())}")

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_poem_service())