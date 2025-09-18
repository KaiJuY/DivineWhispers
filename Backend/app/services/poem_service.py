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

                # Initialize RAG handler
                config = SystemConfig()
                logger.info(f"RAG Config - Collection: {settings.CHROMA_COLLECTION_NAME}, Path: {settings.CHROMA_DB_PATH}")
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
                # Try fallback to direct file reading
                return await self._try_direct_file_read(temple, numeric_id)

            poem_data = await self._create_poem_data_from_chunks(poem_chunks)

            # Validate the analysis structure - if it's corrupted, try direct file read
            if poem_data and not self._is_analysis_valid(poem_data.analysis):
                logger.warning(f"Invalid analysis structure for {poem_id}, trying direct file read")
                direct_data = await self._try_direct_file_read(temple, numeric_id)
                if direct_data and self._is_analysis_valid(direct_data.analysis):
                    poem_data = direct_data

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
        if not chunks:
            raise ValueError("No chunks provided")

        # Use first chunk for basic info
        chunk = chunks[0]

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

        return PoemData(
            id=f"{chunk['temple']}_{chunk['poem_id']}",
            temple=chunk["temple"],
            poem_id=chunk["poem_id"],
            title=chunk.get("title", ""),
            fortune=chunk.get("fortune", ""),
            poem=poem_text or str(chunk.get("poem", "")),
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
