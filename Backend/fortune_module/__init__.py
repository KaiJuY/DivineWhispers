# __init__.py - Facade Pattern Implementation
"""
Fortune Poem RAG System with Integrated FAQ Pipeline

This module provides a unified interface for fortune poem interpretation using RAG
(Retrieval-Augmented Generation) with integrated FAQ pipeline for knowledge base expansion.

Main Features:
- Unified ChromaDB storing both fortune poems and approved FAQ entries
- Temple-specific poem retrieval and interpretation
- FAQ capture, approval workflow, and integration
- Support for OpenAI and Ollama LLM providers
- Multilingual support (Chinese, English, Japanese)
- Clean Facade API for easy integration

Example Usage:
    from fortune_module import FortuneSystem, LLMProvider
    
    # Initialize the system
    system = FortuneSystem(
        llm_provider=LLMProvider.OPENAI,
        llm_config={"api_key": "your-api-key", "model": "gpt-4"}
    )
    
    # Ask for fortune interpretation
    result = system.ask_fortune("Will I find love this year?", temple="GuanYin", poem_id=42)
    print(result.interpretation)
"""

from .unified_rag import UnifiedRAGHandler
from .llm_client import LLMClientFactory, BaseLLMClient, create_llm_client
from .interpreter import PoemInterpreter, InterpreterFactory
from .faq_pipeline import FAQPipeline
from .config import SystemConfig
from .models import *
from typing import List, Optional, Dict, Any, Callable
import logging
import os

# Configure logging
def _setup_logging():
    """Set up logging for the fortune module."""
    config = SystemConfig()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Set up file handler if specified
    handlers = [console_handler]
    if config.log_file:
        try:
            file_handler = logging.FileHandler(config.log_file)
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        except Exception:
            pass  # Skip file logging if it fails
    
    # Configure root logger for the module
    logger = logging.getLogger('fortune_module')
    logger.setLevel(getattr(logging, config.log_level.upper(), logging.INFO))
    
    # Remove existing handlers and add new ones
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    for handler in handlers:
        logger.addHandler(handler)

# Initialize logging when module is imported
_setup_logging()

class FortuneSystem:
    """
    Facade pattern implementation providing a unified interface to the Fortune System.
    
    This class acts as a simplified interface to the complex subsystems including
    RAG handler, LLM clients, interpreters, and FAQ pipeline.
    """
    
    def __init__(self, llm_provider: LLMProvider, llm_config: dict, 
                 config_overrides: dict = None):
        """
        Initialize the Fortune System.
        
        Args:
            llm_provider: The LLM provider to use (OPENAI or OLLAMA)
            llm_config: Configuration dictionary for the LLM provider
            config_overrides: Optional configuration overrides
        """
        self.logger = logging.getLogger(__name__)
        
        try:
            # Initialize configuration
            self.config = SystemConfig()
            if config_overrides:
                self.config.update_config(**config_overrides)
            
            # Initialize core components
            self.rag = UnifiedRAGHandler()
            self.llm = LLMClientFactory.create_client(llm_provider, **llm_config)
            self.faq_pipeline = FAQPipeline(rag_handler=self.rag)
            self.interpreter = InterpreterFactory.create_poem_interpreter(
                self.rag, self.llm, self.faq_pipeline
            )
            
            self.logger.info(f"Fortune System initialized with {llm_provider.value} provider")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Fortune System: {e}")
            raise
    
    # Main Fortune Consultation Interface
    def ask_fortune(self, question: str, temple: str, poem_id: int, 
                   additional_context: bool = True, capture_faq: bool = None) -> InterpretationResult:
        """
        Main interface for fortune consultation with specific poem.
        
        Args:
            question: User's question for fortune interpretation
            temple: Temple name (e.g., "GuanYin", "Mazu")
            poem_id: Specific poem ID number
            additional_context: Whether to include additional RAG context
            capture_faq: Whether to capture this interaction for FAQ (uses config default if None)
            
        Returns:
            InterpretationResult containing interpretation and metadata
        """
        try:
            context_k = self.config.max_poems_per_query if additional_context else 0
            capture = capture_faq if capture_faq is not None else self.config.auto_capture_faq
            
            result = self.interpreter.interpret(
                question=question,
                temple=temple,
                poem_id=poem_id,
                additional_context_k=context_k,
                capture_faq=capture
            )
            
            self.logger.info(f"Fortune consultation completed for {temple} poem #{poem_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Fortune consultation failed: {e}")
            raise
    
    def ask_fortune_streaming(self, question: str, temple: str, poem_id: int,
                             streaming_callback: Optional[Callable[[str], None]] = None,
                             additional_context: bool = True, capture_faq: bool = None) -> InterpretationResult:
        """
        Fortune consultation with LLM streaming support for better UX.

        Args:
            question: User's question for fortune interpretation
            temple: Temple name (e.g., "GuanYin", "Mazu")
            poem_id: Specific poem ID number
            streaming_callback: Optional callback function for LLM token streaming
            additional_context: Whether to include additional RAG context
            capture_faq: Whether to capture this interaction for FAQ (uses config default if None)

        Returns:
            InterpretationResult containing interpretation and metadata
        """
        try:
            context_k = self.config.max_poems_per_query if additional_context else 0
            capture = capture_faq if capture_faq is not None else self.config.auto_capture_faq

            result = self.interpreter.interpret_with_streaming(
                question=question,
                temple=temple,
                poem_id=poem_id,
                streaming_callback=streaming_callback,
                additional_context_k=context_k,
                capture_faq=capture
            )

            self.logger.info(f"Streaming fortune consultation completed for {temple} poem #{poem_id}")
            return result

        except Exception as e:
            self.logger.error(f"Streaming fortune consultation failed: {e}")
            raise

    def ask_fortune_with_poem(self, question: str, selected_poem: SelectedPoem,
                            additional_context: bool = True, capture_faq: bool = None) -> InterpretationResult:
        """
        Alternative interface using SelectedPoem object.

        Args:
            question: User's question for fortune interpretation
            selected_poem: SelectedPoem object with temple and poem_id
            additional_context: Whether to include additional RAG context
            capture_faq: Whether to capture this interaction for FAQ

        Returns:
            InterpretationResult containing interpretation and metadata
        """
        return self.ask_fortune(
            question=question,
            temple=selected_poem.temple,
            poem_id=selected_poem.poem_id,
            additional_context=additional_context,
            capture_faq=capture_faq
        )
    
    # Poem Management Interface
    def get_poem_by_temple(self, temple: str, poem_id: int) -> SelectedPoem:
        """
        Get specific poem by temple and ID.
        
        Args:
            temple: Temple name
            poem_id: Poem ID number
            
        Returns:
            SelectedPoem object
            
        Raises:
            ValueError: If poem not found
        """
        try:
            chunks = self.rag.get_poem_by_temple_and_id(temple, poem_id)
            if not chunks:
                raise ValueError(f"Poem not found: {temple} poem #{poem_id}")
            
            return SelectedPoem(temple=temple, poem_id=poem_id, chunks=chunks)
            
        except Exception as e:
            self.logger.error(f"Failed to get poem {temple}#{poem_id}: {e}")
            raise
    
    def list_available_poems(self, temple: Optional[str] = None) -> List[Dict]:
        """
        List available poems, optionally filtered by temple.
        
        Args:
            temple: Optional temple filter
            
        Returns:
            List of poem dictionaries with basic metadata
        """
        try:
            return self.rag.list_available_poems(temple)
        except Exception as e:
            self.logger.error(f"Failed to list poems: {e}")
            return []
    
    def random_poem(self, temple: Optional[str] = None) -> SelectedPoem:
        """
        Get a random poem for divination.
        
        Args:
            temple: Optional temple filter
            
        Returns:
            Random SelectedPoem object
        """
        import random
        
        try:
            # Get available poems
            poems = self.list_available_poems(temple)
            if not poems:
                # Fallback to default if no poems available
                default_temple = temple or "GuanYin100"
                default_id = random.randint(1, 100)
                self.logger.warning(f"No poems found, using fallback: {default_temple}#{default_id}")
                return SelectedPoem(temple=default_temple, poem_id=default_id, chunks=[])
            
            # Select random poem
            random_poem_info = random.choice(poems)
            return self.get_poem_by_temple(random_poem_info["temple"], random_poem_info["poem_id"])
            
        except Exception as e:
            self.logger.error(f"Failed to get random poem: {e}")
            raise
    
    # FAQ Management Interface
    def get_pending_faqs(self, status: str = "pending") -> List[PendingFAQ]:
        """
        Get pending FAQ entries for approval.
        
        Args:
            status: FAQ status filter (default: "pending")
            
        Returns:
            List of PendingFAQ objects
        """
        try:
            return self.faq_pipeline.get_pending_faqs(status)
        except Exception as e:
            self.logger.error(f"Failed to get pending FAQs: {e}")
            return []
    
    def approve_faq(self, session_id: str, approved_by: str, 
                   edited_question: Optional[str] = None, 
                   edited_answer: Optional[str] = None) -> bool:
        """
        Approve and add FAQ to knowledge base.
        
        Args:
            session_id: Session ID of the FAQ to approve
            approved_by: Name/ID of the approver
            edited_question: Optional edited question text
            edited_answer: Optional edited answer text
            
        Returns:
            True if approval successful, False otherwise
        """
        try:
            return self.faq_pipeline.approve_faq(
                session_id=session_id,
                approved_by=approved_by,
                edited_question=edited_question,
                edited_answer=edited_answer
            )
        except Exception as e:
            self.logger.error(f"FAQ approval failed: {e}")
            return False
    
    def reject_faq(self, session_id: str, rejected_by: str = None, reason: str = None) -> bool:
        """
        Reject pending FAQ.
        
        Args:
            session_id: Session ID of the FAQ to reject
            rejected_by: Name/ID of the rejector
            reason: Reason for rejection
            
        Returns:
            True if rejection successful, False otherwise
        """
        try:
            return self.faq_pipeline.reject_faq(session_id, rejected_by, reason)
        except Exception as e:
            self.logger.error(f"FAQ rejection failed: {e}")
            return False
    
    def process_faq_approval(self, session_id: str) -> Dict[str, Any]:
        """
        Process FAQ through automatic approval chain.
        
        Args:
            session_id: Session ID of the FAQ to process
            
        Returns:
            Dictionary with processing results
        """
        try:
            return self.faq_pipeline.process_faq_approval(session_id)
        except Exception as e:
            self.logger.error(f"FAQ processing failed: {e}")
            return {"error": str(e)}
    
    # System Management Interface
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive system statistics.
        
        Returns:
            Dictionary with system statistics
        """
        try:
            rag_stats = self.rag.get_collection_stats()
            faq_stats = self.faq_pipeline.get_faq_stats()
            
            return {
                "rag_collection": rag_stats,
                "faq_pipeline": faq_stats,
                "configuration": {
                    "llm_provider": self.config.default_llm_provider,
                    "collection_name": self.config.collection_name,
                    "auto_capture_faq": self.config.auto_capture_faq
                }
            }
        except Exception as e:
            self.logger.error(f"Failed to get system stats: {e}")
            return {"error": str(e)}
    
    def health_check(self) -> Dict[str, str]:
        """
        Perform system health check.
        
        Returns:
            Dictionary with component health status
        """
        health = {}
        
        try:
            # Check RAG system
            test_query = self.rag.query("test", top_k=1)
            health["rag"] = "healthy" if test_query else "error"
        except Exception:
            health["rag"] = "error"
        
        try:
            # Check LLM client
            test_response = self.llm.generate("test", max_tokens=10)
            health["llm"] = "healthy" if test_response else "error"
        except Exception:
            health["llm"] = "error"
        
        try:
            # Check FAQ pipeline
            stats = self.faq_pipeline.get_faq_stats()
            health["faq_pipeline"] = "healthy" if stats else "error"
        except Exception:
            health["faq_pipeline"] = "error"
        
        health["overall"] = "healthy" if all(status == "healthy" for status in health.values()) else "degraded"
        
        return health
    
    # Configuration Management
    def update_config(self, **kwargs):
        """
        Update system configuration.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        try:
            self.config.update_config(**kwargs)
            self.logger.info("System configuration updated")
        except Exception as e:
            self.logger.error(f"Failed to update configuration: {e}")
            raise
    
    def get_config(self) -> SystemConfig:
        """
        Get current system configuration.
        
        Returns:
            SystemConfig instance
        """
        return self.config

# Convenience factory functions
def create_fortune_system(llm_provider: str, **llm_config) -> FortuneSystem:
    """
    Convenience function to create a FortuneSystem instance.
    
    Args:
        llm_provider: LLM provider name ("openai" or "ollama")
        **llm_config: LLM configuration parameters
        
    Returns:
        FortuneSystem instance
    """
    try:
        provider = LLMProvider(llm_provider.lower())
        return FortuneSystem(provider, llm_config)
    except ValueError as e:
        available = [p.value for p in LLMProvider]
        raise ValueError(f"Invalid provider '{llm_provider}'. Available: {available}") from e

def create_openai_system(api_key: str, model: str = "gpt-3.5-turbo", **kwargs) -> FortuneSystem:
    """
    Convenience function to create FortuneSystem with OpenAI.
    
    Args:
        api_key: OpenAI API key
        model: OpenAI model name
        **kwargs: Additional configuration
        
    Returns:
        FortuneSystem instance
    """
    llm_config = {"api_key": api_key, "model": model}
    llm_config.update(kwargs)
    return FortuneSystem(LLMProvider.OPENAI, llm_config)

def create_ollama_system(model: str = "llama2", base_url: str = "http://localhost:11434", **kwargs) -> FortuneSystem:
    """
    Convenience function to create FortuneSystem with Ollama.
    
    Args:
        model: Ollama model name
        base_url: Ollama server URL
        **kwargs: Additional configuration
        
    Returns:
        FortuneSystem instance
    """
    llm_config = {"model": model, "base_url": base_url}
    llm_config.update(kwargs)
    return FortuneSystem(LLMProvider.OLLAMA, llm_config)

# Export all public APIs
__all__ = [
    # Main classes
    'FortuneSystem',
    'SystemConfig',
    
    # Data models
    'LLMProvider', 'ChunkType', 'PoemChunk', 'FAQChunk', 'PendingFAQ',
    'RAGResult', 'SelectedPoem', 'InterpretationResult',
    
    # Core components (for advanced usage)
    'UnifiedRAGHandler', 'BaseLLMClient', 'LLMClientFactory', 
    'PoemInterpreter', 'FAQPipeline',
    
    # Convenience functions
    'create_fortune_system', 'create_openai_system', 'create_ollama_system',
    'create_llm_client'
]

# Version information
__version__ = "1.0.0"
__author__ = "DivineWhispers Team"
__description__ = "Fortune Poem RAG System with Integrated FAQ Pipeline"