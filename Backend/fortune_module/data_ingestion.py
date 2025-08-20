# data_ingestion.py - Builder Pattern for ChromaDB Population
"""
Data ingestion module using Builder pattern to populate ChromaDB with fortune poem data.

This module provides flexible builders for creating poem chunks from various sources
and ingesting them into the unified RAG system.

Usage:
    builder = PoemChunkBuilder()
    ingestion_manager = DataIngestionManager(builder, rag_handler)
    ingestion_manager.ingest_temple_data("GuanYin100")
"""

import json
import os
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Iterator
from pathlib import Path
from .models import PoemChunk, ChunkType
from .unified_rag import UnifiedRAGHandler
from .config import SystemConfig
import hashlib

# Builder Pattern - Abstract builder for poem chunks
class PoemChunkBuilderInterface(ABC):
    """Abstract builder interface for creating poem chunks using Builder pattern."""
    
    @abstractmethod
    def reset(self) -> 'PoemChunkBuilderInterface':
        """Reset the builder for a new poem."""
        pass
    
    @abstractmethod
    def set_basic_info(self, poem_data: Dict[str, Any]) -> 'PoemChunkBuilderInterface':
        """Set basic poem information."""
        pass
    
    @abstractmethod
    def set_temple_info(self, temple: str) -> 'PoemChunkBuilderInterface':
        """Set temple information."""
        pass
    
    @abstractmethod
    def build_poem_chunks(self) -> List[PoemChunk]:
        """Build and return the poem chunks."""
        pass

class PoemChunkBuilder(PoemChunkBuilderInterface):
    """Concrete builder for creating poem chunks from JSON data."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.reset()
    
    def reset(self) -> 'PoemChunkBuilder':
        """Reset the builder for a new poem."""
        self._poem_data = {}
        self._temple = ""
        self._chunks = []
        return self
    
    def set_basic_info(self, poem_data: Dict[str, Any]) -> 'PoemChunkBuilder':
        """Set basic poem information from JSON data."""
        self._poem_data = poem_data
        return self
    
    def set_temple_info(self, temple: str) -> 'PoemChunkBuilder':
        """Set temple information."""
        self._temple = temple
        return self
    
    def _create_chunk_id(self, temple: str, poem_id: int, section: str) -> str:
        """Create unique chunk ID."""
        return f"poem_{temple}_{poem_id}_{section}"
    
    def _extract_content_sections(self) -> Dict[str, str]:
        """Extract different content sections from poem data."""
        sections = {}
        
        # Main poem content
        poem_text = self._poem_data.get("poem", "")
        if poem_text:
            sections["poem"] = f"詩文: {poem_text}"
        
        # Analysis sections
        analysis = self._poem_data.get("analysis", {})
        if isinstance(analysis, dict):
            for lang, content in analysis.items():
                if lang in ["zh", "en", "jp"] and content:
                    sections[f"analysis_{lang}"] = f"{lang.upper()} Analysis: {content}"
        
        # RAG analysis if available
        rag_analysis = self._poem_data.get("rag_analysis", "")
        if rag_analysis:
            sections["rag_analysis"] = f"RAG Analysis: {rag_analysis}"
        
        # Combined content for general search
        combined_parts = []
        title = self._poem_data.get("title", "")
        if title:
            combined_parts.append(f"Title: {title}")
        if poem_text:
            combined_parts.append(f"Poem: {poem_text}")
        
        # Add the best analysis (prefer Chinese, then English, then Japanese)
        if "zh" in analysis and analysis["zh"]:
            combined_parts.append(f"Analysis: {analysis['zh']}")
        elif "en" in analysis and analysis["en"]:
            combined_parts.append(f"Analysis: {analysis['en']}")
        elif "jp" in analysis and analysis["jp"]:
            combined_parts.append(f"Analysis: {analysis['jp']}")
        
        if combined_parts:
            sections["combined"] = "\n\n".join(combined_parts)
        
        return sections
    
    def _detect_language(self, text: str) -> str:
        """Detect primary language of text."""
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        japanese_chars = sum(1 for char in text if '\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff')
        total_chars = len(text)
        
        if total_chars == 0:
            return "zh"  # Default to Chinese
        
        chinese_ratio = chinese_chars / total_chars
        japanese_ratio = japanese_chars / total_chars
        
        if chinese_ratio > 0.3:
            return "zh"
        elif japanese_ratio > 0.2:
            return "jp"
        else:
            return "en"
    
    def build_poem_chunks(self) -> List[PoemChunk]:
        """Build poem chunks from the configured data."""
        if not self._poem_data or not self._temple:
            raise ValueError("Missing required data: poem_data and temple must be set")
        
        poem_id = self._poem_data.get("id")
        if poem_id is None:
            raise ValueError("Poem data must contain 'id' field")
        
        title = self._poem_data.get("title", f"Poem {poem_id}")
        fortune = self._poem_data.get("fortune", "Unknown")
        
        # Extract content sections
        sections = self._extract_content_sections()
        
        chunks = []
        for section_name, content in sections.items():
            if not content.strip():
                continue
            
            chunk_id = self._create_chunk_id(self._temple, poem_id, section_name)
            language = self._detect_language(content)
            
            # Create metadata
            metadata = {
                "section": section_name,
                "source_file": self._poem_data.get("_source_file"),
                "subtitle": self._poem_data.get("subtitle"),
                "original_poem": self._poem_data.get("poem", "")
            }
            
            # Add LLM meta if available
            llm_meta = self._poem_data.get("_llm_meta")
            if llm_meta:
                metadata["llm_meta"] = llm_meta
            
            chunk = PoemChunk(
                chunk_id=chunk_id,
                temple=self._temple,
                poem_id=poem_id,
                title=title,
                fortune=fortune,
                content=content,
                language=language,
                chunk_type=ChunkType.POEM,
                metadata=metadata
            )
            
            chunks.append(chunk)
        
        self.logger.debug(f"Built {len(chunks)} chunks for {self._temple} poem #{poem_id}")
        return chunks

# Director class for managing the building process
class DataIngestionDirector:
    """Director class that uses builders to create and ingest poem chunks."""
    
    def __init__(self, builder: PoemChunkBuilderInterface):
        self.builder = builder
        self.logger = logging.getLogger(__name__)
    
    def create_chunks_from_json(self, json_data: Dict[str, Any], temple: str, source_file: str = None) -> List[PoemChunk]:
        """Create poem chunks from JSON data."""
        # Add source file info to the data
        if source_file:
            json_data["_source_file"] = source_file
        
        chunks = (self.builder
                 .reset()
                 .set_temple_info(temple)
                 .set_basic_info(json_data)
                 .build_poem_chunks())
        
        return chunks
    
    def create_chunks_from_file(self, file_path: str, temple: str) -> List[PoemChunk]:
        """Create poem chunks from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            return self.create_chunks_from_json(json_data, temple, os.path.basename(file_path))
            
        except Exception as e:
            self.logger.error(f"Failed to process file {file_path}: {e}")
            return []

# Data source handlers
class DataSourceHandler(ABC):
    """Abstract handler for different data sources."""
    
    @abstractmethod
    def get_temple_files(self, temple: str) -> Iterator[str]:
        """Get iterator of file paths for a temple."""
        pass
    
    @abstractmethod
    def validate_source(self) -> bool:
        """Validate that the data source is accessible."""
        pass

class FileSystemDataSource(DataSourceHandler):
    """Handler for file system-based data sources."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.logger = logging.getLogger(__name__)
    
    def validate_source(self) -> bool:
        """Validate that the base path exists."""
        return self.base_path.exists() and self.base_path.is_dir()
    
    def get_temple_files(self, temple: str) -> Iterator[str]:
        """Get JSON files for a specific temple."""
        temple_path = self.base_path / temple
        
        if not temple_path.exists():
            self.logger.warning(f"Temple directory not found: {temple_path}")
            return
        
        # Find all JSON files
        for json_file in temple_path.glob("*.json"):
            yield str(json_file)

# Main ingestion manager
class DataIngestionManager:
    """Main manager for data ingestion using Builder pattern."""
    
    def __init__(self, rag_handler: UnifiedRAGHandler, 
                 builder: PoemChunkBuilderInterface = None,
                 data_source: DataSourceHandler = None):
        self.config = SystemConfig()
        self.rag = rag_handler
        self.builder = builder or PoemChunkBuilder()
        self.director = DataIngestionDirector(self.builder)
        
        # Set up data source
        if data_source:
            self.data_source = data_source
        else:
            # Default to file system source
            source_path = os.path.abspath(self.config.source_data_path)
            self.data_source = FileSystemDataSource(source_path)
        
        self.logger = logging.getLogger(__name__)
        
        # Validate data source
        if not self.data_source.validate_source():
            self.logger.warning(f"Data source validation failed")
    
    def ingest_temple_data(self, temple: str, clear_existing: bool = False) -> Dict[str, Any]:
        """Ingest all data for a specific temple."""
        if clear_existing:
            self.logger.info(f"Clearing existing data for temple: {temple}")
            self.rag.delete_chunks_by_temple(temple)
        
        stats = {
            "temple": temple,
            "files_processed": 0,
            "chunks_created": 0,
            "chunks_ingested": 0,
            "errors": []
        }
        
        try:
            file_count = 0
            all_chunks = []
            
            # Process all files for the temple
            for file_path in self.data_source.get_temple_files(temple):
                try:
                    chunks = self.director.create_chunks_from_file(file_path, temple)
                    if chunks:
                        all_chunks.extend(chunks)
                        stats["chunks_created"] += len(chunks)
                    
                    file_count += 1
                    
                    # Log progress for large datasets
                    if file_count % 50 == 0:
                        self.logger.info(f"Processed {file_count} files for {temple}")
                        
                except Exception as e:
                    error_msg = f"Failed to process {file_path}: {e}"
                    self.logger.error(error_msg)
                    stats["errors"].append(error_msg)
            
            stats["files_processed"] = file_count
            
            # Batch ingest chunks
            if all_chunks:
                success = self.rag.add_poem_chunks(all_chunks)
                if success:
                    stats["chunks_ingested"] = len(all_chunks)
                    self.logger.info(f"Successfully ingested {len(all_chunks)} chunks for {temple}")
                else:
                    stats["errors"].append("Failed to add chunks to RAG system")
            
        except Exception as e:
            error_msg = f"Temple ingestion failed: {e}"
            self.logger.error(error_msg)
            stats["errors"].append(error_msg)
        
        return stats
    
    def ingest_all_temples(self, clear_existing: bool = False) -> Dict[str, Any]:
        """Ingest data for all configured temples."""
        if clear_existing:
            self.logger.warning("Clearing entire collection")
            self.rag.clear_collection()
        
        overall_stats = {
            "total_files_processed": 0,
            "total_chunks_created": 0,
            "total_chunks_ingested": 0,
            "temple_results": {},
            "errors": []
        }
        
        for temple in self.config.temple_names:
            self.logger.info(f"Starting ingestion for temple: {temple}")
            
            try:
                temple_stats = self.ingest_temple_data(temple, clear_existing=False)
                overall_stats["temple_results"][temple] = temple_stats
                
                # Aggregate statistics
                overall_stats["total_files_processed"] += temple_stats["files_processed"]
                overall_stats["total_chunks_created"] += temple_stats["chunks_created"]
                overall_stats["total_chunks_ingested"] += temple_stats["chunks_ingested"]
                overall_stats["errors"].extend(temple_stats["errors"])
                
                self.logger.info(f"Completed ingestion for {temple}: "
                               f"{temple_stats['chunks_ingested']} chunks from "
                               f"{temple_stats['files_processed']} files")
                
            except Exception as e:
                error_msg = f"Failed to ingest temple {temple}: {e}"
                self.logger.error(error_msg)
                overall_stats["errors"].append(error_msg)
        
        self.logger.info(f"Data ingestion completed: "
                        f"{overall_stats['total_chunks_ingested']} total chunks ingested")
        
        return overall_stats
    
    def validate_ingestion(self) -> Dict[str, Any]:
        """Validate the ingested data."""
        validation_results = {
            "collection_stats": {},
            "temple_coverage": {},
            "issues": []
        }
        
        try:
            # Get collection statistics
            validation_results["collection_stats"] = self.rag.get_collection_stats()
            
            # Check temple coverage
            for temple in self.config.temple_names:
                poems = self.rag.list_available_poems(temple)
                validation_results["temple_coverage"][temple] = {
                    "poem_count": len(poems),
                    "has_data": len(poems) > 0
                }
                
                if len(poems) == 0:
                    validation_results["issues"].append(f"No poems found for temple: {temple}")
            
            # Check for basic functionality
            try:
                test_result = self.rag.query("test query", top_k=1)
                if not test_result.chunks:
                    validation_results["issues"].append("RAG query returned no results")
            except Exception as e:
                validation_results["issues"].append(f"RAG query failed: {e}")
            
        except Exception as e:
            validation_results["issues"].append(f"Validation failed: {e}")
        
        return validation_results

# Convenience functions
def create_ingestion_manager(rag_handler: UnifiedRAGHandler = None) -> DataIngestionManager:
    """Create a data ingestion manager with default settings."""
    if not rag_handler:
        rag_handler = UnifiedRAGHandler()
    
    return DataIngestionManager(rag_handler)

def quick_ingest_all(clear_existing: bool = False) -> Dict[str, Any]:
    """Quick function to ingest all temple data."""
    rag_handler = UnifiedRAGHandler()
    manager = DataIngestionManager(rag_handler)
    return manager.ingest_all_temples(clear_existing=clear_existing)

def quick_ingest_temple(temple: str, clear_existing: bool = False) -> Dict[str, Any]:
    """Quick function to ingest data for a specific temple."""
    rag_handler = UnifiedRAGHandler()
    manager = DataIngestionManager(rag_handler)
    return manager.ingest_temple_data(temple, clear_existing=clear_existing)

if __name__ == "__main__":
    # Command line interface for data ingestion
    import argparse
    
    parser = argparse.ArgumentParser(description="Fortune Poem Data Ingestion")
    parser.add_argument("--temple", help="Ingest data for specific temple")
    parser.add_argument("--all", action="store_true", help="Ingest data for all temples")
    parser.add_argument("--clear", action="store_true", help="Clear existing data before ingestion")
    parser.add_argument("--validate", action="store_true", help="Validate ingested data")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create manager
    manager = create_ingestion_manager()
    
    if args.temple:
        print(f"Ingesting data for temple: {args.temple}")
        result = manager.ingest_temple_data(args.temple, clear_existing=args.clear)
        print(f"Results: {json.dumps(result, indent=2)}")
        
    elif args.all:
        print("Ingesting data for all temples")
        result = manager.ingest_all_temples(clear_existing=args.clear)
        print(f"Results: {json.dumps(result, indent=2)}")
        
    if args.validate:
        print("\nValidating ingested data...")
        validation = manager.validate_ingestion()
        print(f"Validation results: {json.dumps(validation, indent=2)}")