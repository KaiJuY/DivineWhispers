#!/usr/bin/env python3
"""
Test if ChromaDB contains rag_analysis and _llm_meta fields
"""

import asyncio
import sys
import os

# Add the Backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_chroma_fields():
    """Test if ChromaDB contains the enhanced fields"""
    try:
        from fortune_module.unified_rag import UnifiedRAGHandler

        print("Testing ChromaDB fields...")

        # Initialize RAG handler
        rag = UnifiedRAGHandler()
        print("SUCCESS: RAG handler created")

        # Get collection info
        stats = rag.get_collection_stats()
        print(f"Collection stats: {stats}")

        # Try to get a specific poem chunk that should have rag_analysis
        result = rag.query("rag_analysis", top_k=5)
        print(f"Query result type: {type(result)}")
        print(f"Found {len(result.chunks)} chunks for rag_analysis query")

        if hasattr(result, 'chunks') and result.chunks:
            chunk = result.chunks[0]
            print(f"\nChunk type: {type(chunk)}")
            print(f"Chunk keys: {list(chunk.keys()) if isinstance(chunk, dict) else dir(chunk)}")

            if isinstance(chunk, dict):
                chunk_id = chunk.get('chunk_id', 'Unknown')
                content = chunk.get('content', '')
                metadata = chunk.get('metadata', {})
            else:
                chunk_id = getattr(chunk, 'chunk_id', 'Unknown')
                content = getattr(chunk, 'content', '')
                metadata = getattr(chunk, 'metadata', {})

            print(f"\nFound chunk: {chunk_id}")
            print(f"Content preview: {content[:100]}...")
            print(f"Metadata keys: {list(metadata.keys())}")

            # Check for our target fields
            has_rag_analysis = 'rag_analysis' in metadata or any('rag_analysis' in str(k) for k in metadata.keys())
            has_llm_meta = 'llm_meta' in metadata or any('llm_meta' in str(k) for k in metadata.keys())

            print(f"\nField check:")
            print(f"  Has rag_analysis: {has_rag_analysis}")
            print(f"  Has llm_meta: {has_llm_meta}")

            if has_rag_analysis:
                rag_data = metadata.get('rag_analysis') or [v for k, v in metadata.items() if 'rag_analysis' in str(k)]
                print(f"  RAG analysis preview: {str(rag_data)[:100]}...")

            if has_llm_meta:
                llm_data = metadata.get('llm_meta') or [v for k, v in metadata.items() if 'llm_meta' in str(k)]
                print(f"  LLM meta preview: {str(llm_data)[:100]}...")

            # Check if these fields appear in the content itself
            content_has_rag = 'RAG Analysis:' in content
            content_has_llm = 'llm_meta' in content.lower()

            print(f"\nContent check:")
            print(f"  Content has RAG analysis: {content_has_rag}")
            print(f"  Content mentions LLM meta: {content_has_llm}")

        else:
            print("FAILED: No chunks found in ChromaDB")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_chroma_fields())
    sys.exit(0 if result else 1)