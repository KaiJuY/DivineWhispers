# config.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import threading

class SingletonMeta(type):
    """Singleton metaclass for thread-safe singleton implementation."""
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
            return cls._instances[cls]

@dataclass
class SystemConfig(metaclass=SingletonMeta):
    """Global configuration for the Fortune System using Singleton pattern."""
    
    # ChromaDB settings
    chroma_persist_path: str = "./chroma_db"
    collection_name: str = "fortune_knowledge"
    
    # LLM settings
    default_llm_provider: str = "openai"
    openai_config: Dict[str, Any] = field(default_factory=lambda: {"model": "gpt-3.5-turbo"})
    ollama_config: Dict[str, Any] = field(default_factory=lambda: {
        "base_url": "http://localhost:11434", 
        "model": "llama2"
    })
    
    # RAG settings
    default_top_k: int = 5
    max_poems_per_query: int = 3
    max_faqs_per_query: int = 2
    
    # FAQ Pipeline settings
    pending_faq_db_path: str = "pending_faq.db"
    auto_capture_faq: bool = True
    
    # Data ingestion settings
    source_data_path: str = "../SourceCrawler/outputs/"
    temple_names: list = field(default_factory=lambda: [
        "GuanYin100", "GuanYu", "Mazu", "Asakusa", "ErawanShrine", "Tianhou"
    ])
    
    # Embedding settings
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = "fortune_system.log"
    
    def update_config(self, **kwargs):
        """Update configuration values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Invalid configuration key: {key}")
    
    def get_llm_config(self, provider: str = None) -> Dict[str, Any]:
        """Get LLM configuration for the specified provider."""
        provider = provider or self.default_llm_provider
        if provider == "openai":
            return self.openai_config
        elif provider == "ollama":
            return self.ollama_config
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
    
    def get_temple_data_path(self, temple_name: str) -> str:
        """Get the full path to a temple's data directory."""
        return f"{self.source_data_path}/{temple_name}"
    
    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (mainly for testing)."""
        with cls._lock:
            if cls in cls._instances:
                del cls._instances[cls]