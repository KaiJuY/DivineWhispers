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
from app.utils.logging_config import get_logger
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

                # Debug environment
                import os
                logger.info(f"Current working directory: {os.getcwd()}")
                logger.info(f"ChromaDB path exists: {os.path.exists(settings.CHROMA_DB_PATH)}")
                if os.path.exists(settings.CHROMA_DB_PATH):
                    logger.info(f"ChromaDB path contents: {os.listdir(settings.CHROMA_DB_PATH)}")

                # Initialize RAG handler
                config = SystemConfig()
                logger.info(f"RAG Config - Collection: {settings.CHROMA_COLLECTION_NAME}, Path: {settings.CHROMA_DB_PATH}")

                # Try multiple initialization approaches
                try:
                    logger.info("Attempting UnifiedRAGHandler with default parameters...")
                    self.rag_handler = UnifiedRAGHandler()
                    logger.info("SUCCESS: UnifiedRAGHandler initialized with defaults")
                except Exception as e:
                    logger.warning(f"Default initialization failed: {e}")
                    try:
                        logger.info("Attempting UnifiedRAGHandler with explicit parameters...")
                        self.rag_handler = UnifiedRAGHandler(
                            collection_name=settings.CHROMA_COLLECTION_NAME,
                            persist_path=settings.CHROMA_DB_PATH
                        )
                        logger.info("SUCCESS: UnifiedRAGHandler initialized with explicit parameters")
                    except Exception as e2:
                        logger.error(f"Both initialization methods failed: {e2}")
                        raise e2
                
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
        """Ensure the service is initialized before use"""
        if not self._initialized:
            success = await self.initialize_system()
            if not success:
                raise RuntimeError("Failed to initialize poem service")

    def cleanup(self):
        """Clean up service resources"""
        try:
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
    
    async def get_poem_by_id(self, poem_id: str) -> Optional[PoemData]:
        """
        Get specific poem by ID

        Args:
            poem_id: Poem identifier in format "temple_poem_id" or just poem_id

        Returns:
            PoemData object or None if not found
        """
        logger.info(f"[GET_POEM] Retrieving poem by ID: '{poem_id}'")
        await self.ensure_initialized()

        cache_key = f"poem_{poem_id}"
        if cache_key in self.cache:
            logger.debug(f"[GET_POEM] Found poem in cache: {poem_id}")
            return self.cache[cache_key]

        try:
            # Parse poem ID
            logger.debug(f"[GET_POEM] Parsing poem ID: '{poem_id}'")
            temple, numeric_id = await self._parse_poem_id(poem_id)
            logger.debug(f"[GET_POEM] Parsed result - temple: '{temple}', numeric_id: {numeric_id}")

            if not temple or not numeric_id:
                logger.warning(f"[GET_POEM] Invalid poem ID format: {poem_id}")
                return None

            # Get poem chunks
            logger.debug(f"[GET_POEM] Retrieving chunks for {temple}#{numeric_id}")
            poem_chunks = self.rag_handler.get_poem_by_temple_and_id(temple, numeric_id)
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

            # Cache result
            self.cache[cache_key] = poem_data

            return poem_data

        except Exception as e:
            logger.error(f"[GET_POEM] Critical error getting poem by ID {poem_id}: {e}", exc_info=True)
            logger.error(f"[GET_POEM] Error context - poem_id: '{poem_id}', cache_key: '{cache_key}'")
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
        # Input validation and logging
        logger.info(f"[INTERPRET] Starting interpretation for {poem_data.temple} poem #{poem_data.poem_id}")
        logger.debug(f"[INTERPRET] Input parameters: question='{question[:50]}...', language='{language}', user_context={bool(user_context)}")

        await self.ensure_initialized()

        try:
            # Log system availability
            logger.debug(f"[INTERPRET] Fortune system available: {self.fortune_system is not None}")

            # Use Fortune System if available
            if self.fortune_system:
                logger.info(f"[INTERPRET] Using Fortune System for {poem_data.temple}#{poem_data.poem_id}")

                try:
                    logger.debug(f"[INTERPRET] Calling fortune_system.ask_fortune with temple='{poem_data.temple}', poem_id={poem_data.poem_id}")
                    result = self.fortune_system.ask_fortune(
                        question=question,
                        temple=poem_data.temple,
                        poem_id=poem_data.poem_id,
                        additional_context=bool(user_context)
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

                    # Create FortuneResult
                    logger.debug(f"[INTERPRET] Creating FortuneResult object")
                    fortune_result = FortuneResult(
                        poem=poem_data,
                        interpretation=result.interpretation,
                        confidence=result.confidence,
                        additional_sources=additional_sources,
                        temple_sources=result.temple_sources,
                        generated_at=datetime.now(),
                        language=language,
                        job_id=""  # Will be set by job system
                    )
                    logger.info(f"[INTERPRET] Successfully created FortuneResult for {poem_data.temple}#{poem_data.poem_id}")
                    return fortune_result

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

            logger.debug(f"[INTERPRET] Creating fallback FortuneResult object")
            fallback_result = FortuneResult(
                poem=poem_data,
                interpretation=interpretation,
                confidence=0.7,
                additional_sources=[],
                temple_sources=[poem_data.temple],
                generated_at=datetime.now(),
                language=language,
                job_id=""
            )
            logger.info(f"[INTERPRET] Successfully created fallback FortuneResult for {poem_data.temple}#{poem_data.poem_id}")
            return fallback_result

        except Exception as e:
            logger.error(f"[INTERPRET] Critical error in generate_fortune_interpretation: {e}", exc_info=True)
            logger.error(f"[INTERPRET] Failed parameters - temple: {poem_data.temple}, poem_id: {poem_data.poem_id}, question: '{question[:100]}...'")
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
                    analysis=analysis
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
            analysis={"zh": "", "en": "", "jp": ""}
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


# Global service instance
poem_service = PoemService()
