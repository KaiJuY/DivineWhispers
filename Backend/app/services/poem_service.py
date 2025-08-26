"""
Poem Service - Integration wrapper for Fortune Module System

This service provides a clean interface between the FastAPI backend 
and the existing fortune module system (UnifiedRAGHandler).
"""

import asyncio
import json
import logging
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from cachetools import TTLCache

from app.core.config import settings
from app.schemas.fortune import (
    PoemData, PoemSearchResult, FortuneResult, 
    TempleStatsResponse, FortuneSystemHealthResponse
)
from app.utils.poem_utils import (
    format_poem_for_llm_context, parse_fortune_type, 
    normalize_temple_name, get_random_poem_selection,
    validate_poem_data
)

# Add fortune_module to Python path
fortune_module_path = Path(__file__).parent.parent.parent / "fortune_module"
sys.path.insert(0, str(fortune_module_path))

try:
    from fortune_module.unified_rag import UnifiedRAGHandler
    from fortune_module.models import ChunkType, PoemChunk
    from fortune_module.config import SystemConfig
    from fortune_module import FortuneSystem, create_openai_system, create_ollama_system
    from fortune_module.llm_client import LLMClientFactory
except ImportError as e:
    logging.error(f"Failed to import fortune module: {e}")
    raise


logger = logging.getLogger(__name__)


class PoemService:
    """
    Service class for poem and fortune operations with caching and async support
    """
    
    def __init__(self):
        self.rag_handler: Optional[UnifiedRAGHandler] = None
        self.fortune_system: Optional[FortuneSystem] = None
        self.cache = TTLCache(maxsize=1000, ttl=settings.FORTUNE_CACHE_TIMEOUT_SECONDS)
        self._initialized = False
        self._lock = asyncio.Lock()
        
    async def initialize_system(self) -> bool:
        """
        Initialize ChromaDB and Fortune System
        
        Returns:
            True if initialization successful, False otherwise
        """
        async with self._lock:
            if self._initialized:
                return True
                
            try:
                logger.info("Initializing poem service...")
                
                # Initialize RAG handler
                config = SystemConfig()
                self.rag_handler = UnifiedRAGHandler(
                    collection_name=settings.CHROMA_COLLECTION_NAME,
                    persist_path=settings.CHROMA_DB_PATH
                )
                
                # Initialize Fortune System
                await self._initialize_fortune_system()
                
                # Validate initialization
                health_check = await self.health_check()
                if health_check.chroma_db_status != "healthy":
                    logger.error("ChromaDB initialization failed health check")
                    return False
                
                self._initialized = True
                logger.info("Poem service initialized successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to initialize poem service: {e}")
                return False
    
    async def _initialize_fortune_system(self):
        """Initialize the Fortune System with available LLM providers"""
        try:
            # Try OpenAI first if API key is available
            if settings.OPENAI_API_KEY:
                logger.info("Initializing Fortune System with OpenAI...")
                self.fortune_system = create_openai_system(
                    api_key=settings.OPENAI_API_KEY,
                    model=settings.LLM_MODEL
                )
                return
        except Exception as e:
            logger.warning(f"OpenAI initialization failed: {e}")
        
        try:
            # Try Ollama as fallback
            logger.info("Initializing Fortune System with Ollama...")
            self.fortune_system = create_ollama_system(
                model="gpt-oss:20b",
                base_url="http://localhost:11434"
            )
            return
        except Exception as e:
            logger.warning(f"Ollama initialization failed: {e}")
        
        # Create mock system for development/testing
        logger.info("Creating mock Fortune System for development...")
        from fortune_module import FortuneSystem, LLMProvider
        
        self.fortune_system = FortuneSystem(
            llm_provider=LLMProvider.OPENAI,
            llm_config={"api_key": "mock"}
        )
        
        # Replace with mock client
        mock_client = LLMClientFactory.create_mock_client(
            "Based on the selected fortune poem, I can offer you this interpretation: "
            "The poem suggests a time of transition and growth. Trust in your inner wisdom "
            "and remain patient as new opportunities unfold. The energy surrounding you "
            "is positive, indicating that your current path will lead to beneficial outcomes."
        )
        self.fortune_system.llm = mock_client
    
    async def ensure_initialized(self):
        """Ensure the service is initialized before use"""
        if not self._initialized:
            success = await self.initialize_system()
            if not success:
                raise RuntimeError("Failed to initialize poem service")
    
    async def get_random_poem(self, temple_preference: Optional[str] = None) -> PoemData:
        """
        Get a random poem for fortune drawing
        
        Args:
            temple_preference: Optional preferred temple name
            
        Returns:
            PoemData object with random poem
            
        Raises:
            RuntimeError: If no poems available or system not initialized
        """
        await self.ensure_initialized()
        
        cache_key = f"random_poem_{temple_preference or 'any'}"
        
        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Get available poems
            poems = self.rag_handler.list_available_poems(temple_preference)
            
            if not poems:
                raise RuntimeError("No poems available in database")
            
            # Select random poem with weighted selection
            selected_poems = get_random_poem_selection(poems, count=1)
            selected = selected_poems[0]
            
            # Get full poem data
            poem_chunks = self.rag_handler.get_poem_by_temple_and_id(
                selected["temple"], 
                selected["poem_id"]
            )
            
            if not poem_chunks:
                # Fallback to basic data
                poem_data = await self._create_poem_data_from_basic(selected)
            else:
                poem_data = await self._create_poem_data_from_chunks(poem_chunks)
            
            # Cache result
            self.cache[cache_key] = poem_data
            logger.info(f"Selected random poem: {poem_data.temple}#{poem_data.poem_id}")
            
            return poem_data
            
        except Exception as e:
            logger.error(f"Error getting random poem: {e}")
            raise RuntimeError(f"Failed to get random poem: {str(e)}")
    
    async def get_poem_by_id(self, poem_id: str) -> Optional[PoemData]:
        """
        Get specific poem by ID
        
        Args:
            poem_id: Poem identifier in format "temple_poem_id" or just poem_id
            
        Returns:
            PoemData object or None if not found
        """
        await self.ensure_initialized()
        
        cache_key = f"poem_{poem_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Parse poem ID
            temple, numeric_id = await self._parse_poem_id(poem_id)
            
            if not temple or not numeric_id:
                logger.warning(f"Invalid poem ID format: {poem_id}")
                return None
            
            # Get poem chunks
            poem_chunks = self.rag_handler.get_poem_by_temple_and_id(temple, numeric_id)
            
            if not poem_chunks:
                logger.warning(f"Poem not found: {temple}#{numeric_id}")
                return None
            
            poem_data = await self._create_poem_data_from_chunks(poem_chunks)
            
            # Cache result
            self.cache[cache_key] = poem_data
            
            return poem_data
            
        except Exception as e:
            logger.error(f"Error getting poem by ID {poem_id}: {e}")
            return None
    
    async def search_similar_poems(
        self, 
        query: str, 
        top_k: int = 5,
        temple_filter: Optional[str] = None
    ) -> List[PoemSearchResult]:
        """
        Search for poems similar to query
        
        Args:
            query: Search query
            top_k: Maximum number of results
            temple_filter: Optional temple filter
            
        Returns:
            List of PoemSearchResult objects
        """
        await self.ensure_initialized()
        
        cache_key = f"search_{query}_{top_k}_{temple_filter}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            start_time = time.time()
            
            # Query RAG system
            rag_result = self.rag_handler.query(
                question=query,
                top_k=min(top_k, settings.FORTUNE_MAX_SEARCH_RESULTS),
                temple_filter=temple_filter,
                chunk_types=[ChunkType.POEM]
            )
            
            search_results = []
            
            for i, chunk in enumerate(rag_result.chunks):
                if chunk.get("chunk_type") == ChunkType.POEM.value:
                    # Create search result
                    result = PoemSearchResult(
                        temple=chunk["temple"],
                        poem_id=chunk["poem_id"],
                        title=chunk.get("title", ""),
                        fortune=chunk.get("fortune", ""),
                        relevance_score=1.0 - rag_result.scores[i],  # Convert distance to relevance
                        snippet=chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"]
                    )
                    search_results.append(result)
            
            # Cache results
            self.cache[cache_key] = search_results
            
            search_time_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Search '{query}' returned {len(search_results)} results in {search_time_ms}ms")
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching poems: {e}")
            return []
    
    async def get_poem_categories(self) -> Dict[str, int]:
        """
        Get available fortune categories with counts
        
        Returns:
            Dictionary mapping category names to counts
        """
        await self.ensure_initialized()
        
        cache_key = "fortune_categories"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            poems = self.rag_handler.list_available_poems()
            categories = {}
            
            for poem in poems:
                fortune_type = parse_fortune_type(poem.get("fortune", ""))
                categories[fortune_type] = categories.get(fortune_type, 0) + 1
            
            # Cache result
            self.cache[cache_key] = categories
            
            return categories
            
        except Exception as e:
            logger.error(f"Error getting poem categories: {e}")
            return {}
    
    async def get_poems_by_category(self, category: str) -> List[PoemData]:
        """
        Get poems filtered by fortune category
        
        Args:
            category: Fortune category to filter by
            
        Returns:
            List of PoemData objects
        """
        await self.ensure_initialized()
        
        cache_key = f"poems_category_{category}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            all_poems = self.rag_handler.list_available_poems()
            filtered_poems = []
            
            for poem in all_poems:
                fortune_type = parse_fortune_type(poem.get("fortune", ""))
                if fortune_type == category:
                    # Convert to PoemData
                    poem_data = await self._create_poem_data_from_basic(poem)
                    filtered_poems.append(poem_data)
            
            # Cache result
            self.cache[cache_key] = filtered_poems
            
            return filtered_poems
            
        except Exception as e:
            logger.error(f"Error getting poems by category {category}: {e}")
            return []
    
    async def generate_fortune_interpretation(
        self, 
        poem_data: PoemData, 
        question: str,
        language: str = "zh",
        user_context: Optional[str] = None
    ) -> FortuneResult:
        """
        Generate personalized fortune interpretation
        
        Args:
            poem_data: Selected poem data
            question: User's question
            language: Target language
            user_context: Additional user context
            
        Returns:
            FortuneResult with interpretation
        """
        await self.ensure_initialized()
        
        try:
            # Use Fortune System if available
            if self.fortune_system:
                result = self.fortune_system.ask_fortune(
                    question=question,
                    temple=poem_data.temple,
                    poem_id=poem_data.poem_id,
                    additional_context=bool(user_context)
                )
                
                return FortuneResult(
                    poem=poem_data,
                    interpretation=result.interpretation,
                    confidence=result.confidence,
                    additional_sources=result.sources.get("poems", []),
                    temple_sources=result.temple_sources,
                    generated_at=datetime.now(),
                    language=language,
                    job_id=""  # Will be set by job system
                )
            
            # Fallback interpretation
            interpretation = await self._generate_fallback_interpretation(
                poem_data, question, language
            )
            
            return FortuneResult(
                poem=poem_data,
                interpretation=interpretation,
                confidence=0.7,
                additional_sources=[],
                temple_sources=[poem_data.temple],
                generated_at=datetime.now(),
                language=language,
                job_id=""
            )
            
        except Exception as e:
            logger.error(f"Error generating interpretation: {e}")
            raise RuntimeError(f"Failed to generate interpretation: {str(e)}")
    
    async def health_check(self) -> FortuneSystemHealthResponse:
        """
        Check system health
        
        Returns:
            FortuneSystemHealthResponse with health status
        """
        try:
            if not self.rag_handler:
                return FortuneSystemHealthResponse(
                    chroma_db_status="not_initialized",
                    total_poems=0,
                    total_temples=0,
                    last_updated=None,
                    cache_status="not_available",
                    system_load="unknown"
                )
            
            # Get collection stats
            stats = self.rag_handler.get_collection_stats()
            
            chroma_status = "healthy" if not stats.get("error") else "unhealthy"
            total_poems = stats.get("poem_chunks", 0)
            total_temples = stats.get("unique_temples", 0)
            
            cache_status = f"cached_items: {len(self.cache)}"
            system_load = "normal"  # Could be enhanced with actual system metrics
            
            return FortuneSystemHealthResponse(
                chroma_db_status=chroma_status,
                total_poems=total_poems,
                total_temples=total_temples,
                last_updated=datetime.now(),
                cache_status=cache_status,
                system_load=system_load
            )
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return FortuneSystemHealthResponse(
                chroma_db_status="error",
                total_poems=0,
                total_temples=0,
                last_updated=None,
                cache_status="error",
                system_load="error"
            )
    
    async def get_temple_stats(self, temple_name: str) -> Optional[TempleStatsResponse]:
        """
        Get statistics for a specific temple
        
        Args:
            temple_name: Name of temple
            
        Returns:
            TempleStatsResponse or None if temple not found
        """
        await self.ensure_initialized()
        
        try:
            poems = self.rag_handler.list_available_poems(temple_name)
            
            if not poems:
                return None
            
            fortune_categories = {}
            languages_available = set()
            
            for poem in poems:
                fortune_type = parse_fortune_type(poem.get("fortune", ""))
                fortune_categories[fortune_type] = fortune_categories.get(fortune_type, 0) + 1
                
                # Get available languages from poem chunks if possible
                chunks = self.rag_handler.get_poem_by_temple_and_id(
                    poem["temple"], poem["poem_id"]
                )
                for chunk in chunks:
                    languages_available.add(chunk.get("language", "zh"))
            
            return TempleStatsResponse(
                temple_name=temple_name,
                total_poems=len(poems),
                fortune_categories=fortune_categories,
                languages_available=list(languages_available)
            )
            
        except Exception as e:
            logger.error(f"Error getting temple stats for {temple_name}: {e}")
            return None
    
    async def refresh_cache(self) -> bool:
        """
        Clear cache to force refresh of data
        
        Returns:
            True if successful
        """
        try:
            self.cache.clear()
            logger.info("Poem service cache cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    # Helper methods
    
    async def _parse_poem_id(self, poem_id: str) -> tuple[Optional[str], Optional[int]]:
        """Parse poem ID into temple and numeric ID"""
        try:
            if "_" in poem_id:
                # Format: temple_poem_id
                parts = poem_id.split("_")
                if len(parts) >= 2:
                    temple = parts[0]
                    numeric_id = int(parts[1])
                    return temple, numeric_id
            else:
                # Just numeric ID - need to search all temples
                numeric_id = int(poem_id)
                poems = self.rag_handler.list_available_poems()
                for poem in poems:
                    if poem["poem_id"] == numeric_id:
                        return poem["temple"], numeric_id
            
            return None, None
            
        except (ValueError, KeyError):
            return None, None
    
    async def _create_poem_data_from_chunks(self, chunks: List[Dict]) -> PoemData:
        """Create PoemData from poem chunks"""
        if not chunks:
            raise ValueError("No chunks provided")
        
        # Use first chunk for basic info
        chunk = chunks[0]
        
        # Reconstruct analysis from multiple chunks if available
        analysis = {"zh": "", "en": "", "jp": ""}
        
        for chunk_data in chunks:
            content = chunk_data.get("content", "")
            language = chunk_data.get("language", "zh")
            
            if language in analysis:
                if analysis[language]:
                    analysis[language] += "\n\n" + content
                else:
                    analysis[language] = content
        
        # Extract poem text (assume it's in the content)
        poem_text = ""
        for chunk_data in chunks:
            if "Poem:" in chunk_data.get("content", ""):
                content_lines = chunk_data["content"].split("\n")
                for line in content_lines:
                    if line.startswith("Poem:"):
                        poem_text = line.replace("Poem:", "").strip()
                        break
                if poem_text:
                    break
        
        return PoemData(
            id=f"{chunk['temple']}_{chunk['poem_id']}",
            temple=chunk["temple"],
            poem_id=chunk["poem_id"],
            title=chunk.get("title", ""),
            fortune=chunk.get("fortune", ""),
            poem=poem_text or chunk.get("content", "")[:200],
            analysis=analysis
        )
    
    async def _create_poem_data_from_basic(self, poem_info: Dict) -> PoemData:
        """Create PoemData from basic poem info"""
        return PoemData(
            id=f"{poem_info['temple']}_{poem_info['poem_id']}",
            temple=poem_info["temple"],
            poem_id=poem_info["poem_id"],
            title=poem_info.get("title", ""),
            fortune=poem_info.get("fortune", ""),
            poem="",  # Will be filled by chunks if available
            analysis={"zh": "", "en": "", "jp": ""}
        )
    
    async def _generate_fallback_interpretation(
        self, 
        poem_data: PoemData, 
        question: str, 
        language: str
    ) -> str:
        """Generate fallback interpretation when LLM is not available"""
        
        # Template-based interpretation
        fortune_interpretations = {
            "great_fortune": "This is an auspicious time filled with great potential. Your question touches on matters that are likely to unfold favorably.",
            "good_fortune": "Positive energy surrounds your inquiry. With patience and right action, good outcomes are indicated.",
            "small_fortune": "Small but meaningful progress is suggested. Trust in gradual improvement and steady steps forward.",
            "fortune": "The signs are generally positive. Maintain a balanced approach to achieve your desired outcomes.",
            "neutral": "This represents a time of balance and careful consideration. Neither rushing nor delaying is advised.",
            "bad_fortune": "Challenges may be present, but they serve as opportunities for growth and learning.",
            "great_misfortune": "This period calls for extra caution and patience. Focus on inner strength and wisdom."
        }
        
        fortune_type = parse_fortune_type(poem_data.fortune)
        base_interpretation = fortune_interpretations.get(
            fortune_type, 
            "The ancient wisdom of this poem offers guidance for your current situation."
        )
        
        # Create contextual interpretation
        interpretation = f"""
Based on the fortune poem "{poem_data.title}" from {poem_data.temple} temple, here is your interpretation:

{base_interpretation}

The poem's wisdom suggests that your question about "{question[:100]}..." is important to consider at this time. 

Regarding your specific inquiry:
- Reflect on the deeper meanings within your current circumstances
- Consider both the immediate and long-term implications of your choices
- Trust in the natural flow of events while taking appropriate action

Remember that fortune readings offer guidance for reflection, and your own wisdom and choices ultimately shape your path forward.

May this ancient wisdom bring clarity to your journey.
        """.strip()
        
        return interpretation


# Global service instance
poem_service = PoemService()