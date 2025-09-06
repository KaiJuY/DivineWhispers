#!/usr/bin/env python3
"""
Simple ChromaDB initialization script for Docker container
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_chromadb_in_container():
    """Initialize ChromaDB inside the Docker container"""
    
    logger.info("Starting ChromaDB initialization in container...")
    
    try:
        # Add fortune_module to path
        sys.path.insert(0, '/app/fortune_module')
        
        # Import required modules
        from fortune_module.data_ingestion import quick_ingest_all
        from fortune_module.config import SystemConfig
        
        # Ensure chroma_db directory exists with proper permissions
        chroma_path = "/app/chroma_db"
        os.makedirs(chroma_path, mode=0o777, exist_ok=True)
        logger.info(f"Created ChromaDB directory: {chroma_path}")
        
        # Create config
        config = SystemConfig()
        logger.info(f"Config - Collection: {config.collection_name}")
        logger.info(f"Config - ChromaDB path: {config.chroma_persist_path}")
        
        # Run data ingestion
        logger.info("Starting data ingestion...")
        result = quick_ingest_all(clear_existing=True)
        
        total_chunks = result.get('total_chunks_ingested', 0)
        if total_chunks > 0:
            logger.info(f"✅ Successfully ingested {total_chunks} poem chunks!")
            
            # Test the system
            from fortune_module.unified_rag import UnifiedRAGHandler
            rag = UnifiedRAGHandler()
            stats = rag.get_collection_stats()
            logger.info(f"ChromaDB stats: {stats}")
            
            logger.info("🎉 ChromaDB initialization completed successfully!")
            return True
        else:
            logger.error("❌ No chunks were ingested")
            return False
            
    except Exception as e:
        logger.error(f"❌ ChromaDB initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_chromadb_in_container()
    sys.exit(0 if success else 1)