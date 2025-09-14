#!/usr/bin/env python3
"""
Debug script to test ChromaDB query for specific poem
"""

import sys
import os
from pathlib import Path

# Add fortune_module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fortune_module'))

from fortune_module.unified_rag import UnifiedRAGHandler
from fortune_module.models import ChunkType

def main():
    print("Testing ChromaDB query for GuanYu poem 24...")

    rag = UnifiedRAGHandler()

    # Direct query to see what's in the database
    print("\n=== Direct Collection Query ===")
    try:
        results = rag.collection.query(
            query_texts=[""],
            where={
                "$and": [
                    {"chunk_type": {"$eq": ChunkType.POEM.value}},
                    {"temple": {"$eq": "GuanYu"}},
                    {"poem_id": {"$eq": 24}}
                ]
            },
            n_results=10
        )

        print(f"Found {len(results['ids'][0])} results:")
        for i, doc_id in enumerate(results['ids'][0]):
            metadata = results['metadatas'][0][i]
            print(f"  {i+1}. Doc ID: {doc_id}")
            print(f"     Metadata: {metadata}")
            print(f"     Content: {results['documents'][0][i][:100]}...")
            print()

    except Exception as e:
        print(f"Error with direct query: {e}")

    # Try the method call
    print("\n=== Method Call ===")
    try:
        chunks = rag.get_poem_by_temple_and_id("GuanYu", 24)
        print(f"Method returned {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks):
            print(f"  {i+1}. Keys: {list(chunk.keys())}")
            if 'temple' in chunk and 'poem_id' in chunk:
                print(f"     Temple: {chunk['temple']}, Poem ID: {chunk['poem_id']}")
    except Exception as e:
        print(f"Error with method call: {e}")

    # Check what's in the metadata for poem 24
    print("\n=== All Poem 24 Records ===")
    try:
        results = rag.collection.query(
            query_texts=[""],
            where={"poem_id": {"$eq": 24}},  # Without temple filter
            n_results=20
        )

        print(f"Found {len(results['ids'][0])} records with poem_id=24:")
        for i, doc_id in enumerate(results['ids'][0]):
            metadata = results['metadatas'][0][i]
            temple = metadata.get('temple', 'NO_TEMPLE')
            chunk_type = metadata.get('chunk_type', 'NO_TYPE')
            print(f"  {i+1}. Temple: {temple}, Type: {chunk_type}, DocID: {doc_id}")

    except Exception as e:
        print(f"Error querying poem 24: {e}")

if __name__ == "__main__":
    main()