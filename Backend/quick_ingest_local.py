#!/usr/bin/env python3
"""
Quick ingestion script for local development.
This script sets the correct path to the SourceCrawler data and ingests all temple data.
"""

import os
import sys
from pathlib import Path

# Add the fortune_module to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fortune_module'))

from fortune_module.data_ingestion import DataIngestionManager
from fortune_module.unified_rag import UnifiedRAGHandler
from fortune_module.config import SystemConfig

def main():
    print("[FIRE] Starting local data ingestion for DivineWhispers...")

    # Calculate the correct path to SourceCrawler data
    backend_dir = Path(__file__).parent
    source_crawler_dir = backend_dir.parent / "SourceCrawler"

    print(f"Backend directory: {backend_dir}")
    print(f"Looking for SourceCrawler data in: {source_crawler_dir}")

    if not source_crawler_dir.exists():
        print(f"[ERROR] SourceCrawler directory not found: {source_crawler_dir}")
        return False

    # Check for temple directories
    temples_found = []
    expected_temples = ["GuanYin100", "GuanYu", "Mazu", "Asakusa", "ErawanShrine", "Tianhou"]

    for temple in expected_temples:
        temple_path = source_crawler_dir / temple
        if temple_path.exists():
            json_files = list(temple_path.glob("*.json"))
            if json_files:
                temples_found.append((temple, len(json_files)))
                print(f"[OK] Found temple {temple} with {len(json_files)} JSON files")
            else:
                print(f"[WARN] Temple directory {temple} exists but no JSON files found")
        else:
            print(f"[ERROR] Temple directory not found: {temple_path}")

    if not temples_found:
        print("[ERROR] No temple data found. Please run the SourceCrawler first.")
        return False

    # Override the config with the correct local path
    config = SystemConfig()
    config.update_config(source_data_path=str(source_crawler_dir))

    # Create RAG handler and ingestion manager
    rag_handler = UnifiedRAGHandler()
    manager = DataIngestionManager(rag_handler)

    # Update the data source to use the correct path
    from fortune_module.data_ingestion import FileSystemDataSource
    manager.data_source = FileSystemDataSource(str(source_crawler_dir))

    print(f"\n[START] Starting ingestion for {len(temples_found)} temples...")

    # Clear existing data first
    print("[CLEAN] Clearing existing data...")
    result = manager.ingest_all_temples(clear_existing=True)

    # Print results
    print(f"\n[RESULTS] Ingestion Results:")
    print(f"Total files processed: {result['total_files_processed']}")
    print(f"Total chunks created: {result['total_chunks_created']}")
    print(f"Total chunks ingested: {result['total_chunks_ingested']}")

    if result['errors']:
        print(f"[ERROR] Errors encountered: {len(result['errors'])}")
        for error in result['errors'][:5]:  # Show first 5 errors
            print(f"  - {error}")
    else:
        print("[OK] No errors encountered")

    # Validate the ingestion
    print("\n[VALIDATE] Validating ingestion...")
    validation = manager.validate_ingestion()

    stats = validation.get('collection_stats', {})
    print(f"Collection statistics:")
    print(f"  Total chunks: {stats.get('total_chunks', 0)}")
    print(f"  Poem chunks: {stats.get('poem_chunks', 0)}")
    print(f"  Unique temples: {stats.get('unique_temples', 0)}")

    if validation.get('issues'):
        print(f"[WARN] Issues found: {len(validation['issues'])}")
        for issue in validation['issues']:
            print(f"  - {issue}")
    else:
        print("[OK] Validation passed!")

    return result['total_chunks_ingested'] > 0

if __name__ == "__main__":
    success = main()
    if success:
        print("\n[SUCCESS] Data ingestion completed successfully!")
        print("You can now test the API endpoints.")
        sys.exit(0)
    else:
        print("\n[FAIL] Data ingestion failed!")
        sys.exit(1)