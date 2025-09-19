"""
Test unified_rag module in isolation
"""
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=== Testing UnifiedRAGHandler ===")
print(f"Current working directory: {os.getcwd()}")

try:
    from fortune_module.unified_rag import UnifiedRAGHandler
    print("SUCCESS: Imported UnifiedRAGHandler")

    # Test initialization
    print("\n--- Testing initialization ---")
    rag = UnifiedRAGHandler()
    print("SUCCESS: UnifiedRAGHandler initialized")

    # Test query
    print("\n--- Testing query ---")
    result = rag.query("love", top_k=5)
    print(f"SUCCESS: Query returned {len(result.chunks)} chunks")

    # Test stats
    print("\n--- Testing stats ---")
    stats = rag.get_collection_stats()
    print(f"SUCCESS: Stats: {stats}")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()