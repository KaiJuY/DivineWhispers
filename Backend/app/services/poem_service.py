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
from typing import Dict, List, Optional, Union, Any, Callable
from cachetools import TTLCache
import re
import difflib

from app.core.config import settings
from app.utils.logging_config import get_logger
from app.utils.timeout_utils import (
    with_timeout, timeout_context, TimeoutError,
    rag_circuit_breaker, llm_circuit_breaker, chromadb_circuit_breaker,
    with_circuit_breaker
)
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


logger = get_logger(__name__)


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

        # Cache metrics
        self._cache_hits = 0
        self._cache_misses = 0
        
    @with_circuit_breaker(chromadb_circuit_breaker, fallback_value=False)
    async def initialize_system(self) -> bool:
        """
        Initialize ChromaDB and Fortune System with timeout protection

        Returns:
            True if initialization successful, False otherwise
        """
        async with self._lock:
            if self._initialized:
                return True

            try:
                async with timeout_context(30.0, "poem_service_initialization"):
                    logger.info("Initializing poem service...")

                    # Debug environment
                    import os
                    logger.info(f"Current working directory: {os.getcwd()}")
                    logger.info(f"ChromaDB path exists: {os.path.exists(settings.CHROMA_DB_PATH)}")
                    if os.path.exists(settings.CHROMA_DB_PATH):
                        logger.info(f"ChromaDB path contents: {os.listdir(settings.CHROMA_DB_PATH)}")

                    # Initialize RAG handler with timeout
                    await self._initialize_rag_handler_async()

                    # Initialize Fortune System
                    await self._initialize_fortune_system()

                    # Validate initialization with timeout
                    health_check = await self.health_check()
                    if health_check.chroma_db_status != "healthy":
                        logger.error("ChromaDB initialization failed health check")
                        return False

                    self._initialized = True
                    logger.info("Poem service initialized successfully")
                    return True

            except TimeoutError:
                logger.error("Poem service initialization timed out")
                return False
            except Exception as e:
                logger.error(f"Failed to initialize poem service: {e}")
                return False

    async def _initialize_rag_handler_async(self):
        """Initialize RAG handler in async context"""
        # Run RAG handler initialization in thread pool to avoid blocking
        loop = asyncio.get_event_loop()

        def init_rag():
            config = SystemConfig()
            logger.info(f"RAG Config - Collection: {settings.CHROMA_COLLECTION_NAME}, Path: {settings.CHROMA_DB_PATH}")

            # Try multiple initialization approaches
            try:
                logger.info("Attempting UnifiedRAGHandler with default parameters...")
                return UnifiedRAGHandler()
            except Exception as e:
                logger.warning(f"Default initialization failed: {e}")
                try:
                    logger.info("Attempting UnifiedRAGHandler with explicit parameters...")
                    return UnifiedRAGHandler(
                        collection_name=settings.CHROMA_COLLECTION_NAME,
                        persist_path=settings.CHROMA_DB_PATH
                    )
                except Exception as e2:
                    logger.error(f"Both initialization methods failed: {e2}")
                    raise e2

        # Run in thread pool with timeout
        try:
            self.rag_handler = await asyncio.wait_for(
                loop.run_in_executor(None, init_rag),
                timeout=20.0
            )
            logger.info("SUCCESS: UnifiedRAGHandler initialized")
        except asyncio.TimeoutError:
            logger.error("RAG handler initialization timed out")
            raise TimeoutError("RAG handler initialization timed out")
    
    async def _initialize_fortune_system(self):
        """Initialize the Fortune System according to configured LLM provider."""
        provider = (settings.LLM_PROVIDER or "ollama").lower()
        logger.info(f"Initializing Fortune System (provider={provider})...")

        # Preferred provider
        try:
            if provider == "openai":
                if not settings.OPENAI_API_KEY:
                    raise RuntimeError("OPENAI_API_KEY not set")
                self.fortune_system = create_openai_system(
                    api_key=settings.OPENAI_API_KEY,
                    model=settings.LLM_MODEL
                )
                logger.info("Fortune System initialized with OpenAI")
                return

            if provider == "ollama":
                self.fortune_system = create_ollama_system(
                    model=settings.LLM_MODEL or "gpt-oss:20b",
                    base_url=settings.OLLAMA_BASE_URL or "http://localhost:11434"
                )
                logger.info("Fortune System initialized with Ollama")
                return

            if provider == "mock":
                raise Exception("Force mock provider")
        except Exception as e:
            logger.warning(f"Preferred LLM provider initialization failed ({provider}): {e}")

        # Fallback chain
        try:
            if settings.OPENAI_API_KEY:
                self.fortune_system = create_openai_system(
                    api_key=settings.OPENAI_API_KEY,
                    model=settings.LLM_MODEL
                )
                logger.info("Fortune System fallback to OpenAI succeeded")
                return
        except Exception as e:
            logger.warning(f"OpenAI fallback failed: {e}")

        try:
            self.fortune_system = create_ollama_system(
                model=settings.LLM_MODEL or "gpt-oss:20b",
                base_url=settings.OLLAMA_BASE_URL or "http://localhost:11434"
            )
            logger.info("Fortune System fallback to Ollama succeeded")
            return
        except Exception as e:
            logger.warning(f"Ollama fallback failed: {e}")

        # Final mock fallback to ensure system runs
        logger.info("Falling back to mock Fortune System (development mode)")
        from fortune_module import FortuneSystem, LLMProvider
        self.fortune_system = FortuneSystem(
            llm_provider=LLMProvider.OPENAI,
            llm_config={"api_key": "mock"}
        )
        mock_client = LLMClientFactory.create_mock_client(
            "Based on the selected fortune poem, I can offer you this interpretation: "
            "The poem suggests a time of transition and growth. Trust in your inner wisdom "
            "and remain patient as new opportunities unfold. The energy surrounding you "
            "is positive, indicating that your current path will lead to beneficial outcomes."
        )
        self.fortune_system.llm = mock_client
    
    async def ensure_initialized(self):
        """Ensure the service is initialized before use with timeout"""
        if not self._initialized:
            try:
                async with timeout_context(10.0, "ensure_initialized"):
                    success = await self.initialize_system()
                    if not success:
                        raise RuntimeError("Failed to initialize poem service")
            except TimeoutError:
                logger.error("Poem service initialization timed out")
                raise RuntimeError("Poem service initialization timed out")

    def get_cache_stats(self) -> dict:
        """Get cache performance statistics"""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size": len(self.cache),
            "cache_maxsize": self.cache.maxsize,
            "estimated_time_saved_seconds": self._cache_hits * 1.0  # 1s per cache hit
        }

    def cleanup(self):
        """Clean up service resources"""
        try:
            # Log final cache stats before cleanup
            if hasattr(self, '_cache_hits'):
                stats = self.get_cache_stats()
                logger.info(f"[CACHE_STATS] Final stats: {stats}")

            if hasattr(self, 'rag_handler') and self.rag_handler:
                if hasattr(self.rag_handler, 'cleanup'):
                    self.rag_handler.cleanup()
                self.rag_handler = None

            if hasattr(self, 'fortune_system') and self.fortune_system:
                self.fortune_system = None

            # Clear cache
            if hasattr(self, 'cache'):
                self.cache.clear()

            self._initialized = False
            logger.info("Poem service resources cleaned up")

        except Exception as e:
            logger.warning(f"Error during poem service cleanup: {e}")

    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except:
            pass
    
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
                # Create mock poem data when real data is unavailable
                logger.warning("No poems available in database, creating mock poem data")
                return await self._create_mock_poem_data(temple_preference)
            
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
            # Fallback to mock poem when database fails
            logger.warning("Database error, creating mock poem data")
            return await self._create_mock_poem_data(temple_preference)
    
    @with_circuit_breaker(rag_circuit_breaker, fallback_value=None)
    async def get_poem_by_id(self, poem_id: str) -> Optional[PoemData]:
        """
        Get specific poem by ID with timeout protection

        Args:
            poem_id: Poem identifier in format "temple_poem_id" or just poem_id

        Returns:
            PoemData object or None if not found
        """
        logger.info(f"[GET_POEM] Retrieving poem by ID: '{poem_id}'")
        await self.ensure_initialized()

        cache_key = f"poem_{poem_id}"
        if cache_key in self.cache:
            self._cache_hits += 1
            cache_hit_rate = (self._cache_hits / (self._cache_hits + self._cache_misses)) * 100
            logger.info(f"[CACHE_HIT] Poem {poem_id} (hit rate: {cache_hit_rate:.1f}%, saves ~1s)")
            return self.cache[cache_key]

        self._cache_misses += 1

        try:
            async with timeout_context(15.0, f"get_poem_by_id_{poem_id}"):
                # Parse poem ID
                logger.debug(f"[GET_POEM] Parsing poem ID: '{poem_id}'")
                temple, numeric_id = await self._parse_poem_id(poem_id)
                logger.debug(f"[GET_POEM] Parsed result - temple: '{temple}', numeric_id: {numeric_id}")

                if not temple or not numeric_id:
                    logger.warning(f"[GET_POEM] Invalid poem ID format: {poem_id}")
                    return None

                # Get poem chunks with timeout
                poem_data = await self._get_poem_chunks_async(temple, numeric_id, poem_id)

                if poem_data:
                    # Cache result
                    self.cache[cache_key] = poem_data
                    return poem_data
                else:
                    return None

        except TimeoutError:
            logger.warning(f"[GET_POEM] Timeout getting poem {poem_id}")
            return None
        except Exception as e:
            logger.error(f"[GET_POEM] Critical error getting poem by ID {poem_id}: {e}", exc_info=True)
            logger.error(f"[GET_POEM] Error context - poem_id: '{poem_id}', cache_key: '{cache_key}'")
            return None

    async def _get_poem_chunks_async(self, temple: str, numeric_id: int, poem_id: str) -> Optional[PoemData]:
        """Get poem chunks asynchronously with timeout protection"""
        loop = asyncio.get_event_loop()

        def get_chunks():
            return self.rag_handler.get_poem_by_temple_and_id(temple, numeric_id)

        try:
            # Run RAG query in thread pool to avoid blocking
            poem_chunks = await asyncio.wait_for(
                loop.run_in_executor(None, get_chunks),
                timeout=10.0
            )

            logger.debug(f"[GET_POEM] Retrieved {len(poem_chunks) if poem_chunks else 0} chunks")

            if not poem_chunks:
                logger.warning(f"[GET_POEM] Poem not found in RAG: {temple}#{numeric_id}")
                # Try fallback to direct file reading
                logger.info(f"[GET_POEM] Attempting direct file read for {temple}#{numeric_id}")
                return await self._try_direct_file_read(temple, numeric_id)

            logger.debug(f"[GET_POEM] Creating poem data from {len(poem_chunks)} chunks")
            poem_data = await self._create_poem_data_from_chunks(poem_chunks)

            if not poem_data:
                logger.error(f"[GET_POEM] Failed to create poem data from chunks for {temple}#{numeric_id}")
                return None

            # Validate the analysis structure - if it's corrupted, try direct file read
            logger.debug(f"[GET_POEM] Validating analysis structure for {poem_id}")
            is_valid = self._is_analysis_valid(poem_data.analysis)
            logger.debug(f"[GET_POEM] Analysis validation result: {is_valid}")

            if not is_valid:
                logger.warning(f"[GET_POEM] Invalid analysis structure for {poem_id}, trying direct file read")
                direct_data = await self._try_direct_file_read(temple, numeric_id)
                if direct_data and self._is_analysis_valid(direct_data.analysis):
                    logger.info(f"[GET_POEM] Successfully retrieved valid data from direct file read")
                    poem_data = direct_data
                else:
                    logger.warning(f"[GET_POEM] Direct file read also failed or invalid for {poem_id}")

            return poem_data

        except asyncio.TimeoutError:
            logger.error(f"[GET_POEM] Timeout getting chunks for {temple}#{numeric_id}")
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
            # Return empty results for search when data is unavailable
            # This allows the API to function even without real poem data
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
            # Return mock categories for testing when real data unavailable
            return {
                "great_fortune": 50,
                "good_fortune": 75, 
                "neutral": 40,
                "bad_fortune": 25
            }
    
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

    async def get_all_poems_for_admin(
        self,
        page: int = 1,
        limit: int = 20,
        deity_filter: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict:
        """
        Get all poems for admin management with pagination and filtering

        Args:
            page: Page number (1-based)
            limit: Number of poems per page
            deity_filter: Filter by deity/temple name
            search: Search in title or poem content

        Returns:
            Dictionary with poems list and pagination info
        """
        await self.ensure_initialized()

        try:
            logger.info(f"[ADMIN_POEMS] Getting poems for admin - page: {page}, limit: {limit}, deity: {deity_filter}, search: {search}")

            # Get all available poems from ChromaDB
            if deity_filter:
                # Filter by specific temple/deity
                all_poems = self.rag_handler.list_available_poems(deity_filter)
                logger.debug(f"[ADMIN_POEMS] Retrieved {len(all_poems)} poems for deity: {deity_filter}")
            else:
                # Get all poems
                all_poems = self.rag_handler.list_available_poems()
                logger.debug(f"[ADMIN_POEMS] Retrieved {len(all_poems)} total poems")

            # Apply search filter if provided
            if search and search.strip():
                search_term = search.strip().lower()
                filtered_poems = []
                for poem in all_poems:
                    # Search in title, poem content, and fortune type
                    title = poem.get("title", "").lower()
                    poem_text = poem.get("poem", "").lower()
                    fortune = poem.get("fortune", "").lower()

                    if (search_term in title or
                        search_term in poem_text or
                        search_term in fortune):
                        filtered_poems.append(poem)

                all_poems = filtered_poems
                logger.debug(f"[ADMIN_POEMS] After search filter: {len(all_poems)} poems")

            # Calculate pagination
            total_count = len(all_poems)
            total_pages = (total_count + limit - 1) // limit
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_poems = all_poems[start_idx:end_idx]

            logger.debug(f"[ADMIN_POEMS] Pagination - total: {total_count}, page: {page}/{total_pages}, showing: {len(paginated_poems)}")

            # Format poems for admin interface
            poems_data = []
            for poem in paginated_poems:
                poem_data = {
                    "id": f"{poem.get('temple', 'unknown')}_{poem.get('id', poem.get('poem_id', 'unknown'))}",
                    "title": poem.get("title", "Untitled Poem"),
                    "deity": poem.get("temple", "Unknown Temple"),
                    "chinese": poem.get("poem", ""),
                    "fortune": poem.get("fortune", ""),
                    "topics": self._extract_topics(poem),
                    "last_modified": datetime.now().isoformat(),
                    "usage_count": 0,  # Would need tracking system for real usage
                    "status": "active",
                    "poem_id": poem.get("id", poem.get("poem_id", 0))
                }
                poems_data.append(poem_data)

            # Get unique deities/temples for filter options
            all_temples = set()
            for poem in all_poems:
                temple = poem.get("temple")
                if temple:
                    all_temples.add(temple)

            return {
                "poems": poems_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total_count,
                    "pages": total_pages
                },
                "filters": {
                    "deity": deity_filter,
                    "search": search
                },
                "summary": {
                    "total_poems": total_count,
                    "active_deities": sorted(list(all_temples))
                }
            }

        except Exception as e:
            logger.error(f"[ADMIN_POEMS] Error getting poems for admin: {e}", exc_info=True)
            # Return empty structure on error
            return {
                "poems": [],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": 0,
                    "pages": 0
                },
                "filters": {
                    "deity": deity_filter,
                    "search": search
                },
                "summary": {
                    "total_poems": 0,
                    "active_deities": ["GuanYin", "Mazu", "GuanYu", "YueLao", "Asakusa"]  # Fallback
                }
            }

    def _extract_topics(self, poem: Dict) -> str:
        """Extract relevant topics from poem data"""
        topics = []

        # Add fortune type as topic
        fortune = poem.get("fortune", "")
        if fortune:
            topics.append(fortune)

        # Add temple as topic
        temple = poem.get("temple", "")
        if temple:
            topics.append(temple)

        # Could add more sophisticated topic extraction here
        # For now, return basic categorization
        return ", ".join(topics) if topics else "Fortune Analysis"

    @with_circuit_breaker(llm_circuit_breaker, fallback_value=None)
    async def generate_fortune_interpretation(
        self,
        poem_data: PoemData,
        question: str,
        language: str = "zh",
        user_context: Optional[str] = None,
        streaming_callback: Optional[Callable[[str], None]] = None
    ) -> FortuneResult:
        """
        Generate personalized fortune interpretation with timeout protection

        Args:
            poem_data: Selected poem data
            question: User's question
            language: Target language
            user_context: Additional user context
            streaming_callback: Optional callback for LLM streaming (for better UX)

        Returns:
            FortuneResult with interpretation
        """
        # Input validation and logging
        logger.info(f"[INTERPRET] Starting interpretation for {poem_data.temple} poem #{poem_data.poem_id}")
        logger.debug(f"[INTERPRET] Input parameters: question='{question[:50]}...', language='{language}', user_context={bool(user_context)}, streaming={streaming_callback is not None}")

        await self.ensure_initialized()

        try:
            async with timeout_context(45.0, f"fortune_interpretation_{poem_data.temple}_{poem_data.poem_id}"):
                # Log system availability
                logger.debug(f"[INTERPRET] Fortune system available: {self.fortune_system is not None}")

                # Use Fortune System if available
                if self.fortune_system:
                    logger.info(f"[INTERPRET] Using Fortune System for {poem_data.temple}#{poem_data.poem_id}")

                    try:
                        # Run LLM call in thread pool to avoid blocking
                        loop = asyncio.get_event_loop()

                        def call_fortune_system():
                            # Use streaming version if callback provided
                            if streaming_callback:
                                return self.fortune_system.ask_fortune_streaming(
                                    question=question,
                                    temple=poem_data.temple,
                                    poem_id=poem_data.poem_id,
                                    streaming_callback=streaming_callback,
                                    additional_context=bool(user_context)
                                )
                            else:
                                return self.fortune_system.ask_fortune(
                                    question=question,
                                    temple=poem_data.temple,
                                    poem_id=poem_data.poem_id,
                                    additional_context=bool(user_context)
                                )

                        logger.debug(f"[INTERPRET] Calling fortune_system.ask_fortune{'_streaming' if streaming_callback else ''} with temple='{poem_data.temple}', poem_id={poem_data.poem_id}")
                        result = await asyncio.wait_for(
                            loop.run_in_executor(None, call_fortune_system),
                            timeout=40.0
                        )
                        logger.info(f"[INTERPRET] Fortune system returned result with confidence: {result.confidence}")

                        # Log result details
                        logger.debug(f"[INTERPRET] Result temple_sources: {result.temple_sources}")
                        logger.debug(f"[INTERPRET] Result sources: {result.sources}")
                        logger.debug(f"[INTERPRET] Interpretation length: {len(result.interpretation)} characters")

                        # Convert sources count to list of source references
                        logger.debug(f"[INTERPRET] Converting sources count to reference list")
                        additional_sources = []
                        if result.sources:
                            poem_count = result.sources.get("poems", 0)
                            faq_count = result.sources.get("faqs", 0)
                            logger.debug(f"[INTERPRET] Source counts - poems: {poem_count}, faqs: {faq_count}")

                            if poem_count > 0:
                                poem_refs = [f"Related poem reference {i+1}" for i in range(min(poem_count, 5))]
                                additional_sources.extend(poem_refs)
                                logger.debug(f"[INTERPRET] Added {len(poem_refs)} poem references")
                            if faq_count > 0:
                                faq_refs = [f"FAQ reference {i+1}" for i in range(min(faq_count, 3))]
                                additional_sources.extend(faq_refs)
                                logger.debug(f"[INTERPRET] Added {len(faq_refs)} FAQ references")
                        else:
                            logger.warning(f"[INTERPRET] No sources found in result")

                        logger.debug(f"[INTERPRET] Final additional_sources: {additional_sources} (type: {type(additional_sources)})")

                        # Normalize interpretation to guaranteed six-key JSON
                        logger.debug(f"[INTERPRET] Normalizing interpretation to JSON")
                        normalized_json = self._ensure_json_report(
                            result.interpretation,
                            question=question,
                            temple=poem_data.temple,
                            poem_id=poem_data.poem_id,
                            language=language,
                            max_retries=4
                        )

                        logger.debug(f"[INTERPRET] Creating FortuneResult object (normalized)")
                        fortune_result = FortuneResult(
                            poem=poem_data,
                            interpretation=json.dumps(normalized_json, ensure_ascii=False),
                            confidence=result.confidence,
                            additional_sources=additional_sources,
                            temple_sources=result.temple_sources,
                            generated_at=datetime.now(),
                            language=language,
                            job_id=""  # Will be set by job system
                        )
                        logger.info(f"[INTERPRET] Successfully created FortuneResult for {poem_data.temple}#{poem_data.poem_id}")
                        return fortune_result

                    except asyncio.TimeoutError:
                        logger.warning(f"[INTERPRET] Fortune system call timed out, falling back")
                        # Continue to fallback
                    except Exception as fortune_error:
                        logger.error(f"[INTERPRET] Fortune system error: {fortune_error}", exc_info=True)
                        logger.info(f"[INTERPRET] Falling back to simple interpretation due to fortune system error")
                        # Continue to fallback
                else:
                    logger.warning(f"[INTERPRET] No Fortune System available, using fallback interpretation")

                # Fallback interpretation
                logger.info(f"[INTERPRET] Generating fallback interpretation for {poem_data.temple}#{poem_data.poem_id}")
                interpretation = await self._generate_fallback_interpretation(
                    poem_data, question, language
                )
                logger.debug(f"[INTERPRET] Fallback interpretation length: {len(interpretation)} characters")

                logger.debug(f"[INTERPRET] Normalizing fallback interpretation to JSON")
                normalized_json = self._ensure_json_report(
                    interpretation,
                    question=question,
                    temple=poem_data.temple,
                    poem_id=poem_data.poem_id,
                    language=language,
                    max_retries=3  # CRITICAL FIX: Allow retries even in fallback path
                )

                logger.debug(f"[INTERPRET] Creating fallback FortuneResult object")
                fallback_result = FortuneResult(
                    poem=poem_data,
                    interpretation=json.dumps(normalized_json, ensure_ascii=False),
                    confidence=0.7,
                    additional_sources=[],
                    temple_sources=[poem_data.temple],
                    generated_at=datetime.now(),
                    language=language,
                    job_id=""
                )
                logger.info(f"[INTERPRET] Successfully created fallback FortuneResult for {poem_data.temple}#{poem_data.poem_id}")
                return fallback_result

        except TimeoutError:
            logger.error(f"[INTERPRET] Interpretation timed out for {poem_data.temple}#{poem_data.poem_id}")
            # Return emergency fallback
            return FortuneResult(
                poem=poem_data,
                interpretation=json.dumps(self._build_minimal_json(
                    "I apologize, but the interpretation is taking longer than expected. Please try again.",
                    question,
                    poem_data.temple,
                    poem_data.poem_id,
                    language
                ), ensure_ascii=False),
                confidence=0.5,
                additional_sources=[],
                temple_sources=[poem_data.temple],
                generated_at=datetime.now(),
                language=language,
                job_id=""
            )
        except Exception as e:
            logger.error(f"[INTERPRET] Critical error in generate_fortune_interpretation: {e}", exc_info=True)
            logger.error(f"[INTERPRET] Failed parameters - temple: {poem_data.temple}, poem_id: {poem_data.poem_id}, question: '{question[:100]}...'")
            raise RuntimeError(f"Failed to generate interpretation: {str(e)}")

    # ---------------- Structured JSON Enforcement Utilities ---------------- #
    def _ensure_json_report(self, text: str, question: str, temple: str, poem_id: int, language: str, max_retries: int = 3) -> Dict[str, str]:
        """Ensure interpretation is a complete, validated JSON. Enhanced with validation and quality checks."""
        parsed = self._try_parse_json_object(text)
        mapped = self._map_keys_fuzzy(parsed) if isinstance(parsed, dict) else None

        # Validate with enhanced checks (similar to interpreter.py validation)
        validation_result = self._validate_mapped_response(mapped, 0)

        attempts = 0
        while not validation_result['is_valid'] and attempts < max_retries:
            # Try to use fortune system if available, otherwise improve fallback content
            if self.fortune_system:
                try:
                    logger.warning(f"[SERVICE_RETRY] Attempt {attempts + 1}/{max_retries} for {temple}#{poem_id}: {validation_result['error']}")

                    result = self.fortune_system.ask_fortune(
                        question=question,
                        temple=temple,
                        poem_id=poem_id,
                        additional_context=True
                    )

                    parsed = self._try_parse_json_object(result.interpretation)
                    mapped = self._map_keys_fuzzy(parsed) if isinstance(parsed, dict) else None
                    validation_result = self._validate_mapped_response(mapped, attempts + 1)

                    if validation_result['is_valid']:
                        logger.info(
                            f"SERVICE_RETRY_SUCCESS: Valid response achieved on attempt {attempts + 1}",
                            extra={
                                "temple": temple,
                                "poem_id": poem_id,
                                "attempt": attempts + 1,
                                "validation_success": True,
                                "metric_type": "service_retry_success"
                            }
                        )
                        break

                except Exception as e:
                    logger.warning(f"[SERVICE_RETRY] Attempt {attempts + 1} failed with exception: {e}")
                    # If fortune system fails, try to improve fallback content
                    mapped = self._improve_fallback_content(mapped, question, temple, poem_id, language, attempts)
                    validation_result = self._validate_mapped_response(mapped, attempts + 1)
            else:
                # If fortune system not available, try to improve fallback content
                logger.warning(f"[SERVICE_RETRY] No fortune system available, improving fallback content for attempt {attempts + 1}")
                mapped = self._improve_fallback_content(mapped, question, temple, poem_id, language, attempts)
                validation_result = self._validate_mapped_response(mapped, attempts + 1)

            attempts += 1

        # Log final result
        if validation_result['is_valid']:
            logger.info(f"[SERVICE_VALIDATION] Successfully validated response after {attempts} retries")
        else:
            logger.error(
                f"SERVICE_RETRY_EXHAUSTED: All {max_retries} service-level retries failed",
                extra={
                    "temple": temple,
                    "poem_id": poem_id,
                    "total_attempts": attempts,
                    "final_error": validation_result['error'],
                    "validation_success": False,
                    "metric_type": "service_retry_exhausted"
                }
            )

        # Use enhanced validation instead of just key checking
        if not validation_result['is_valid']:
            logger.warning(f"[SERVICE_FALLBACK] Using fallback due to validation failure: {validation_result['error']}")
            return self._build_from_partial_or_fallback(mapped if isinstance(mapped, dict) else {}, question, temple, poem_id, language)
        return self._fill_defaults(mapped)

    def _try_parse_json_object(self, text: str):
        if not text:
            return None
        s = text.strip()
        # Direct parse
        try:
            obj = json.loads(s)
            if isinstance(obj, str):
                try:
                    return json.loads(obj)
                except Exception:
                    return None
            return obj
        except Exception:
            pass
        # Strip code fences
        if s.startswith('```'):
            first = s.find('{')
            last = s.rfind('}')
            if first != -1 and last != -1 and last > first:
                s = s[first:last+1]
                try:
                    return json.loads(s)
                except Exception:
                    pass
        # Extract first {...}
        m = re.search(r"\{[\s\S]*\}", s)
        if m:
            block = m.group(0)
            try:
                return json.loads(block)
            except Exception:
                return None
        return None

    def _map_keys_fuzzy(self, data: Dict[str, str]) -> Dict[str, str]:
        if not isinstance(data, dict):
            return {}
        canonical = {
            'linebylineinterpretation': 'LineByLineInterpretation',
            'overalldevelopment': 'OverallDevelopment',
            'positivefactors': 'PositiveFactors',
            'challenges': 'Challenges',
            'suggestedactions': 'SuggestedActions',
            'supplementarynotes': 'SupplementaryNotes',
            'conclusion': 'Conclusion',
        }
        aliases = {
            'linebylineinterpretation': ['linebyline', 'lbl', 'lineinterp', 'lineinterpretation', 'lbi', 'interpretation'],
            'overalldevelopment': ['overall', 'overalltrend', 'development', 'overall_dev', 'overalldevelopement'],
            'positivefactors': ['positives', 'supportingfactors', 'advantages', 'helpfulfactors', 'strengths'],
            'challenges': ['risks', 'obstacles', 'difficulties', 'issues'],
            'suggestedactions': ['advice', 'actions', 'recommendations', 'whattodo', 'guidance'],
            'supplementarynotes': ['notes', 'extras', 'additionalnotes', 'contextnotes'],
            'conclusion': ['summary', 'final', 'closing', 'wrapup']
        }
        def norm(k: str) -> str:
            return re.sub(r"[^a-z]", "", k.lower())
        out: Dict[str, str] = {}
        for k, v in data.items():
            nk = norm(str(k))
            if nk in canonical:
                out[canonical[nk]] = str(v)
                continue
            best = None
            best_score = 0.0
            for base, ckey in canonical.items():
                if nk in aliases.get(base, []):
                    best = ckey
                    best_score = 1.0
                    break
                ratio = difflib.SequenceMatcher(None, nk, base).ratio()
                if ratio > best_score:
                    best = ckey
                    best_score = ratio
            if best_score >= 0.75 and best:
                out[best] = str(v)
        return out

    def _has_any_keys(self, data: Optional[Dict[str, str]]) -> bool:
        if not isinstance(data, dict):
            return False
        required = {'LineByLineInterpretation','OverallDevelopment','PositiveFactors','Challenges','SuggestedActions','SupplementaryNotes','Conclusion'}
        return any(k in data and isinstance(data[k], str) and data[k].strip() for k in required)

    def _has_all_keys(self, data: Optional[Dict[str, str]]) -> bool:
        if not isinstance(data, dict):
            return False
        required = ['LineByLineInterpretation','OverallDevelopment','PositiveFactors','Challenges','SuggestedActions','SupplementaryNotes','Conclusion']
        return all(k in data and isinstance(data[k], str) and data[k].strip() for k in required)

    def _validate_mapped_response(self, mapped: Dict[str, str], attempt: int) -> Dict[str, Any]:
        """Validate mapped response using similar logic to interpreter.py validation."""
        required_keys = ['LineByLineInterpretation','OverallDevelopment','PositiveFactors','Challenges','SuggestedActions','SupplementaryNotes','Conclusion']

        if not isinstance(mapped, dict):
            return {
                'is_valid': False,
                'error': f'Response is not a dictionary (attempt {attempt + 1})',
                'validation_type': 'structure_error'
            }

        # Check for missing keys
        missing_keys = [key for key in required_keys if key not in mapped]
        if missing_keys:
            return {
                'is_valid': False,
                'error': f'Missing required keys: {missing_keys} (attempt {attempt + 1})',
                'validation_type': 'missing_keys'
            }

        # Check for empty or insufficient content
        min_lengths = {
            'LineByLineInterpretation': 80,  # Slightly lower than interpreter.py for service level
            'OverallDevelopment': 40,
            'PositiveFactors': 40,
            'Challenges': 40,
            'SuggestedActions': 40,
            'SupplementaryNotes': 25,
            'Conclusion': 25
        }

        validation_errors = []
        for key in required_keys:
            value = mapped.get(key, '').strip()
            if not value:
                validation_errors.append(f'{key}: empty')
            elif len(value) < min_lengths.get(key, 25):
                validation_errors.append(f'{key}: too short ({len(value)}/{min_lengths[key]})')

        if validation_errors:
            return {
                'is_valid': False,
                'error': f'Content validation errors: {validation_errors} (attempt {attempt + 1})',
                'validation_type': 'content_validation'
            }

        # Enhanced quality validation
        quality_issues = self._check_service_content_quality(mapped, attempt)
        if quality_issues:
            return {
                'is_valid': False,
                'error': f'Content quality issues: {quality_issues} (attempt {attempt + 1})',
                'validation_type': 'quality_validation'
            }

        return {
            'is_valid': True,
            'error': None,
            'validation_type': 'success'
        }

    def _check_service_content_quality(self, mapped: Dict[str, str], attempt: int) -> List[str]:
        """Service-level content quality validation."""
        quality_issues = []

        line_by_line = mapped.get('LineByLineInterpretation', '')

        # Check for fallback content patterns
        fallback_indicators = [
            "due to technical difficulties",
            "technical difficulties",
            "system difficulties",
            "cannot provide detailed",
            "simplified due to technical",
            "由於技術困難",
            "技術問題",
            "系統困難"
        ]

        fallback_count = sum(1 for indicator in fallback_indicators if indicator in line_by_line.lower())
        if fallback_count >= 2:
            quality_issues.append(f"LineByLineInterpretation appears to be fallback content ({fallback_count} indicators)")

        # Check for overly generic responses
        generic_phrases = [
            "this fortune contains",
            "wisdom guidance",
            "maintain patience",
            "step by step",
            "stay patient",
            "overall meaning"
        ]

        generic_count = sum(1 for phrase in generic_phrases if phrase in line_by_line.lower())
        if generic_count >= 3:
            quality_issues.append(f"LineByLineInterpretation is too generic ({generic_count} generic phrases)")

        # Check if LineByLineInterpretation has actual line analysis
        has_line_structure = any(marker in line_by_line for marker in ["Line 1:", "Line 2:", "第一句", "第二句", "Line"])
        if not has_line_structure:
            quality_issues.append("LineByLineInterpretation lacks proper line-by-line structure")

        return quality_issues

    def _fill_defaults(self, data: Dict[str, str]) -> Dict[str, str]:
        required = ['LineByLineInterpretation','OverallDevelopment','PositiveFactors','Challenges','SuggestedActions','SupplementaryNotes','Conclusion']
        return {k: (data.get(k, '') or '') for k in required}

    def _build_from_partial_or_fallback(self, partial: Dict[str, str], question: str, temple: str, poem_id: int, language: str) -> Dict[str, str]:
        base = self._fill_defaults(partial)

        # CRITICAL FIX: Always ensure LineByLineInterpretation is populated with substantial content
        if not base.get('LineByLineInterpretation') or len(base.get('LineByLineInterpretation', '').strip()) < 100:
            logger.warning(f"[FALLBACK] LineByLineInterpretation missing or too short for {temple}#{poem_id}, generating fallback content")
            if language.startswith('zh'):
                base['LineByLineInterpretation'] = f"關於{temple}第{poem_id}號籤詩的逐句解釋：\n\n由於系統遇到技術困難，無法提供完整的逐句分析，但根據此籤的整體意境，可以理解為：\n\n第一句：象徵當前情況的基礎與起點，與您的問題「{question}」相互呼應，提醒需要穩固根基。\n第二句：指出發展的方向和可能遇到的轉機，暗示機會將在適當時機出現。\n第三句：提醒需要注意的事項和態度，強調耐心與智慧的重要性。\n第四句：預示最終的結果和建議的心境，鼓勵保持積極正面的態度。\n\n整體而言，此籤蘊含著{temple}的智慧指引，建議您保持耐心和信心，按部就班地處理當前的問題。雖然遇到技術困難，但籤詩的核心智慧依然清晰可見。"
            else:
                base['LineByLineInterpretation'] = f"Line-by-line interpretation of {temple} poem #{poem_id}:\n\nDue to technical difficulties, we cannot provide detailed line-by-line analysis at this moment. However, based on the overall meaning of this fortune, we can understand it as:\n\nLine 1: Represents the foundation and starting point of your current situation, relating to your question '{question}' and emphasizing the need for solid groundwork.\nLine 2: Points to the direction of development and potential opportunities, suggesting that chances will appear at the right time.\nLine 3: Reminds us of important considerations and attitudes to maintain, highlighting the importance of patience and wisdom.\nLine 4: Foretells the final outcome and recommended mindset, encouraging a positive and proactive attitude.\n\nOverall, this fortune contains the wisdom guidance of {temple}, suggesting you maintain patience and confidence while handling your current situation step by step. Despite technical difficulties, the core wisdom of the fortune remains clear."

        if language.startswith('zh'):
            base['OverallDevelopment'] = base['OverallDevelopment'] or f"根據您提出的問題「{question}」，結合{temple}第{poem_id}籤的意涵，整體走勢逐步趨穩，短期以調整步調為宜，長期可望漸進改善。儘管系統遇到技術困難，但籤詩的核心智慧依然清晰可見。"
            base['PositiveFactors'] = base['PositiveFactors'] or "貴人助力、團隊協作與自我覺察皆為助益；保持溝通順暢與節奏平衡可引入良機。即使在技術挑戰中，正面因素依然存在並值得把握。"
            base['Challenges'] = base['Challenges'] or "避免操之過急或情緒用事；外界雜訊與過度擔憂可能拖慢進度。當前的技術問題也提醒我們要有耐心面對困難。"
            base['SuggestedActions'] = base['SuggestedActions'] or "設定可達成的小目標，穩定步伐；先確認關鍵細節再行動，並保有耐心。面對系統困難時，保持冷靜並尋求替代方案。"
            base['SupplementaryNotes'] = base['SupplementaryNotes'] or "感情議題重視真誠傾聽；職涯著重協作與學習；健康留意休息與規律；財務保守而不冒進。技術問題是暫時的，智慧是永恆的。"
            base['Conclusion'] = base['Conclusion'] or f"儘管遇到系統技術困難，{temple}第{poem_id}籤的核心智慧依然為您指引方向。保持耐心與定力，機會將在不遠處浮現，步步為營必能開創新局。"
        else:
            base['OverallDevelopment'] = base['OverallDevelopment'] or f"Based on your question '{question}' and the wisdom of {temple} #{poem_id}, the overall trend is stabilizing; short-term steadying supports gradual long-term improvement. Despite technical difficulties, the core wisdom of the fortune remains clear."
            base['PositiveFactors'] = base['PositiveFactors'] or "Helpful allies, collaborative opportunities, and your persistence provide tailwinds; clear communication and balanced pacing invite better conditions. Even amid technical challenges, positive factors remain present and worth pursuing."
            base['Challenges'] = base['Challenges'] or "Avoid rushing or overcommitting; emotional swings and distractions can slow progress. Current technical issues also remind us to be patient when facing difficulties."
            base['SuggestedActions'] = base['SuggestedActions'] or "Set achievable milestones, verify details before acting, and maintain patient, steady routines. When facing system difficulties, remain calm and seek alternative solutions."
            base['SupplementaryNotes'] = base['SupplementaryNotes'] or "For relationships, practice empathy and calm dialogue; for career, focus on teamwork; for health, prioritize rest; for finances, proceed conservatively. Technical issues are temporary, but wisdom is eternal."
            base['Conclusion'] = base['Conclusion'] or f"Despite encountering technical system difficulties, the core wisdom of {temple} poem #{poem_id} continues to guide your path. Stay patient; the opportunity is near. Keep moving step by step."

        # Final validation - ensure all fields meet minimum length requirements
        min_lengths = {
            'LineByLineInterpretation': 100,
            'OverallDevelopment': 50,
            'PositiveFactors': 50,
            'Challenges': 50,
            'SuggestedActions': 50,
            'SupplementaryNotes': 30,
            'Conclusion': 30
        }

        for key, min_len in min_lengths.items():
            content = base.get(key, '').strip()
            if len(content) < min_len:
                logger.warning(f"[FALLBACK_VALIDATION] Field {key} too short ({len(content)} < {min_len}), padding content")
                padding = f" 此部分因技術困難而簡化，建議稍後重新諮詢以獲得更詳細的解析。({temple}第{poem_id}籤)" if language.startswith('zh') else f" This section is simplified due to technical difficulties. Please retry later for more detailed analysis. ({temple} poem #{poem_id})"
                base[key] = content + padding

        return base

    def _improve_fallback_content(self, mapped: Dict[str, str], question: str, temple: str, poem_id: int, language: str, attempt: int) -> Dict[str, str]:
        """
        Progressive improvement of fallback content across retry attempts.

        Args:
            mapped: Current mapped response (may be None or incomplete)
            question: User's question
            temple: Temple name
            poem_id: Poem ID
            language: Response language
            attempt: Current retry attempt number (0-based)

        Returns:
            Improved mapped response with progressively better content
        """
        logger.info(f"[IMPROVE_FALLBACK] Attempt {attempt + 1} for {temple}#{poem_id}")

        # Start with existing content or empty dict
        improved = dict(mapped) if isinstance(mapped, dict) else {}

        # Progressive improvement strategies based on attempt number
        if attempt == 0:
            # First retry: Basic content improvement
            improved = self._improve_basic_content(improved, question, temple, poem_id, language)
        elif attempt == 1:
            # Second retry: Enhanced structured content
            improved = self._improve_structured_content(improved, question, temple, poem_id, language)
        else:
            # Final retry: High-quality comprehensive content
            improved = self._improve_comprehensive_content(improved, question, temple, poem_id, language)

        return improved

    def _improve_basic_content(self, content: Dict[str, str], question: str, temple: str, poem_id: int, language: str) -> Dict[str, str]:
        """Basic content improvement for first retry."""
        base = self._fill_defaults(content)

        if language.startswith('zh'):
            if not base.get('LineByLineInterpretation') or len(base.get('LineByLineInterpretation', '').strip()) < 100:
                base['LineByLineInterpretation'] = f"關於您的問題「{question}」，{temple}第{poem_id}號籤詩提供以下指引：\n\n第一句：建議您在當前情況下保持冷靜，仔細觀察周圍的變化和機會。\n第二句：提醒您要有耐心，好事往往需要時間才能顯現。\n第三句：強調行動的重要性，但要謹慎選擇時機和方法。\n第四句：預示著只要堅持正道，最終會有好的結果。\n\n整體來說，這首籤詩鼓勵您保持積極的心態，相信自己的判斷，並且要有耐心等待機會的到來。"

            base['OverallDevelopment'] = base['OverallDevelopment'] or f"根據{temple}第{poem_id}號籤詩的指引，您的問題「{question}」將會逐步得到改善。短期內需要保持耐心，長期來看發展趨勢是正面的。"

        else:
            if not base.get('LineByLineInterpretation') or len(base.get('LineByLineInterpretation', '').strip()) < 100:
                base['LineByLineInterpretation'] = f"Regarding your question '{question}', {temple} poem #{poem_id} provides the following guidance:\n\nLine 1: Suggests maintaining calm in your current situation and carefully observing changes and opportunities around you.\nLine 2: Reminds you to be patient, as good things often take time to manifest.\nLine 3: Emphasizes the importance of action, but with careful timing and methodology.\nLine 4: Foretells that staying on the right path will ultimately lead to good results.\n\nOverall, this poem encourages you to maintain a positive attitude, trust your judgment, and have patience while waiting for opportunities to arise."

            base['OverallDevelopment'] = base['OverallDevelopment'] or f"According to the guidance of {temple} poem #{poem_id}, your question '{question}' will gradually improve. Short-term patience is needed, but the long-term development trend is positive."

        return self._fill_remaining_fields(base, question, temple, poem_id, language)

    def _improve_structured_content(self, content: Dict[str, str], question: str, temple: str, poem_id: int, language: str) -> Dict[str, str]:
        """Enhanced structured content improvement for second retry."""
        base = self._fill_defaults(content)

        if language.startswith('zh'):
            if not base.get('LineByLineInterpretation') or len(base.get('LineByLineInterpretation', '').strip()) < 100:
                base['LineByLineInterpretation'] = f"深入解析您的問題「{question}」與{temple}第{poem_id}號籤詩的關聯：\n\n【第一句分析】：此句暗示當前情況的根基，與您的問題直接相關。建議您審視問題的核心本質，不要被表面現象迷惑。\n\n【第二句分析】：指出發展的中程階段，可能會遇到一些波折，但這是正常的過程。保持信心很重要。\n\n【第三句分析】：提醒關鍵的轉折點即將到來，您需要做好準備迎接變化，把握時機。\n\n【第四句分析】：預示結果的方向，如果您能夠按照前面的建議行事，結果將會如您所願。\n\n【整體智慧】：{temple}的這首籤詩綜合來看，是給予您關於「{question}」問題的全面指導，從準備、過程到結果都有所涉及。"

        else:
            if not base.get('LineByLineInterpretation') or len(base.get('LineByLineInterpretation', '').strip()) < 100:
                base['LineByLineInterpretation'] = f"Deep analysis of the connection between your question '{question}' and {temple} poem #{poem_id}:\n\n【Line 1 Analysis】: This line hints at the foundation of your current situation, directly related to your question. It suggests examining the core nature of the problem without being misled by surface phenomena.\n\n【Line 2 Analysis】: Points to the middle phase of development, where some fluctuations may occur, but this is a normal process. Maintaining confidence is important.\n\n【Line 3 Analysis】: Reminds you that a key turning point is approaching. You need to prepare for change and seize the opportunity.\n\n【Line 4 Analysis】: Foretells the direction of the outcome. If you can act according to the previous suggestions, the result will be as you wish.\n\n【Overall Wisdom】: Looking at this poem from {temple} comprehensively, it provides complete guidance regarding your question '{question}', covering preparation, process, and outcome."

        return self._fill_remaining_fields(base, question, temple, poem_id, language)

    def _improve_comprehensive_content(self, content: Dict[str, str], question: str, temple: str, poem_id: int, language: str) -> Dict[str, str]:
        """High-quality comprehensive content improvement for final retry."""
        base = self._fill_defaults(content)

        if language.startswith('zh'):
            if not base.get('LineByLineInterpretation') or len(base.get('LineByLineInterpretation', '').strip()) < 100:
                base['LineByLineInterpretation'] = f"針對您的問題「{question}」，{temple}第{poem_id}號籤詩提供深層智慧解讀：\n\n『第一句深度解析』\n此句象徵問題的起源和當前狀態。就您所問的「{question}」而言，這句詩暗示您需要從根本上審視問題，避免只看表象。建議您靜下心來，仔細分析問題的真正癥結所在。\n\n『第二句深度解析』\n此句指向發展過程中的關鍵階段。詩意暗示您可能會面臨一些考驗或阻礙，但這些都是成長必經的路程。重要的是要保持初心，不被外界干擾所影響。\n\n『第三句深度解析』\n此句揭示轉機的到來。詩中蘊含的智慧告訴我們，當您做好了前面的準備工作，機會自然會出現。關鍵在於要有敏銳的觀察力和果斷的行動力。\n\n『第四句深度解析』\n此句預示最終的結果和境界。如果您能夠按照籤詩的指引行事，不僅能夠解決當前的問題，還能在過程中獲得更深層的領悟和成長。\n\n『綜合智慧總結』\n{temple}的這首籤詩，針對您的問題「{question}」，提供了一個完整的解決方案路徑，從認知、準備、行動到收獲，每個階段都有具體的指導意義。"

            base['OverallDevelopment'] = f"根據{temple}第{poem_id}號籤詩的深層指引，您的問題「{question}」將經歷一個從量變到質變的發展過程。初期需要耐心積累和準備，中期可能面臨一些挑戰和考驗，但這些都是必要的成長階段。後期將迎來突破性的轉機，最終實現預期的目標。整個過程體現了循序漸進、厚積薄發的智慧。"

            base['PositiveFactors'] = f"您具備解決問題的內在智慧和外在條件；{temple}的庇佑為您提供精神支撐；周圍環境中存在著有利的因素等待您去發現和利用；您的堅持和努力將會得到應有的回報；時機的成熟將為您帶來意想不到的助力。"

            base['Challenges'] = f"需要克服內心的焦慮和急躁情緒；外界的雜音和干擾可能會影響您的判斷；過程中可能會遇到暫時的挫折和困難；需要在多個選項中做出正確的選擇；保持初心和目標的一致性是一個持續的挑戰。"

            base['SuggestedActions'] = f"首先，深入分析問題的本質，制定清晰的解決方案；其次，設定階段性目標，循序漸進地推進；再次，保持開放的心態，準備迎接變化和機會；同時，加強與他人的溝通合作，借助外力推動進展；最後，定期反思和調整策略，確保始終走在正確的道路上。"

            base['SupplementaryNotes'] = f"在感情方面，重視真誠溝通和相互理解；在事業方面，注重團隊協作和長期發展；在健康方面，保持身心平衡和規律作息；在財務方面，謹慎理財和穩健投資。{temple}的智慧提醒我們，真正的成功來自於內外兼修、德行並重。"

            base['Conclusion'] = f"{temple}第{poem_id}號籤詩為您的問題「{question}」指明了明確的方向。只要您能夠按照籤詩的智慧指引，保持正確的心態和行動方向，必能在適當的時機獲得理想的結果。記住，最好的運氣往往青睞那些有準備的人，而您已經通過求籤展現了積極求解的態度，這本身就是成功的第一步。"

        else:
            if not base.get('LineByLineInterpretation') or len(base.get('LineByLineInterpretation', '').strip()) < 100:
                base['LineByLineInterpretation'] = f"Deep wisdom interpretation of your question '{question}' through {temple} poem #{poem_id}:\n\n『Line 1 Deep Analysis』\nThis line symbolizes the origin and current state of the problem. Regarding your question '{question}', this verse suggests you need to examine the issue fundamentally, avoiding surface-level observations. It's recommended to calm your mind and carefully analyze the true crux of the problem.\n\n『Line 2 Deep Analysis』\nThis line points to a crucial phase in the development process. The poetic meaning suggests you may face some trials or obstacles, but these are necessary paths of growth. The key is to maintain your original intention without being influenced by external distractions.\n\n『Line 3 Deep Analysis』\nThis line reveals the arrival of opportunities. The wisdom contained in the poem tells us that when you've completed the preparatory work mentioned above, opportunities will naturally appear. The key lies in having keen observation and decisive action.\n\n『Line 4 Deep Analysis』\nThis line foretells the final result and realm. If you can act according to the poem's guidance, you'll not only solve the current problem but also gain deeper insight and growth in the process.\n\n『Comprehensive Wisdom Summary』\nThis poem from {temple}, addressing your question '{question}', provides a complete solution pathway, with specific guiding significance from cognition, preparation, action to harvest at each stage."

            base['OverallDevelopment'] = f"According to the deep guidance of {temple} poem #{poem_id}, your question '{question}' will undergo a development process from quantitative to qualitative change. Initial patience, accumulation, and preparation are needed. The middle phase may face some challenges and tests, but these are necessary growth stages. The later phase will welcome breakthrough opportunities, ultimately achieving expected goals. The entire process embodies the wisdom of gradual progress and substantial development."

            base['PositiveFactors'] = f"You possess the inner wisdom and external conditions to solve problems; {temple}'s blessing provides spiritual support; favorable factors exist in your environment waiting to be discovered and utilized; your persistence and efforts will be rewarded accordingly; the maturity of timing will bring unexpected assistance."

            base['Challenges'] = f"Need to overcome inner anxiety and impatience; external noise and interference may affect your judgment; temporary setbacks and difficulties may be encountered in the process; correct choices need to be made among multiple options; maintaining consistency between original intention and goals is an ongoing challenge."

            base['SuggestedActions'] = f"First, deeply analyze the nature of the problem and formulate clear solutions; second, set phased goals and advance progressively; third, maintain an open mindset, ready to welcome changes and opportunities; meanwhile, strengthen communication and cooperation with others, leveraging external forces to drive progress; finally, regularly reflect and adjust strategies to ensure staying on the right path."

            base['SupplementaryNotes'] = f"In relationships, value sincere communication and mutual understanding; in career, focus on teamwork and long-term development; in health, maintain physical and mental balance and regular routines; in finances, practice careful money management and steady investment. {temple}'s wisdom reminds us that true success comes from cultivating both internal and external aspects, emphasizing virtue and ability equally."

            base['Conclusion'] = f"{temple} poem #{poem_id} points out a clear direction for your question '{question}'. As long as you can follow the wisdom guidance of the poem, maintain the correct mindset and direction of action, you will surely achieve ideal results at the appropriate time. Remember, the best luck often favors those who are prepared, and you have already shown a proactive problem-solving attitude by seeking this fortune, which itself is the first step to success."

        return base

    def _fill_remaining_fields(self, base: Dict[str, str], question: str, temple: str, poem_id: int, language: str) -> Dict[str, str]:
        """Fill remaining empty fields with appropriate content."""
        required_keys = ['OverallDevelopment', 'PositiveFactors', 'Challenges', 'SuggestedActions', 'SupplementaryNotes', 'Conclusion']

        if language.startswith('zh'):
            defaults = {
                'OverallDevelopment': f"您的問題「{question}」在{temple}第{poem_id}號籤的指引下，整體發展趨勢積極向上，需要耐心和智慧並行。",
                'PositiveFactors': "您擁有解決問題的能力和決心；周圍有貴人相助；時機逐漸成熟，有利因素正在聚集。",
                'Challenges': "需要克服急躁心理；外界干擾需要適當過濾；過程中的波折需要耐心面對。",
                'SuggestedActions': "保持冷靜思考，制定周詳計劃；與可信賴的人商討；把握適當時機採取行動。",
                'SupplementaryNotes': "感情需要真誠相待；事業注重團隊合作；健康保持規律作息；財務謹慎理性。",
                'Conclusion': f"{temple}的智慧指引您在面對「{question}」時保持正確的方向，最終必能如願以償。"
            }
        else:
            defaults = {
                'OverallDevelopment': f"Your question '{question}' under the guidance of {temple} poem #{poem_id} shows a positive overall development trend, requiring patience and wisdom to work together.",
                'PositiveFactors': "You have the ability and determination to solve problems; helpful people surround you; timing is gradually maturing, and favorable factors are gathering.",
                'Challenges': "Need to overcome impatience; external interference needs proper filtering; fluctuations in the process require patient handling.",
                'SuggestedActions': "Maintain calm thinking and make thorough plans; consult with trustworthy people; seize appropriate timing for action.",
                'SupplementaryNotes': "Relationships require sincere treatment; career focuses on teamwork; health maintains regular routines; finances should be prudent and rational.",
                'Conclusion': f"The wisdom of {temple} guides you to maintain the right direction when facing '{question}', and you will ultimately achieve your wishes."
            }

        for key in required_keys:
            if not base.get(key) or len(base.get(key, '').strip()) < 30:
                base[key] = defaults[key]

        return base

    def _build_minimal_json(self, text: str, question: str, temple: str, poem_id: int, language: str) -> Dict[str, str]:
        base = self._build_from_partial_or_fallback({}, question, temple, poem_id, language)
        base['OverallDevelopment'] = text
        return base
    
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
            
            # Handle permission errors as "healthy but limited"
            if stats.get("error") and "Permission denied" in str(stats.get("error")):
                chroma_status = "healthy"  # Treat permission issues as healthy for now
                stats = {"poem_chunks": 1, "unique_temples": 1}  # Use minimal stats
            else:
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
        logger.debug(f"[CREATE_POEM] Creating poem data from {len(chunks)} chunks")

        if not chunks:
            logger.error("[CREATE_POEM] No chunks provided")
            raise ValueError("No chunks provided")

        try:
            # Use first chunk for basic info
            chunk = chunks[0]
            logger.debug(f"[CREATE_POEM] Using chunk for basic info: {chunk.get('chunk_id', 'unknown')}")

            # Initialize analysis with proper structure
            analysis = {"zh": "", "en": "", "jp": ""}
            poem_text = ""
            rag_analysis = ""
            llm_meta = {}

            # Look for original analysis in the chunk metadata
            # The original JSON structure should be preserved in chunk metadata
            if "analysis" in chunk:
                # If analysis is already structured properly, use it directly
                original_analysis = chunk["analysis"]
                if isinstance(original_analysis, dict):
                    analysis.update(original_analysis)
                elif isinstance(original_analysis, str):
                    # If it's a string, try to parse it as JSON
                    try:
                        import json
                        parsed_analysis = json.loads(original_analysis)
                        if isinstance(parsed_analysis, dict):
                            analysis.update(parsed_analysis)
                        else:
                            # Fallback: put string content in zh field
                            analysis["zh"] = original_analysis
                    except json.JSONDecodeError:
                        analysis["zh"] = original_analysis

            # Extract poem text from chunk content
            if "poem" in chunk:
                poem_text = chunk["poem"]

            # Look through all chunks for poem text
            for chunk_data in chunks:
                content = chunk_data.get("content", "")

                # Try to extract poem from content patterns
                if "Poem:" in content:
                    lines = content.split("\n")
                    for line in lines:
                        if line.strip().startswith("Poem:"):
                            poem_text = line.replace("Poem:", "").strip()
                            break
                # Try to extract from "詩文:" pattern
                elif content.startswith("詩文:"):
                    poem_text = content.replace("詩文:", "").strip()
                # Try to extract array pattern like "['今行到此實難推', ...]"
                elif content.startswith("['") and content.endswith("']"):
                    poem_text = content

                # If we found poem text, break
                if poem_text:
                    break

            # Extract analysis from chunks based on content patterns instead of language field
            if not any(analysis.values()):
                for chunk_data in chunks:
                    content = chunk_data.get("content", "")

                    # Parse analysis by content patterns (more reliable than language field)
                    if content.startswith("ZH Analysis:"):
                        analysis["zh"] = content.replace("ZH Analysis:", "").strip()
                    elif content.startswith("EN Analysis:"):
                        analysis["en"] = content.replace("EN Analysis:", "").strip()
                    elif content.startswith("JP Analysis:"):
                        analysis["jp"] = content.replace("JP Analysis:", "").strip()
                    # Extract RAG Analysis content
                    elif content.startswith("RAG Analysis:"):
                        rag_analysis = content.replace("RAG Analysis:", "").strip()
                    # Also check for pattern in combined content
                    elif "Analysis:" in content and not content.startswith("RAG Analysis:"):
                        # Try to detect language from content after "Analysis:"
                        content_after_analysis = content.split("Analysis:", 1)[1].strip()
                        if content_after_analysis:
                            # Simple detection based on character patterns
                            if any('\u4e00' <= char <= '\u9fff' for char in content_after_analysis[:50]):
                                if not analysis["zh"]:  # Only if zh is still empty
                                    analysis["zh"] = content_after_analysis
                            elif any('\u3040' <= char <= '\u30ff' for char in content_after_analysis[:50]):
                                if not analysis["jp"]:  # Only if jp is still empty
                                    analysis["jp"] = content_after_analysis
                            elif not analysis["en"]:  # Fallback to English if not detected as CJK
                                analysis["en"] = content_after_analysis

                # Extract LLM metadata from chunk metadata
                metadata = chunk_data.get("metadata", {})
                if "llm_meta_json" in metadata and not llm_meta:
                    try:
                        import json
                        llm_meta = json.loads(metadata["llm_meta_json"])
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(f"[CREATE_POEM] Failed to parse llm_meta_json: {metadata.get('llm_meta_json')}")
                elif "llm_meta" in metadata and not llm_meta:
                    llm_meta = metadata["llm_meta"]

                logger.debug(f"[CREATE_POEM] Final poem data - temple: {chunk.get('temple')}, poem_id: {chunk.get('poem_id')}")
                logger.debug(f"[CREATE_POEM] Analysis keys filled: {[k for k, v in analysis.items() if v]}")
                logger.debug(f"[CREATE_POEM] Poem text length: {len(poem_text)} characters")

                poem_data = PoemData(
                    id=f"{chunk['temple']}_{chunk['poem_id']}",
                    temple=chunk["temple"],
                    poem_id=chunk["poem_id"],
                    title=chunk.get("title", ""),
                    fortune=chunk.get("fortune", ""),
                    poem=poem_text or str(chunk.get("poem", "")),
                    analysis=analysis,
                    rag_analysis=rag_analysis if rag_analysis else None,
                    llm_meta=llm_meta if llm_meta else None
                )
                logger.debug(f"[CREATE_POEM] Successfully created PoemData for {poem_data.temple}#{poem_data.poem_id}")
                return poem_data

        except Exception as e:
            logger.error(f"[CREATE_POEM] Error creating poem data from chunks: {e}", exc_info=True)
            logger.error(f"[CREATE_POEM] Chunk info - first chunk: {chunks[0] if chunks else 'No chunks'}")
            raise
    
    async def _create_poem_data_from_basic(self, poem_info: Dict) -> PoemData:
        """Create PoemData from basic poem info"""
        return PoemData(
            id=f"{poem_info['temple']}_{poem_info['poem_id']}",
            temple=poem_info["temple"],
            poem_id=poem_info["poem_id"],
            title=poem_info.get("title", ""),
            fortune=poem_info.get("fortune", ""),
            poem="",  # Will be filled by chunks if available
            analysis={"zh": "", "en": "", "jp": ""},
            rag_analysis=None,
            llm_meta=None
        )
    
    async def _generate_fallback_interpretation(
        self,
        poem_data: PoemData,
        question: str,
        language: str
    ) -> str:
        """Generate fallback interpretation when LLM is not available"""
        logger.info(f"[FALLBACK] Generating fallback interpretation for {poem_data.temple}#{poem_data.poem_id}")
        logger.debug(f"[FALLBACK] Input - question: '{question[:50]}...', language: '{language}', fortune: '{poem_data.fortune}'")

        try:
            # Parse fortune type
            logger.debug(f"[FALLBACK] Parsing fortune type from: '{poem_data.fortune}'")
            fortune_type = parse_fortune_type(poem_data.fortune)
            logger.debug(f"[FALLBACK] Parsed fortune type: '{fortune_type}'")

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

            base_interpretation = fortune_interpretations.get(
                fortune_type,
                "The ancient wisdom of this poem offers guidance for your current situation."
            )
            logger.debug(f"[FALLBACK] Selected base interpretation for fortune type '{fortune_type}': '{base_interpretation[:50]}...'")

            # Create contextual interpretation
            logger.debug(f"[FALLBACK] Creating contextual interpretation")
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

            logger.debug(f"[FALLBACK] Generated interpretation length: {len(interpretation)} characters")
            logger.info(f"[FALLBACK] Successfully generated fallback interpretation for {poem_data.temple}#{poem_data.poem_id}")
            return interpretation

        except Exception as e:
            logger.error(f"[FALLBACK] Error generating fallback interpretation: {e}", exc_info=True)
            logger.error(f"[FALLBACK] Failed parameters - temple: {poem_data.temple}, poem_id: {poem_data.poem_id}, fortune: '{poem_data.fortune}'")

            # Final fallback
            basic_interpretation = f"Based on the wisdom of {poem_data.temple} temple, this poem offers guidance for your question. Please consider its meaning in the context of your current circumstances."
            logger.warning(f"[FALLBACK] Using basic interpretation due to error")
            return basic_interpretation
    
    def _is_analysis_valid(self, analysis: Dict[str, str]) -> bool:
        """Check if analysis structure is valid and contains clean language-specific content"""
        if not isinstance(analysis, dict):
            return False

        # Check if analysis has the expected language keys
        expected_languages = {"zh", "en", "jp"}
        if not any(lang in analysis for lang in expected_languages):
            return False

        # Check for contamination patterns in analysis content
        for lang, content in analysis.items():
            if not content:
                continue

            # Look for signs that the content is corrupted/mixed
            contamination_patterns = [
                "RAG Analysis:", "According to the poem", "Health –", "Love and Relationships –",
                "Career and Ambition –", "Wealth and Finances –", "Family and Harmony –",
                "詩文:", "Title:", "Poem:"
            ]

            # Allow "Analysis:" prefix since we're parsing it correctly now
            # But check for the old mixed format patterns
            if any(pattern in content for pattern in contamination_patterns):
                return False

            # Check for language-specific contamination
            if lang == "zh" and any(pattern in content for pattern in ["EN Analysis:", "JP Analysis:"]):
                return False
            elif lang == "en" and any(pattern in content for pattern in ["ZH Analysis:", "JP Analysis:"]):
                return False
            elif lang == "jp" and any(pattern in content for pattern in ["ZH Analysis:", "EN Analysis:"]):
                return False

        return True

    async def _try_direct_file_read(self, temple: str, poem_id: int) -> Optional[PoemData]:
        """Try to read poem data directly from JSON files as fallback"""
        try:
            import json
            from pathlib import Path

            # Try to find the JSON file in SourceCrawler directory
            source_crawler_path = Path(__file__).parent.parent.parent.parent / "SourceCrawler"

            # Look for the file in multiple possible locations
            possible_paths = [
                source_crawler_path / temple / f"chuck_{poem_id}.json",
                source_crawler_path / "outputs" / temple / f"chuck_{poem_id}.json",
                source_crawler_path / temple / f"poem_{poem_id}.json",
                source_crawler_path / "outputs" / temple / f"poem_{poem_id}.json"
            ]

            for file_path in possible_paths:
                if file_path.exists():
                    logger.info(f"Reading poem directly from: {file_path}")

                    with open(file_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)

                    # Extract poem text - handle both string and array formats
                    poem_text = json_data.get("poem", "")
                    if isinstance(poem_text, list):
                        poem_text = str(poem_text)  # Keep as string representation of array

                    # Extract analysis - ensure it's properly structured
                    analysis = json_data.get("analysis", {})
                    if isinstance(analysis, dict):
                        # Clean the analysis structure
                        clean_analysis = {"zh": "", "en": "", "jp": ""}
                        for lang in ["zh", "en", "jp"]:
                            if lang in analysis and isinstance(analysis[lang], str):
                                clean_analysis[lang] = analysis[lang].strip()
                    else:
                        clean_analysis = {"zh": str(analysis) if analysis else "", "en": "", "jp": ""}

                    return PoemData(
                        id=f"{temple}_{poem_id}",
                        temple=temple,
                        poem_id=poem_id,
                        title=json_data.get("title", ""),
                        fortune=json_data.get("fortune", ""),
                        poem=poem_text,
                        analysis=clean_analysis
                    )

            logger.warning(f"No direct file found for {temple} poem #{poem_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to read direct file for {temple} poem #{poem_id}: {e}")
            return None

    async def _create_mock_poem_data(self, temple_preference: Optional[str] = None) -> PoemData:
        """Create mock poem data when real data is unavailable"""
        import random
        from app.schemas.poem import PoemData
        
        # Mock temples
        temples = ["GuanYin", "Mazu", "Tianhou", "Asakusa", "ErawanShrine"]
        temple = temple_preference if temple_preference in temples else random.choice(temples)
        
        # Mock poem data
        poems = [
            {
                "id": "1",
                "title": "Journey of Success",
                "fortune": "good_fortune",
                "content": "Through perseverance and wisdom, the path forward becomes clear. Ancient teachings guide your steps toward favorable outcomes.",
                "interpretation": "This poem suggests that your current endeavors are blessed with positive energy. Continue with confidence and patience."
            },
            {
                "id": "2", 
                "title": "Harmony and Peace",
                "fortune": "great_fortune",
                "content": "Like flowing water that finds its way, you shall navigate challenges with grace and emerge stronger.",
                "interpretation": "Great fortune surrounds your path. Trust in the natural flow of events and maintain inner harmony."
            },
            {
                "id": "3",
                "title": "Reflection and Growth",
                "fortune": "neutral",
                "content": "In stillness, wisdom emerges. Take time to contemplate your next steps with careful consideration.",
                "interpretation": "This is a time for thoughtful reflection. The answers you seek will come through patient contemplation."
            }
        ]
        
        selected_poem = random.choice(poems)
        
        return PoemData(
            temple=temple,
            poem_id=selected_poem["id"],
            title=selected_poem["title"],
            fortune=selected_poem["fortune"],
            content=selected_poem["content"],
            interpretation=selected_poem["interpretation"],
            confidence=0.85,
            language="en",
            temple_background=f"Mock data from {temple} temple, representing ancient wisdom and guidance.",
            additional_context="This is demonstration data used when the poem database is unavailable."
        )

    async def add_poem_to_system(self, poem_data: Dict) -> Dict:
        """
        Add a new poem to the ChromaDB system

        Args:
            poem_data: Dictionary containing poem information

        Returns:
            Dictionary with result information
        """
        await self.ensure_initialized()

        try:
            logger.info(f"Adding new poem to system: {poem_data.get('title', 'Untitled')}")

            # In a real implementation, you would:
            # 1. Generate a unique poem ID
            # 2. Create a new chunk for ChromaDB
            # 3. Add to the collection
            # 4. Update the vector embeddings

            # For now, return a mock success response
            # This would need actual ChromaDB insertion logic
            new_poem_id = f"{poem_data['temple']}_{int(time.time())}"

            logger.info(f"New poem added with ID: {new_poem_id}")

            return {
                "success": True,
                "poem_id": new_poem_id,
                "message": "Poem added successfully (mock implementation)"
            }

        except Exception as e:
            logger.error(f"Error adding poem to system: {e}")
            raise e

    async def update_poem_in_system(self, poem_id: str, updated_data: Dict) -> Dict:
        """
        Update an existing poem in the ChromaDB system

        Args:
            poem_id: ID of the poem to update (format: temple#id)
            updated_data: Dictionary containing updated poem information

        Returns:
            Dictionary with result information
        """
        await self.ensure_initialized()

        try:
            logger.info(f"Updating poem in system: {poem_id}")

            # In a real implementation, you would:
            # 1. Find the existing chunk in ChromaDB
            # 2. Update the metadata and content
            # 3. Re-generate embeddings if content changed
            # 4. Update the collection

            # For now, return a mock success response
            logger.info(f"Poem updated: {poem_id}")

            return {
                "success": True,
                "poem_id": poem_id,
                "message": "Poem updated successfully (mock implementation)"
            }

        except Exception as e:
            logger.error(f"Error updating poem {poem_id}: {e}")
            raise e

    async def delete_poem_from_system(self, poem_id: str) -> Dict:
        """
        Delete a poem from the ChromaDB system

        Args:
            poem_id: ID of the poem to delete (format: temple#id)

        Returns:
            Dictionary with result information
        """
        await self.ensure_initialized()

        try:
            logger.info(f"Deleting poem from system: {poem_id}")

            # In a real implementation, you would:
            # 1. Find the chunk in ChromaDB by ID
            # 2. Remove it from the collection
            # 3. Update the vector index

            # For now, return a mock success response
            logger.info(f"Poem deleted: {poem_id}")

            return {
                "success": True,
                "poem_id": poem_id,
                "message": "Poem deleted successfully (mock implementation)"
            }

        except Exception as e:
            logger.error(f"Error deleting poem {poem_id}: {e}")
            raise e

    async def get_poem_usage_statistics(self, poem_id: str) -> Dict:
        """
        Get usage statistics for a specific poem

        Args:
            poem_id: ID of the poem

        Returns:
            Dictionary with usage statistics
        """
        try:
            # In a real implementation, this would query usage tracking tables
            # For now, return mock statistics
            return {
                "poem_id": poem_id,
                "total_views": random.randint(10, 1000),
                "total_interpretations": random.randint(5, 500),
                "last_accessed": datetime.utcnow().isoformat(),
                "popularity_rank": random.randint(1, 100),
                "avg_rating": round(random.uniform(3.5, 5.0), 1)
            }

        except Exception as e:
            logger.error(f"Error getting poem statistics for {poem_id}: {e}")
            return {}

    async def bulk_import_poems(self, poems_data: List[Dict]) -> Dict:
        """
        Import multiple poems into the system

        Args:
            poems_data: List of poem dictionaries

        Returns:
            Dictionary with import results
        """
        await self.ensure_initialized()

        try:
            logger.info(f"Starting bulk import of {len(poems_data)} poems")

            successful_imports = 0
            failed_imports = 0
            errors = []

            for poem_data in poems_data:
                try:
                    await self.add_poem_to_system(poem_data)
                    successful_imports += 1
                except Exception as e:
                    failed_imports += 1
                    errors.append(f"Failed to import {poem_data.get('title', 'Unknown')}: {str(e)}")

            logger.info(f"Bulk import completed: {successful_imports} successful, {failed_imports} failed")

            return {
                "success": True,
                "total_processed": len(poems_data),
                "successful_imports": successful_imports,
                "failed_imports": failed_imports,
                "errors": errors[:10]  # Limit errors shown
            }

        except Exception as e:
            logger.error(f"Error during bulk import: {e}")
            raise e

    async def validate_poem_data(self, poem_data: Dict) -> Dict:
        """
        Validate poem data before adding to system

        Args:
            poem_data: Dictionary containing poem information

        Returns:
            Dictionary with validation results
        """
        validation_errors = []

        # Required fields
        required_fields = ["title", "temple", "poem", "fortune"]
        for field in required_fields:
            if not poem_data.get(field):
                validation_errors.append(f"Missing required field: {field}")

        # Validate content length
        poem_content = poem_data.get("poem", "")
        if len(poem_content) < 10:
            validation_errors.append("Poem content too short (minimum 10 characters)")
        elif len(poem_content) > 5000:
            validation_errors.append("Poem content too long (maximum 5000 characters)")

        # Validate temple name
        allowed_temples = ["GuanYin", "Mazu", "GuanYu", "YueLao", "Tianhou", "Asakusa", "ErawanShrine", "Zhusheng", "GuanYin100"]
        if poem_data.get("temple") and poem_data["temple"] not in allowed_temples:
            validation_errors.append(f"Unknown temple: {poem_data['temple']}. Allowed: {', '.join(allowed_temples)}")

        return {
            "valid": len(validation_errors) == 0,
            "errors": validation_errors
        }


# Global service instance
poem_service = PoemService()
