# llm_client.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Iterator, Callable
from .models import LLMProvider
from .config import SystemConfig
import logging
import json

# Strategy Pattern - Base class for LLM clients
class BaseLLMClient(ABC):
    """Abstract base class for LLM clients using Strategy pattern."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from LLM."""
        pass

    def generate_stream(self, prompt: str, callback: Optional[Callable[[str], None]] = None, **kwargs) -> str:
        """
        Generate response with streaming support (optional).
        Default implementation falls back to non-streaming.

        Args:
            prompt: The input prompt
            callback: Optional callback function called with each token/chunk
            **kwargs: Additional generation parameters

        Returns:
            Complete generated text
        """
        # Default: fallback to non-streaming
        result = self.generate(prompt, **kwargs)
        if callback:
            callback(result)  # Send entire result at once
        return result

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate the configuration for this client."""
        pass

class OpenAIClient(BaseLLMClient):
    """OpenAI client implementation using Strategy pattern."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.model = config.get("model", "gpt-3.5-turbo")
        self.base_url = config.get("base_url")
        
        if not self.validate_config():
            raise ValueError("Invalid OpenAI configuration")
        
        # Initialize OpenAI client
        try:
            import openai
            client_params = {"api_key": self.api_key}
            if self.base_url:
                client_params["base_url"] = self.base_url
            self.client = openai.OpenAI(**client_params)
            self.logger.info(f"OpenAI client initialized with model: {self.model}")
        except ImportError:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    def validate_config(self) -> bool:
        """Validate OpenAI configuration."""
        if not self.api_key:
            self.logger.error("OpenAI API key is required")
            return False
        return True
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using OpenAI API."""
        try:
            # Set default parameters
            params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 1000)
            }

            # Add any additional kwargs
            for key, value in kwargs.items():
                if key not in ["temperature", "max_tokens"] and value is not None:
                    params[key] = value

            response = self.client.chat.completions.create(**params)
            generated_text = response.choices[0].message.content

            self.logger.debug(f"Generated response length: {len(generated_text)}")
            return generated_text

        except Exception as e:
            self.logger.error(f"OpenAI generation failed: {e}")
            raise

    def generate_stream(self, prompt: str, callback: Optional[Callable[[str], None]] = None, **kwargs) -> str:
        """Generate response with streaming using OpenAI API."""
        try:
            # Set default parameters
            params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 1000),
                "stream": True  # Enable streaming
            }

            # Add any additional kwargs
            for key, value in kwargs.items():
                if key not in ["temperature", "max_tokens", "stream"] and value is not None:
                    params[key] = value

            response_stream = self.client.chat.completions.create(**params)

            full_response = ""
            for chunk in response_stream:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_response += token
                    if callback:
                        callback(token)

            self.logger.debug(f"Streamed response length: {len(full_response)}")
            return full_response

        except Exception as e:
            self.logger.error(f"OpenAI streaming failed: {e}")
            raise

class OllamaClient(BaseLLMClient):
    """Ollama client implementation using Strategy pattern."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.model = config.get("model", "llama2")
        
        if not self.validate_config():
            raise ValueError("Invalid Ollama configuration")
        
        # Test connection
        try:
            import requests
            self.requests = requests
            # Test if Ollama server is accessible
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self.logger.info(f"Ollama client initialized with model: {self.model}")
            else:
                raise ConnectionError(f"Ollama server not accessible at {self.base_url}")
        except ImportError:
            raise ImportError("Requests library not installed. Run: pip install requests")
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Could not connect to Ollama server: {e}")
            # Don't fail initialization, allow runtime connection attempts
    
    def validate_config(self) -> bool:
        """Validate Ollama configuration."""
        if not self.base_url or not self.model:
            self.logger.error("Ollama base_url and model are required")
            return False
        return True
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using Ollama API."""
        try:
            # Prepare request payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "num_predict": kwargs.get("max_tokens", 1000)
                }
            }

            # Add any additional options
            for key, value in kwargs.items():
                if key not in ["temperature", "max_tokens"] and value is not None:
                    payload["options"][key] = value

            response = self.requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=180  # 3 minute timeout for generation
            )
            response.raise_for_status()

            response_data = response.json()
            generated_text = response_data.get("response", "")

            self.logger.debug(f"Generated response length: {len(generated_text)}")
            return generated_text

        except self.requests.exceptions.RequestException as e:
            self.logger.error(f"Ollama request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Ollama response: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Ollama generation failed: {e}")
            raise

    def generate_stream(self, prompt: str, callback: Optional[Callable[[str], None]] = None, **kwargs) -> str:
        """Generate response with streaming using Ollama API."""
        try:
            # Prepare request payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": True,  # Enable streaming
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "num_predict": kwargs.get("max_tokens", 1000)
                }
            }

            # Add any additional options
            for key, value in kwargs.items():
                if key not in ["temperature", "max_tokens", "stream"] and value is not None:
                    payload["options"][key] = value

            response = self.requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=True,  # Enable streaming in requests
                timeout=180
            )
            response.raise_for_status()

            full_response = ""
            # Process streaming response line by line
            for line in response.iter_lines():
                if line:
                    try:
                        chunk_data = json.loads(line)
                        token = chunk_data.get("response", "")
                        if token:
                            full_response += token
                            if callback:
                                callback(token)

                        # Check if generation is complete
                        if chunk_data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        # Skip malformed lines
                        continue

            self.logger.debug(f"Streamed response length: {len(full_response)}")
            return full_response

        except self.requests.exceptions.RequestException as e:
            self.logger.error(f"Ollama streaming failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Ollama streaming failed: {e}")
            raise

class MockLLMClient(BaseLLMClient):
    """Mock LLM client for testing purposes."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.mock_response = config.get("mock_response", "This is a mock response for testing.")
    
    def validate_config(self) -> bool:
        """Mock client always has valid config."""
        return True
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate mock response."""
        self.logger.debug(f"Mock generation for prompt length: {len(prompt)}")
        return f"{self.mock_response}\n\nPrompt was: {prompt[:100]}..."

# Factory Pattern - Create LLM clients
class LLMClientFactory:
    """Factory for creating LLM clients using Factory pattern."""
    
    _client_registry = {
        LLMProvider.OPENAI: OpenAIClient,
        LLMProvider.OLLAMA: OllamaClient,
    }
    
    @classmethod
    def register_client(cls, provider: LLMProvider, client_class: type):
        """Register a new LLM client type."""
        cls._client_registry[provider] = client_class
    
    @classmethod
    def create_client(cls, provider: LLMProvider, **config) -> BaseLLMClient:
        """Create an LLM client based on provider type."""
        if provider not in cls._client_registry:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        client_class = cls._client_registry[provider]
        
        try:
            return client_class(config)
        except Exception as e:
            logging.getLogger(cls.__name__).error(f"Failed to create {provider.value} client: {e}")
            raise
    
    @classmethod
    def create_from_config(cls, system_config: SystemConfig, provider: Optional[LLMProvider] = None) -> BaseLLMClient:
        """Create client using SystemConfig."""
        if not provider:
            provider = LLMProvider(system_config.default_llm_provider)
        
        config = system_config.get_llm_config(provider.value)
        return cls.create_client(provider, **config)
    
    @classmethod
    def create_mock_client(cls, mock_response: str = None) -> BaseLLMClient:
        """Create a mock client for testing."""
        config = {"mock_response": mock_response} if mock_response else {}
        return MockLLMClient(config)
    
    @classmethod
    def list_available_providers(cls) -> list:
        """List all registered LLM providers."""
        return list(cls._client_registry.keys())

# Utility function for easy client creation
def create_llm_client(provider: str, **config) -> BaseLLMClient:
    """Utility function to create LLM client from string provider name."""
    try:
        provider_enum = LLMProvider(provider.lower())
        return LLMClientFactory.create_client(provider_enum, **config)
    except ValueError as e:
        available = [p.value for p in LLMClientFactory.list_available_providers()]
        raise ValueError(f"Invalid provider '{provider}'. Available: {available}") from e