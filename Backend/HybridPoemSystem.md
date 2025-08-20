Fortune Poem RAG System with Integrated FAQ - Design Document

## 1. Overview

This module provides a RAG-only fortune poem interpretation system with integrated FAQ pipeline:

- **Unified ChromaDB**: Stores both fortune poems and approved FAQ entries as searchable chunks
- **Temple-specific Retrieval**: Filter poems by specific temple and chunk ID
- **FAQ Pipeline**: Automatically captures user Q&A → pending approval → integrates into RAG
- **Unified LLM Interface**: Support for both OpenAI and Ollama with consistent API
- **Approval Workflow**: Review and approve FAQ entries before adding to knowledge base
- **Simple Interface**: Clean, minimal API for easy integration

Data source: `SourceCrawler/outputs/` (temple fortune poem JSON files)

## 2. Module Structure
```
fortune_module/
│── __init__.py
│── unified_rag.py     # ChromaDB with poems + FAQ chunks
│── llm_client.py      # Unified OpenAI/Ollama interface
│── interpreter.py     # RAG query + LLM interpretation + FAQ capture
│── faq_pipeline.py    # FAQ approval workflow
│── models.py          # Data structures
│── config.py          # Configuration settings
```

## 3. Data Structures

```python
# models.py
from dataclasses import dataclass
from typing import Optional, Dict, List
from enum import Enum
from datetime import datetime

class LLMProvider(Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"

class ChunkType(Enum):
    POEM = "poem"
    FAQ = "faq"

@dataclass
class PoemChunk:
    chunk_id: str          # Format: poem_{temple}_{poem_id}_{section}
    temple: str            # Temple name
    poem_id: int           # Original poem ID
    title: str             # Poem title
    fortune: str           # Fortune level (大吉, 中吉, etc.)
    content: str           # Poem text + analysis section
    language: str          # Language (zh/en/jp)
    chunk_type: ChunkType = ChunkType.POEM
    metadata: Dict = None  # Additional temple/poem metadata

@dataclass
class FAQChunk:
    chunk_id: str          # Format: faq_{category}_{hash}
    category: str          # FAQ category (love, career, health, etc.)
    question: str          # Original user question
    answer: str            # System response
    content: str           # Combined Q&A for search
    language: str          # Language detected
    chunk_type: ChunkType = ChunkType.FAQ
    created_at: datetime = None
    approved_by: str = None
    metadata: Dict = None

@dataclass
class PendingFAQ:
    question: str
    answer: str
    category: str
    language: str
    session_id: str
    created_at: datetime
    status: str = "pending"  # pending, approved, rejected
    
@dataclass
class RAGResult:
    chunks: List[Dict]     # Mix of PoemChunk and FAQChunk
    scores: List[float]
    query: str

@dataclass
class SelectedPoem:
    temple: str
    poem_id: int
    chunks: List[Dict]  # Poem chunks from get_poem_by_temple_and_id
    
@dataclass
class InterpretationResult:
    interpretation: str
    selected_poem: SelectedPoem
    relevant_chunks: List[Dict]  # Additional RAG context
    sources: Dict[str, int]  # {"poems": count, "faqs": count}
    temple_sources: List[str]
    confidence: float
```

## 4. Unified RAG Handler (Poems + FAQ)

```python
# unified_rag.py
import chromadb
from typing import List, Optional, Union
from .models import PoemChunk, FAQChunk, RAGResult, ChunkType
import hashlib
from datetime import datetime

class UnifiedRAGHandler:
    def __init__(self, collection_name: str = "fortune_knowledge", persist_path: str = "./chroma"):
        self.client = chromadb.PersistentClient(path=persist_path)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_poem_chunks(self, poems: List[PoemChunk]):
        """Add poem chunks to the knowledge base."""
        documents = [chunk.content for chunk in poems]
        metadatas = [
            {
                "chunk_type": ChunkType.POEM.value,
                "temple": chunk.temple,
                "poem_id": chunk.poem_id,
                "fortune": chunk.fortune,
                "language": chunk.language,
                "title": chunk.title,
                **(chunk.metadata or {})
            }
            for chunk in poems
        ]
        ids = [chunk.chunk_id for chunk in poems]
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def add_faq_chunk(self, faq: FAQChunk):
        """Add approved FAQ chunk to the knowledge base."""
        self.collection.add(
            documents=[faq.content],
            metadatas=[{
                "chunk_type": ChunkType.FAQ.value,
                "category": faq.category,
                "language": faq.language,
                "created_at": faq.created_at.isoformat() if faq.created_at else None,
                "approved_by": faq.approved_by,
                **(faq.metadata or {})
            }],
            ids=[faq.chunk_id]
        )
    
    def query(self, question: str, top_k: int = 5, 
             temple_filter: Optional[str] = None,
             chunk_types: Optional[List[ChunkType]] = None) -> RAGResult:
        """Query relevant content with optional filtering."""
        
        where_clause = {}
        if temple_filter:
            where_clause["temple"] = temple_filter
        if chunk_types:
            where_clause["chunk_type"] = {"$in": [ct.value for ct in chunk_types]}
        
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
                    "created_at": metadata.get("created_at"),
                    "approved_by": metadata.get("approved_by")
                })
            
            chunks.append(chunk_data)
        
        return RAGResult(
            chunks=chunks,
            scores=results['distances'][0],
            query=question
        )
    
    def get_poem_by_temple_and_id(self, temple: str, poem_id: int) -> List[Dict]:
        """Retrieve specific poem chunks by temple and poem ID."""
        results = self.collection.query(
            query_texts=[""],
            where={
                "chunk_type": ChunkType.POEM.value,
                "temple": temple, 
                "poem_id": poem_id
            },
            n_results=100
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
        
        return chunks
```

## 5. FAQ Pipeline with Approval Workflow

```python
# faq_pipeline.py
import json
import sqlite3
from typing import List, Optional
from datetime import datetime
from .models import PendingFAQ, FAQChunk, ChunkType
from .unified_rag import UnifiedRAGHandler
import hashlib

class FAQPipeline:
    def __init__(self, db_path: str = "pending_faq.db", rag_handler: UnifiedRAGHandler = None):
        self.db_path = db_path
        self.rag = rag_handler
        self._init_db()
    
    def _init_db(self):
        """Initialize pending FAQ database."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pending_faqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                category TEXT,
                language TEXT,
                session_id TEXT,
                created_at TIMESTAMP,
                status TEXT DEFAULT 'pending'
            )
        """)
        conn.commit()
        conn.close()
    
    def capture_interaction(self, question: str, answer: str, category: str, 
                          language: str, session_id: str) -> int:
        """Capture user interaction for potential FAQ creation."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "INSERT INTO pending_faqs (question, answer, category, language, session_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (question, answer, category, language, session_id, datetime.now())
        )
        faq_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return faq_id
    
    def get_pending_faqs(self, status: str = "pending") -> List[PendingFAQ]:
        """Get pending FAQs for review."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT question, answer, category, language, session_id, created_at, status FROM pending_faqs WHERE status = ?",
            (status,)
        )
        
        faqs = []
        for row in cursor.fetchall():
            faqs.append(PendingFAQ(
                question=row[0],
                answer=row[1],
                category=row[2],
                language=row[3],
                session_id=row[4],
                created_at=datetime.fromisoformat(row[5]),
                status=row[6]
            ))
        
        conn.close()
        return faqs
    
    def approve_faq(self, session_id: str, approved_by: str, 
                   edited_question: Optional[str] = None, 
                   edited_answer: Optional[str] = None) -> bool:
        """Approve a pending FAQ and add to RAG system."""
        conn = sqlite3.connect(self.db_path)
        
        # Get the pending FAQ
        cursor = conn.execute(
            "SELECT question, answer, category, language FROM pending_faqs WHERE session_id = ? AND status = 'pending'",
            (session_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return False
        
        question = edited_question or row[0]
        answer = edited_answer or row[1]
        category = row[2]
        language = row[3]
        
        # Create FAQ chunk
        content = f"Q: {question}\n\nA: {answer}"
        chunk_id = f"faq_{category}_{hashlib.md5(content.encode()).hexdigest()[:8]}"
        
        faq_chunk = FAQChunk(
            chunk_id=chunk_id,
            category=category,
            question=question,
            answer=answer,
            content=content,
            language=language,
            created_at=datetime.now(),
            approved_by=approved_by
        )
        
        # Add to RAG system
        if self.rag:
            self.rag.add_faq_chunk(faq_chunk)
        
        # Update status in database
        conn.execute(
            "UPDATE pending_faqs SET status = 'approved' WHERE session_id = ?",
            (session_id,)
        )
        conn.commit()
        conn.close()
        
        return True
    
    def reject_faq(self, session_id: str) -> bool:
        """Reject a pending FAQ."""
        conn = sqlite3.connect(self.db_path)
        result = conn.execute(
            "UPDATE pending_faqs SET status = 'rejected' WHERE session_id = ?",
            (session_id,)
        )
        conn.commit()
        conn.close()
        return result.rowcount > 0
```

## 6. Unified LLM Interface

```python
# llm_client.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from .models import LLMProvider
import openai
import requests
import json

class BaseLLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        pass

class OpenAIClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
    
    def generate(self, prompt: str, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content

class OllamaClient(BaseLLMClient):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url
        self.model = model
    
    def generate(self, prompt: str, **kwargs) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                **kwargs
            }
        )
        return json.loads(response.text)["response"]

class LLMClientFactory:
    @staticmethod
    def create_client(provider: LLMProvider, **config) -> BaseLLMClient:
        if provider == LLMProvider.OPENAI:
            return OpenAIClient(
                api_key=config["api_key"],
                model=config.get("model", "gpt-3.5-turbo")
            )
        elif provider == LLMProvider.OLLAMA:
            return OllamaClient(
                base_url=config.get("base_url", "http://localhost:11434"),
                model=config.get("model", "llama2")
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
```

## 7. Main Interpreter with FAQ Pipeline

```python
# interpreter.py
from typing import Optional
import uuid
from .models import InterpretationResult, ChunkType
from .unified_rag import UnifiedRAGHandler
from .llm_client import BaseLLMClient
from .faq_pipeline import FAQPipeline

class PoemInterpreter:
    def __init__(self, rag_handler: UnifiedRAGHandler, llm_client: BaseLLMClient, faq_pipeline: FAQPipeline):
        self.rag = rag_handler
        self.llm = llm_client
        self.faq_pipeline = faq_pipeline
    
    def interpret(self, question: str, temple: str, poem_id: int, 
                 additional_context_k: int = 3, capture_faq: bool = True) -> InterpretationResult:
        """Generate fortune interpretation for specific poem with additional RAG context."""
        
        # Get the specific poem
        selected_poem_chunks = self.rag.get_poem_by_temple_and_id(temple, poem_id)
        if not selected_poem_chunks:
            raise ValueError(f"Poem not found: {temple} poem #{poem_id}")
        
        # Get additional context via RAG (excluding the selected poem)
        rag_result = self.rag.query(question, top_k=additional_context_k + 2)  # Get extra in case selected poem appears
        
        # Separate additional context (exclude the selected poem)
        additional_chunks = [
            c for c in rag_result.chunks 
            if not (c.get("temple") == temple and c.get("poem_id") == poem_id)
        ]
        poem_chunks = [c for c in additional_chunks if c["chunk_type"] == ChunkType.POEM.value]
        faq_chunks = [c for c in additional_chunks if c["chunk_type"] == ChunkType.FAQ.value]
        
        # Build context starting with the selected poem
        context_parts = []
        
        # Add selected poem
        selected_poem_content = "\n".join([chunk["content"] for chunk in selected_poem_chunks])
        context_parts.append(
            f"Selected Fortune Poem (Temple: {temple}, Poem #{poem_id}):\n{selected_poem_content}"
        )
        
        # Add additional poem context
        for i, chunk in enumerate(poem_chunks[:2]):  # Limit additional poems to 2
            context_parts.append(
                f"Related Poem {i+1} (Temple: {chunk['temple']}, Fortune: {chunk['fortune']}):\n{chunk['content']}"
            )
        
        # Add FAQ context
        for i, chunk in enumerate(faq_chunks[:2]):  # Limit FAQ to 2
            context_parts.append(
                f"Previous FAQ {i+1} (Category: {chunk['category']}):\n{chunk['content']}"
            )
        
        context = "\n\n".join(context_parts)
        
        # Generate interpretation
        prompt = f"""You are a fortune interpretation assistant specializing in Chinese temple divination.

Context:
{context}

User question: {question}

Instructions:
1. Focus primarily on interpreting the selected fortune poem from {temple} (Poem #{poem_id}) in relation to the user's question
2. Use the related poems and previous FAQ as supporting context to enrich your interpretation
3. Provide a thoughtful interpretation considering the poem meanings and fortune levels
4. Answer in the same language as the user's question
5. Be supportive and constructive in your guidance
6. Keep your response focused and practical
7. Mention the specific temple and poem number in your response

Response:"""

        interpretation = self.llm.generate(prompt)
        
        # Capture interaction for potential FAQ
        if capture_faq:
            session_id = str(uuid.uuid4())
            category = self._detect_category(question)
            language = self._detect_language(question)
            
            self.faq_pipeline.capture_interaction(
                question=question,
                answer=interpretation,
                category=category,
                language=language,
                session_id=session_id
            )
        
        # Calculate confidence based on additional context relevance
        avg_score = sum(rag_result.scores) / len(rag_result.scores) if rag_result.scores else 0
        confidence = max(0, 1 - avg_score)
        
        selected_poem = SelectedPoem(
            temple=temple,
            poem_id=poem_id,
            chunks=selected_poem_chunks
        )
        
        return InterpretationResult(
            interpretation=interpretation,
            selected_poem=selected_poem,
            relevant_chunks=additional_chunks,
            sources={
                "poems": len(poem_chunks),
                "faqs": len(faq_chunks)
            },
            temple_sources=list(set([temple] + [c["temple"] for c in poem_chunks if "temple" in c])),
            confidence=confidence
        )
    
    def _detect_category(self, question: str) -> str:
        """Simple category detection based on keywords."""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["love", "relationship", "marriage", "partner"]):
            return "love"
        elif any(word in question_lower for word in ["career", "job", "work", "business"]):
            return "career"
        elif any(word in question_lower for word in ["health", "illness", "recovery", "medical"]):
            return "health"
        elif any(word in question_lower for word in ["money", "wealth", "financial", "income"]):
            return "wealth"
        else:
            return "general"
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection."""
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return "zh"
        elif any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in text):
            return "jp"
        else:
            return "en"
```

## 8. Simple API Interface

```python
# __init__.py
from .unified_rag import UnifiedRAGHandler
from .llm_client import LLMClientFactory, LLMProvider
from .interpreter import PoemInterpreter
from .faq_pipeline import FAQPipeline
from .models import *
from typing import List, Optional

class FortuneSystem:
    def __init__(self, llm_provider: LLMProvider, llm_config: dict):
        self.rag = UnifiedRAGHandler()
        self.llm = LLMClientFactory.create_client(llm_provider, **llm_config)
        self.faq_pipeline = FAQPipeline(rag_handler=self.rag)
        self.interpreter = PoemInterpreter(self.rag, self.llm, self.faq_pipeline)
    
    def ask_fortune(self, question: str, temple: str, poem_id: int, 
                   additional_context: bool = True, capture_faq: bool = True) -> InterpretationResult:
        """Main interface for fortune consultation with specific poem."""
        context_k = 3 if additional_context else 0
        return self.interpreter.interpret(question, temple, poem_id, 
                                        additional_context_k=context_k, capture_faq=capture_faq)
    
    def ask_fortune_with_poem(self, question: str, selected_poem: SelectedPoem, 
                            additional_context: bool = True, capture_faq: bool = True) -> InterpretationResult:
        """Alternative interface using SelectedPoem object."""
        context_k = 3 if additional_context else 0
        return self.interpreter.interpret(question, selected_poem.temple, selected_poem.poem_id,
                                        additional_context_k=context_k, capture_faq=capture_faq)
    
    def get_poem_by_temple(self, temple: str, poem_id: int) -> SelectedPoem:
        """Get specific poem by temple and ID."""
        chunks = self.rag.get_poem_by_temple_and_id(temple, poem_id)
        if not chunks:
            raise ValueError(f"Poem not found: {temple} poem #{poem_id}")
        return SelectedPoem(temple=temple, poem_id=poem_id, chunks=chunks)
    
    def list_available_poems(self, temple: Optional[str] = None) -> List[Dict]:
        """List available poems, optionally filtered by temple."""
        # This would require a separate method in UnifiedRAGHandler to list available poems
        # For now, return a placeholder
        return [{"temple": temple or "all", "note": "Implementation needed in UnifiedRAGHandler"}]
    
    def random_poem(self, temple: Optional[str] = None) -> SelectedPoem:
        """Get a random poem for divination."""
        import random
        # This is a placeholder - would need proper implementation
        # For now, return a default poem
        default_temple = temple or "GuanYin"
        default_id = random.randint(1, 100)  # Assuming poems 1-100 exist
        return self.get_poem_by_temple(default_temple, default_id)
    
    # FAQ Management Interface
    def get_pending_faqs(self) -> List[PendingFAQ]:
        """Get pending FAQ entries for approval."""
        return self.faq_pipeline.get_pending_faqs()
    
    def approve_faq(self, session_id: str, approved_by: str, 
                   edited_question: Optional[str] = None, 
                   edited_answer: Optional[str] = None) -> bool:
        """Approve and add FAQ to knowledge base."""
        return self.faq_pipeline.approve_faq(session_id, approved_by, edited_question, edited_answer)
    
    def reject_faq(self, session_id: str) -> bool:
        """Reject pending FAQ."""
        return self.faq_pipeline.reject_faq(session_id)
```

## 9. Usage Examples

```python
# Basic Usage
system = FortuneSystem(
    llm_provider=LLMProvider.OPENAI,
    llm_config={"api_key": "your-api-key", "model": "gpt-4"}
)

# Method 1: Ask fortune with specific temple and poem ID
result = system.ask_fortune("Will I find love this year?", temple="GuanYin", poem_id=42)
print(result.interpretation)
print(f"Selected: {result.selected_poem.temple} Poem #{result.selected_poem.poem_id}")
print(f"Additional context: {result.sources['poems']} poems, {result.sources['faqs']} FAQs")

# Method 2: Get poem first, then ask fortune
poem = system.get_poem_by_temple("GuanYin", 42)
result = system.ask_fortune_with_poem("Will I find love this year?", poem)

# Method 3: Random poem divination
random_poem = system.random_poem(temple="Mazu")
result = system.ask_fortune_with_poem("What does the future hold?", random_poem)

# Review and approve FAQ
pending_faqs = system.get_pending_faqs()
for faq in pending_faqs:
    print(f"Q: {faq.question}")
    print(f"A: {faq.answer}")
    print(f"Category: {faq.category}")
    
    # Approve with optional edits
    system.approve_faq(
        session_id=faq.session_id,
        approved_by="admin",
        edited_question="Will I find romantic love this year?",  # Optional edit
        edited_answer=None  # Keep original answer
    )

# Get specific poem as object
poem = system.get_poem_by_temple("GuanYin", 42)
print(f"Poem: {poem.temple} #{poem.poem_id}")
print(f"Chunks: {len(poem.chunks)}")
```

## 10. Fortune Consultation Workflow

1. **Poem Selection**: 
   - **Specific**: `ask_fortune(question, temple, poem_id)`
   - **Object-based**: `ask_fortune_with_poem(question, selected_poem)`
   - **Random divination**: `random_poem()` → `ask_fortune_with_poem()`

2. **Interpretation Process**:
   - System retrieves the selected poem chunks
   - Finds additional relevant context (poems + FAQ) via RAG
   - LLM generates interpretation focusing on selected poem
   - Auto-captures Q&A for potential FAQ

3. **FAQ Approval Workflow**:
   - **Admin review** → View pending FAQs with `get_pending_faqs()`
   - **Approval process**:
     - **Approve**: `approve_faq()` → Adds to ChromaDB knowledge base
     - **Edit & Approve**: Modify question/answer then approve
     - **Reject**: `reject_faq()` → Removes from pending list
   - **Integration** → Approved FAQs become searchable alongside poems

## 11. Configuration

```python
# config.py
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class SystemConfig:
    # ChromaDB settings
    chroma_persist_path: str = "./chroma_db"
    collection_name: str = "fortune_knowledge"
    
    # LLM settings
    default_llm_provider: str = "openai"
    openai_config: Dict[str, Any] = None
    ollama_config: Dict[str, Any] = None
    
    # RAG settings
    default_top_k: int = 5
    max_poems_per_query: int = 3
    max_faqs_per_query: int = 2
    
    # FAQ Pipeline settings
    pending_faq_db_path: str = "pending_faq.db"
    auto_capture_faq: bool = True
    
    def __post_init__(self):
        if self.openai_config is None:
            self.openai_config = {"model": "gpt-3.5-turbo"}
        if self.ollama_config is None:
            self.ollama_config = {"base_url": "http://localhost:11434", "model": "llama2"}
```

This integrated system automatically builds a knowledge base from user interactions while maintaining quality through the approval workflow.