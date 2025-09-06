#!/usr/bin/env python3
"""
Simple ChromaDB initialization - just create the collection
"""
import os
import chromadb

# Set environment variables
os.environ['HOME'] = '/app/home'
os.environ['TRANSFORMERS_CACHE'] = '/app/transformers_cache'
os.environ['SENTENCE_TRANSFORMERS_HOME'] = '/app/sentence_transformers'
os.environ['HF_HOME'] = '/app/transformers_cache'

try:
    print("Creating ChromaDB client...")
    client = chromadb.PersistentClient(path="/app/chroma_db")
    
    print("Creating collection...")
    collection = client.get_or_create_collection(
        name="fortune_knowledge",
        metadata={"hnsw:space": "cosine"}
    )
    
    print("Adding minimal test data...")
    # Add one test entry to ensure collection works
    collection.add(
        documents=["Test fortune poem for initialization"],
        metadatas=[{
            "chunk_type": "poem",
            "temple": "test",
            "poem_id": "1",
            "title": "Test Fortune",
            "fortune": "good_fortune",
            "language": "en"
        }],
        ids=["test_1"]
    )
    
    print("Testing collection query...")
    results = collection.query(
        query_texts=["test"],
        n_results=1
    )
    
    print(f"Collection created successfully with {collection.count()} items")
    print("✅ ChromaDB initialization completed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()