#!/usr/bin/env python3
"""
Script to fix ChromaDB initialization issues and reinitialize the fortune system
"""

import os
import sys
import shutil
import logging
from pathlib import Path

# Add the current directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_chromadb():
    """Fix ChromaDB by clearing and reinitializing the database"""
    
    logger.info("Starting ChromaDB fix process...")
    
    # Path to ChromaDB directory
    chroma_db_path = Path("./chroma_db")
    
    try:
        # Step 1: Backup existing ChromaDB (in case we need to recover)
        backup_path = Path("./chroma_db_backup")
        if chroma_db_path.exists():
            if backup_path.exists():
                shutil.rmtree(backup_path)
            shutil.copytree(chroma_db_path, backup_path)
            logger.info(f"Backed up existing ChromaDB to {backup_path}")
        
        # Step 2: Clear existing ChromaDB
        if chroma_db_path.exists():
            shutil.rmtree(chroma_db_path)
            logger.info("Cleared existing ChromaDB directory")
        
        # Step 3: Re-create directory
        chroma_db_path.mkdir(exist_ok=True)
        logger.info("Created new ChromaDB directory")
        
        # Step 4: Re-initialize ChromaDB and ingest data
        logger.info("Attempting to reinitialize ChromaDB with data ingestion...")
        
        # Import and run data ingestion
        from fortune_module.data_ingestion import quick_ingest_all
        from fortune_module.config import SystemConfig
        
        # Create config
        config = SystemConfig()
        logger.info(f"Using collection name: {config.collection_name}")
        logger.info(f"Using ChromaDB path: {config.chroma_persist_path}")
        
        # Run ingestion
        result = quick_ingest_all(clear_existing=True)
        logger.info(f"Ingestion result: {result}")
        
        # Extract total chunks from result
        total_chunks = result.get('total_chunks_ingested', 0)
        
        if total_chunks > 0:
            logger.info(f"Successfully ingested {total_chunks} poem chunks")
            
            # Step 5: Test the connection
            from fortune_module.unified_rag import UnifiedRAGHandler
            
            rag = UnifiedRAGHandler()
            stats = rag.get_collection_stats()
            logger.info(f"ChromaDB stats after fix: {stats}")
            
            if stats.get('total_chunks', 0) > 0:
                logger.info("✅ ChromaDB fix completed successfully!")
                return True
            else:
                logger.error("❌ No data found after ingestion")
                return False
        else:
            logger.error("❌ Data ingestion failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ ChromaDB fix failed: {e}")
        
        # Try to restore backup
        try:
            if backup_path.exists() and chroma_db_path.exists():
                shutil.rmtree(chroma_db_path)
                shutil.copytree(backup_path, chroma_db_path)
                logger.info("Restored backup due to fix failure")
        except Exception as restore_error:
            logger.error(f"Failed to restore backup: {restore_error}")
        
        return False

def test_poem_service():
    """Test the poem service after ChromaDB fix"""
    
    logger.info("Testing poem service...")
    
    try:
        from app.services.poem_service import poem_service
        import asyncio
        
        async def test_service():
            # Reset the service
            poem_service._initialized = False
            
            # Try to initialize
            success = await poem_service.initialize_system()
            
            if success:
                logger.info("✅ Poem service initialized successfully")
                
                # Test getting categories
                categories = await poem_service.get_poem_categories()
                logger.info(f"Categories found: {list(categories.keys()) if categories else 'None'}")
                
                if categories:
                    logger.info("✅ Poem service is working correctly!")
                    return True
                else:
                    logger.warning("⚠️ Poem service initialized but no categories found")
                    return False
            else:
                logger.error("❌ Poem service initialization failed")
                return False
        
        # Run the async test
        return asyncio.run(test_service())
        
    except Exception as e:
        logger.error(f"❌ Poem service test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("=== Divine Whispers ChromaDB Fix Tool ===")
    
    # Step 1: Fix ChromaDB
    if fix_chromadb():
        logger.info("ChromaDB fix completed successfully")
        
        # Step 2: Test poem service
        if test_poem_service():
            logger.info("🎉 All systems working correctly!")
            sys.exit(0)
        else:
            logger.error("Poem service test failed")
            sys.exit(1)
    else:
        logger.error("ChromaDB fix failed")
        sys.exit(1)