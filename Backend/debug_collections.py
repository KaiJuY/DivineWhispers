#!/usr/bin/env python3
"""
Debug script to check ChromaDB collections
"""

import chromadb

def main():
    print("Checking ChromaDB collections...")

    # Connect to ChromaDB
    client = chromadb.PersistentClient(path="./chroma_db")

    # List all collections
    collections = client.list_collections()

    print(f"Found {len(collections)} collections:")
    for i, coll in enumerate(collections):
        print(f"  {i+1}. Name: {coll.name}")
        print(f"      UUID: {coll.id}")

        # Get collection stats
        try:
            count = coll.count()
            print(f"      Items: {count}")

            # Peek at some items
            if count > 0:
                results = coll.peek(limit=3)
                print(f"      Sample IDs: {results['ids'][:3] if results['ids'] else 'None'}")
        except Exception as e:
            print(f"      Error getting stats: {e}")
        print()

if __name__ == "__main__":
    main()