# models.py
from dataclasses import dataclass, field
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
    metadata: Dict = field(default_factory=dict)  # Additional temple/poem metadata

@dataclass
class FAQChunk:
    chunk_id: str          # Format: faq_{category}_{hash}
    category: str          # FAQ category (love, career, health, etc.)
    question: str          # Original user question
    answer: str            # System response
    content: str           # Combined Q&A for search
    language: str          # Language detected
    chunk_type: ChunkType = ChunkType.FAQ
    created_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

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