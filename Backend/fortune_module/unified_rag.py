# unified_rag.py
import chromadb
from typing import List, Optional, Union, Dict, Any
from .models import PoemChunk, FAQChunk, RAGResult, ChunkType
from .config import SystemConfig
import hashlib
import logging
from datetime import datetime

class UnifiedRAGHandler:
    """Repository pattern implementation for unified RAG operations on poems and FAQs."""
    
    def __init__(self, collection_name: str = None, persist_path: str = None):
        self.config = SystemConfig()
        self.collection_name = collection_name or self.config.collection_name
        self.persist_path = persist_path or self.config.chroma_persist_path
        self.logger = logging.getLogger(__name__)
        
        # Initialize ChromaDB client
        try:
            self.client = chromadb.PersistentClient(path=self.persist_path)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self.logger.info(f"Connected to ChromaDB collection: {self.collection_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def _sanitize_metadata(self, metadata: Dict) -> Dict:
        """Sanitize metadata to ensure all values are ChromaDB-compatible primitive types."""
        sanitized = {}
        
        for key, value in metadata.items():
            if value is None:
                sanitized[key] = None
            elif isinstance(value, (str, int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, (dict, list, tuple)):
                # Convert complex types to JSON strings
                import json
                try:
                    sanitized[f"{key}_json"] = json.dumps(value, ensure_ascii=False)
                except (TypeError, ValueError):
                    sanitized[f"{key}_str"] = str(value)
            else:
                # Convert any other type to string
                sanitized[f"{key}_str"] = str(value)
        
        return sanitized
    
    def add_poem_chunks(self, poems: List[PoemChunk]) -> bool:
        """Add poem chunks to the knowledge base."""
        try:
            documents = [chunk.content for chunk in poems]
            metadatas = [
                {
                    "chunk_type": ChunkType.POEM.value,
                    "temple": chunk.temple,
                    "poem_id": chunk.poem_id,
                    "fortune": chunk.fortune,
                    "language": chunk.language,
                    "title": chunk.title,
                    "created_at": datetime.now().isoformat(),
                    **self._sanitize_metadata(chunk.metadata or {})
                }
                for chunk in poems
            ]
            ids = [chunk.chunk_id for chunk in poems]
            
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            self.logger.info(f"Added {len(poems)} poem chunks to ChromaDB")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add poem chunks: {e}")
            return False
    
    def add_faq_chunk(self, faq: FAQChunk) -> bool:
        """Add approved FAQ chunk to the knowledge base."""
        try:
            self.collection.add(
                documents=[faq.content],
                metadatas=[{
                    "chunk_type": ChunkType.FAQ.value,
                    "category": faq.category,
                    "language": faq.language,
                    "question": faq.question,
                    "answer": faq.answer,
                    "created_at": faq.created_at.isoformat() if faq.created_at else datetime.now().isoformat(),
                    "approved_by": faq.approved_by,
                    **self._sanitize_metadata(faq.metadata or {})
                }],
                ids=[faq.chunk_id]
            )
            
            self.logger.info(f"Added FAQ chunk: {faq.chunk_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add FAQ chunk: {e}")
            return False
    
    def query(self, question: str, top_k: int = None, 
             temple_filter: Optional[str] = None,
             chunk_types: Optional[List[ChunkType]] = None) -> RAGResult:
        """Query relevant content with optional filtering using Repository pattern."""
        
        top_k = top_k or self.config.default_top_k
        
        # Build where clause for filtering with proper ChromaDB syntax
        conditions = []
        if temple_filter:
            conditions.append({"temple": {"$eq": temple_filter}})
        if chunk_types:
            conditions.append({"chunk_type": {"$in": [ct.value for ct in chunk_types]}})
        
        # Construct where clause
        if len(conditions) == 0:
            where_clause = None
        elif len(conditions) == 1:
            where_clause = conditions[0]
        else:
            where_clause = {"$and": conditions}
        
        try:
            results = self.collection.query(
                query_texts=[question],
                n_results=top_k,
                where=where_clause if where_clause else None
            )
            
            chunks = []
            for i, doc_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]
                chunk_data = {
                    "chunk_id": doc_id,
                    "content": results['documents'][0][i],
                    "chunk_type": metadata["chunk_type"],
                    "language": metadata["language"],
                    "metadata": metadata
                }
                
                # Add type-specific fields
                if metadata["chunk_type"] == ChunkType.POEM.value:
                    chunk_data.update({
                        "temple": metadata["temple"],
                        "poem_id": metadata["poem_id"],
                        "fortune": metadata["fortune"],
                        "title": metadata.get("title", "")
                    })
                elif metadata["chunk_type"] == ChunkType.FAQ.value:
                    chunk_data.update({
                        "category": metadata["category"],
                        "question": metadata.get("question", ""),
                        "answer": metadata.get("answer", ""),
                        "created_at": metadata.get("created_at"),
                        "approved_by": metadata.get("approved_by")
                    })
                
                chunks.append(chunk_data)
            
            self.logger.info(f"Query returned {len(chunks)} results for: {question[:50]}...")
            
            return RAGResult(
                chunks=chunks,
                scores=results['distances'][0],
                query=question
            )
            
        except Exception as e:
            self.logger.error(f"Query failed: {e}")
            return RAGResult(chunks=[], scores=[], query=question)
    
    def get_poem_by_temple_and_id(self, temple: str, poem_id: int) -> List[Dict]:
        """Retrieve specific poem chunks by temple and poem ID."""
        try:
            results = self.collection.query(
                query_texts=[""],
                where={
                    "$and": [
                        {"chunk_type": {"$eq": ChunkType.POEM.value}},
                        {"temple": {"$eq": temple}},
                        {"poem_id": {"$eq": poem_id}}
                    ]
                },
                n_results=100  # Get all chunks for this poem
            )
            
            chunks = []
            for i, doc_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]
                chunks.append({
                    "chunk_id": doc_id,
                    "temple": temple,
                    "poem_id": poem_id,
                    "title": metadata.get("title", ""),
                    "fortune": metadata["fortune"],
                    "content": results['documents'][0][i],
                    "language": metadata["language"],
                    "chunk_type": ChunkType.POEM.value,
                    "metadata": metadata
                })
            
            self.logger.info(f"Retrieved {len(chunks)} chunks for {temple} poem #{poem_id}")
            return chunks
            
        except Exception as e:
            self.logger.error(f"Failed to get poem {temple}#{poem_id}: {e}")
            return []
    
    def list_available_poems(self, temple: Optional[str] = None) -> List[Dict]:
        """List available poems with basic metadata."""
        try:
            # Build where clause properly for ChromaDB
            if temple:
                where_clause = {
                    "$and": [
                        {"chunk_type": {"$eq": ChunkType.POEM.value}},
                        {"temple": {"$eq": temple}}
                    ]
                }
            else:
                where_clause = {"chunk_type": {"$eq": ChunkType.POEM.value}}
                
            # Query with high limit to get all poems
            results = self.collection.query(
                query_texts=[""],
                where=where_clause,
                n_results=10000  # Large number to get all
            )
            
            # Group by temple and poem_id to get unique poems
            poem_dict = {}
            for i, doc_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]
                temple_name = metadata["temple"]
                poem_id = metadata["poem_id"]
                
                key = f"{temple_name}_{poem_id}"
                if key not in poem_dict:
                    poem_dict[key] = {
                        "temple": temple_name,
                        "poem_id": poem_id,
                        "title": metadata.get("title", ""),
                        "fortune": metadata.get("fortune", ""),
                        "language": metadata.get("language", "")
                    }
            
            poems = list(poem_dict.values())
            self.logger.info(f"Found {len(poems)} available poems")
            return poems
            
        except Exception as e:
            self.logger.error(f"Failed to list poems: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            # Get all items to calculate stats
            all_results = self.collection.query(
                query_texts=[""],
                n_results=100000  # Very large number to get all
            )
            
            total_chunks = len(all_results['ids'][0])
            poem_chunks = 0
            faq_chunks = 0
            temples = set()
            
            for metadata in all_results['metadatas'][0]:
                if metadata["chunk_type"] == ChunkType.POEM.value:
                    poem_chunks += 1
                    temples.add(metadata.get("temple", "unknown"))
                elif metadata["chunk_type"] == ChunkType.FAQ.value:
                    faq_chunks += 1
            
            stats = {
                "total_chunks": total_chunks,
                "poem_chunks": poem_chunks,
                "faq_chunks": faq_chunks,
                "unique_temples": len(temples),
                "temple_list": list(temples)
            }
            
            self.logger.info(f"Collection stats: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {e}")
            return {"error": str(e)}
    
    def delete_chunks_by_temple(self, temple: str) -> bool:
        """Delete all chunks for a specific temple (useful for re-ingestion)."""
        try:
            # First, find all chunk IDs for this temple
            results = self.collection.query(
                query_texts=[""],
                where={"temple": temple},
                n_results=10000
            )
            
            chunk_ids = results['ids'][0]
            if chunk_ids:
                self.collection.delete(ids=chunk_ids)
                self.logger.info(f"Deleted {len(chunk_ids)} chunks for temple: {temple}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete chunks for temple {temple}: {e}")
            return False
    
    def clear_collection(self) -> bool:
        """Clear all data from the collection (use with caution)."""
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            self.logger.warning("Collection cleared and recreated")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear collection: {e}")
            return False