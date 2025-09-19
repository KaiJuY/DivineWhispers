"""
Minimal ChromaDB test to isolate the schema issue
"""
import chromadb
import os
import logging

logging.basicConfig(level=logging.DEBUG)

print("=== Testing ChromaDB Initialization ===")
print(f"Current working directory: {os.getcwd()}")
print(f"ChromaDB version: {chromadb.__version__}")

# Test 1: Initialize with Backend path
try:
    print("\n--- Test 1: Backend path ---")
    client = chromadb.PersistentClient(path="chroma_db")
    print("SUCCESS: Backend path initialization successful")
    collections = client.list_collections()
    print(f"SUCCESS: Collections found: {len(collections)}")
    if collections:
        for col in collections:
            print(f"  - {col.name}: {col.count()} items")
except Exception as e:
    print(f"FAILED: Backend path failed: {e}")

# Test 2: Initialize with root path
try:
    print("\n--- Test 2: Root path ---")
    client = chromadb.PersistentClient(path="../chroma_db")
    print("SUCCESS: Root path initialization successful")
    collections = client.list_collections()
    print(f"SUCCESS: Collections found: {len(collections)}")
    if collections:
        for col in collections:
            print(f"  - {col.name}: {col.count()} items")
except Exception as e:
    print(f"FAILED: Root path failed: {e}")

# Test 3: Use absolute paths
backend_abs = os.path.abspath("chroma_db")
root_abs = os.path.abspath("../chroma_db")

try:
    print(f"\n--- Test 3: Absolute backend path ({backend_abs}) ---")
    client = chromadb.PersistentClient(path=backend_abs)
    print("SUCCESS: Absolute backend path initialization successful")
    collections = client.list_collections()
    print(f"SUCCESS: Collections found: {len(collections)}")
except Exception as e:
    print(f"FAILED: Absolute backend path failed: {e}")

try:
    print(f"\n--- Test 4: Absolute root path ({root_abs}) ---")
    client = chromadb.PersistentClient(path=root_abs)
    print("SUCCESS: Absolute root path initialization successful")
    collections = client.list_collections()
    print(f"SUCCESS: Collections found: {len(collections)}")
except Exception as e:
    print(f"FAILED: Absolute root path failed: {e}")