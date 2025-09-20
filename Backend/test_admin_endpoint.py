#!/usr/bin/env python3
"""
Test the admin endpoint poem logic without authentication
"""

import asyncio
import sys
import os

# Add the Backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_admin_poem_endpoint():
    """Test the admin poem endpoint logic"""
    try:
        from app.services.poem_service import poem_service
        from datetime import datetime

        print("Testing admin poem endpoint logic...")

        # Initialize the poem service
        await poem_service.initialize_system()
        print("SUCCESS: Poem service initialized")

        # Test poem ID parsing and lookup
        poem_id = "Tianhou_99"
        print(f"\nTesting with poem ID: {poem_id}")

        # Parse poem_id (same logic as admin endpoint)
        if "_" in poem_id:
            temple, numeric_id = poem_id.rsplit("_", 1)
        else:
            raise Exception("Invalid poem ID format")

        print(f"SUCCESS: Parsed - temple: {temple}, numeric_id: {numeric_id}")

        # Get poem details (same logic as admin endpoint)
        poem_data = await poem_service.get_poem_by_id(f"{temple}_{numeric_id}")

        if not poem_data:
            raise Exception("Poem not found")

        print("SUCCESS: Poem found!")

        # Format response (same logic as admin endpoint)
        result = {
            "id": poem_id,
            "title": getattr(poem_data, "title", "Untitled"),
            "deity": getattr(poem_data, "temple", temple),
            "chinese": getattr(poem_data, "poem", ""),
            "fortune": getattr(poem_data, "fortune", ""),
            "analysis": getattr(poem_data, "analysis", {}),
            "topics": getattr(poem_data, "topics", []),
            "metadata": {
                "temple": temple,
                "poem_id": numeric_id,
                "last_modified": datetime.utcnow().isoformat(),
                "usage_count": 0
            }
        }

        print("SUCCESS: Response formatted successfully!")
        print(f"  Title: {result['title']}")
        print(f"  Deity: {result['deity']}")
        print(f"  Fortune: {result['fortune']}")
        print(f"  Chinese: {result['chinese'][:50]}..." if len(result['chinese']) > 50 else f"  Chinese: {result['chinese']}")

        return True

    except Exception as e:
        print(f"ERROR: Error testing admin endpoint: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_admin_poem_endpoint())
    sys.exit(0 if result else 1)