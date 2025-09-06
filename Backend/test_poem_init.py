#!/usr/bin/env python3
import os
import asyncio
import logging

# Set up environment
os.environ['TRANSFORMERS_CACHE'] = '/app/transformers_cache'
os.environ['SENTENCE_TRANSFORMERS_HOME'] = '/app/sentence_transformers'
os.environ['CHROMA_DB_PATH'] = '/app/chroma_db'

logging.basicConfig(level=logging.INFO)

async def test_poem_service():
    try:
        from app.services.poem_service import poem_service
        
        # Reset the service
        poem_service._initialized = False
        
        # Try to initialize
        success = await poem_service.initialize_system()
        
        if success:
            print("✅ Poem service initialized successfully")
            
            # Test getting categories
            categories = await poem_service.get_poem_categories()
            print(f"Categories found: {list(categories.keys()) if categories else 'None'}")
            
            if categories:
                print("✅ Poem service is working correctly!")
                return True
            else:
                print("⚠️ Poem service initialized but no categories found")
                return False
        else:
            print("❌ Poem service initialization failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_poem_service())
    print(f"Result: {result}")