#!/usr/bin/env python3
"""
Initialize ChromaDB for Render deployment
This script creates a fresh ChromaDB from source data during the build process
"""

import os
import sys
import logging
import shutil
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_chromadb():
    """Initialize ChromaDB from source data for deployment"""

    logger.info("=== ChromaDB Deployment Initialization ===")

    try:
        # Import after adding to path
        from fortune_module.data_ingestion import quick_ingest_all
        from fortune_module.config import SystemConfig
        from fortune_module.unified_rag import UnifiedRAGHandler

        # Get config
        config = SystemConfig()
        chroma_path = Path(config.chroma_persist_path)
        source_path = Path(config.source_data_path)

        logger.info(f"ChromaDB path: {chroma_path.absolute()}")
        logger.info(f"Source data path: {source_path.absolute()}")

        # Check if source data exists
        if not source_path.exists():
            logger.error(f"Source data path does not exist: {source_path.absolute()}")
            logger.error("Available paths in current directory:")
            for item in Path('.').iterdir():
                logger.error(f"  {item}")
            return False

        # Check if ChromaDB already exists and is valid
        if chroma_path.exists():
            logger.info("ChromaDB directory already exists, checking validity...")
            try:
                # Try to connect to existing DB
                test_rag = UnifiedRAGHandler()
                stats = test_rag.get_collection_stats()
                total_chunks = stats.get('total_chunks', 0)

                if total_chunks > 0:
                    logger.info(f"✅ Existing ChromaDB is valid with {total_chunks} chunks")
                    logger.info("Skipping initialization")
                    test_rag.cleanup()
                    return True
                else:
                    logger.warning("Existing ChromaDB has no data, recreating...")
                    test_rag.cleanup()
            except Exception as e:
                logger.warning(f"Existing ChromaDB is invalid: {e}")
                logger.info("Removing invalid ChromaDB...")
                shutil.rmtree(chroma_path)

        # Create fresh ChromaDB directory
        chroma_path.mkdir(parents=True, exist_ok=True)
        logger.info("Created ChromaDB directory")

        # Count source files
        total_json_files = 0
        for temple in config.temple_names:
            temple_path = source_path / temple
            if temple_path.exists():
                json_files = list(temple_path.glob("*.json"))
                logger.info(f"Found {len(json_files)} JSON files for {temple}")
                total_json_files += len(json_files)

        if total_json_files == 0:
            logger.error("No JSON source files found!")
            return False

        logger.info(f"Total source files to ingest: {total_json_files}")

        # Run data ingestion
        logger.info("Starting data ingestion...")
        result = quick_ingest_all(clear_existing=True)

        # Check results
        total_chunks = result.get('total_chunks_ingested', 0)
        temples_processed = result.get('temples_processed', 0)

        logger.info(f"Ingestion completed:")
        logger.info(f"  - Temples processed: {temples_processed}")
        logger.info(f"  - Total chunks ingested: {total_chunks}")

        if total_chunks > 0:
            # Verify the database
            logger.info("Verifying ChromaDB...")
            verify_rag = UnifiedRAGHandler()
            stats = verify_rag.get_collection_stats()
            verify_rag.cleanup()

            logger.info(f"Verification stats: {stats}")
            logger.info("✅ ChromaDB initialization completed successfully!")
            return True
        else:
            logger.error("❌ No data was ingested!")
            return False

    except Exception as e:
        logger.error(f"❌ ChromaDB initialization failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = init_chromadb()
    sys.exit(0 if success else 1)
