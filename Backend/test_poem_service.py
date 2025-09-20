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

        # Test get_poem_by_id with known poem
        print("\n--- Testing get_poem_by_id ---")
        test_poem_id = "Tianhou_99"
        print(f"Testing with poem ID: {test_poem_id}")

        poem_result = await poem_service.get_poem_by_id(test_poem_id)
        if poem_result:
            print("SUCCESS: Poem found!")
            print(f"  Type: {type(poem_result)}")
            print(f"  Title: {getattr(poem_result, 'title', 'N/A')}")
            print(f"  Temple: {getattr(poem_result, 'temple', 'N/A')}")
            print(f"  Fortune: {getattr(poem_result, 'fortune', 'N/A')}")
            print(f"  Attributes: {dir(poem_result)}")
        else:
            print("FAILED: Poem not found")

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_poem_service())