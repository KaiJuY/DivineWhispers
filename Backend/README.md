# Fortune Poem RAG System with Integrated FAQ Pipeline

A comprehensive Retrieval-Augmented Generation (RAG) system for Chinese temple fortune poem interpretation with integrated FAQ management pipeline.

## 🌟 Features

### Core Functionality
- **Unified ChromaDB**: Stores both fortune poems and approved FAQ entries as searchable chunks
- **Temple-specific Retrieval**: Filter and retrieve poems by specific temple and poem ID
- **RAG-based Interpretation**: Contextual fortune interpretation with additional relevant content
- **FAQ Pipeline**: Automatic capture, approval workflow, and knowledge base integration
- **Multilingual Support**: Chinese, English, and Japanese language support
- **Clean API Interface**: Facade pattern for easy integration

### Design Patterns Implemented
- **Singleton Pattern** - `config.py` for global configuration management
- **Factory + Strategy Pattern** - `llm_client.py` for OpenAI/Ollama providers
- **Repository Pattern** - `unified_rag.py` for ChromaDB operations
- **Chain of Responsibility** - `faq_pipeline.py` for approval workflow
- **Template Method** - `interpreter.py` for interpretation flow
- **Facade Pattern** - `__init__.py` for clean API interface
- **Builder Pattern** - `data_ingestion.py` for ChromaDB population

### LLM Provider Support
- **OpenAI**: GPT models (GPT-3.5-turbo, GPT-4, etc.)
- **Ollama**: Local LLM deployment support
- **Mock Client**: For testing and development

## 📁 Project Structure

```
Backend/
├── fortune_module/                 # Main fortune system module
│   ├── __init__.py                # Facade pattern - main API interface
│   ├── models.py                  # Data structures using dataclasses
│   ├── config.py                  # Singleton pattern - global configuration
│   ├── unified_rag.py             # Repository pattern - ChromaDB operations
│   ├── llm_client.py              # Strategy + Factory - LLM providers
│   ├── faq_pipeline.py            # Chain of Responsibility - FAQ approval
│   ├── interpreter.py             # Template Method - interpretation flow
│   ├── data_ingestion.py          # Builder pattern - data ingestion
│   ├── test_system.py             # Comprehensive test suite
│   └── requirements.txt           # Python dependencies
├── demo_system.py                 # Demonstration script
└── README.md                      # This documentation
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
cd Backend/fortune_module

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file or set environment variables:

```bash
# For OpenAI support
export OPENAI_API_KEY="your_openai_api_key"

# For Ollama support (optional)
export OLLAMA_BASE_URL="http://localhost:11434"
```

### 3. Data Ingestion

First, ingest the fortune poem data from the crawler output:

```bash
# Setup system and ingest all temple data
python ../demo_system.py --setup

# Or ingest specific temple
python -m fortune_module.data_ingestion --temple GuanYin100

# Or programmatically
python -c "from fortune_module.data_ingestion import quick_ingest_all; quick_ingest_all()"
```

### 4. Basic Usage

```python
from fortune_module import FortuneSystem, LLMProvider

# Initialize system with OpenAI
system = FortuneSystem(
    llm_provider=LLMProvider.OPENAI,
    llm_config={"api_key": "your_openai_api_key", "model": "gpt-3.5-turbo"}
)

# Ask for fortune interpretation
result = system.ask_fortune(
    question="Will I find success in my career?",
    temple="GuanYin100",
    poem_id=42
)

print(result.interpretation)
print(f"Confidence: {result.confidence}")
print(f"Sources: {result.sources}")
```

## 📖 Detailed Usage

### Fortune Consultation Methods

#### Method 1: Direct Temple and Poem ID
```python
result = system.ask_fortune(
    question="What does my future hold?",
    temple="GuanYin100",
    poem_id=1,
    additional_context=True,  # Include related poems/FAQs
    capture_faq=True         # Capture for FAQ pipeline
)
```

#### Method 2: Using SelectedPoem Object
```python
poem = system.get_poem_by_temple("Mazu", 25)
result = system.ask_fortune_with_poem(
    question="Should I make this important decision?",
    selected_poem=poem
)
```

#### Method 3: Random Divination
```python
random_poem = system.random_poem(temple="Asakusa")  # Optional temple filter
result = system.ask_fortune_with_poem(
    question="What guidance do you have for me?",
    selected_poem=random_poem
)
```

### FAQ Management

#### Get Pending FAQs
```python
pending_faqs = system.get_pending_faqs()
for faq in pending_faqs:
    print(f"Q: {faq.question}")
    print(f"A: {faq.answer}")
    print(f"Category: {faq.category}")
```

#### Automatic Approval Processing
```python
# Process FAQ through approval chain
result = system.process_faq_approval(session_id)
if result['approval_status'] == 'auto_approved':
    system.approve_faq(session_id, approved_by="admin")
```

#### Manual FAQ Management
```python
# Approve with optional edits
system.approve_faq(
    session_id="abc123",
    approved_by="admin",
    edited_question="Will I find romantic love this year?",  # Optional
    edited_answer=None  # Keep original
)

# Reject FAQ
system.reject_faq(
    session_id="xyz789",
    rejected_by="admin",
    reason="Question too vague"
)
```

### System Administration

#### Health Check
```python
health = system.health_check()
print(f"Overall status: {health['overall']}")
for component, status in health.items():
    print(f"{component}: {status}")
```

#### System Statistics
```python
stats = system.get_system_stats()
print(f"Total poems: {stats['rag_collection']['poem_chunks']}")
print(f"Total FAQs: {stats['rag_collection']['faq_chunks']}")
```

#### Configuration Management
```python
# Update configuration
system.update_config(
    max_poems_per_query=5,
    auto_capture_faq=False
)

# Get current configuration
config = system.get_config()
print(f"Collection name: {config.collection_name}")
```

## 🔧 Advanced Usage

### Custom LLM Providers

```python
from fortune_module.llm_client import LLMClientFactory, BaseLLMClient

# Create custom LLM client
class CustomLLMClient(BaseLLMClient):
    def validate_config(self):
        return True
    
    def generate(self, prompt, **kwargs):
        # Your custom implementation
        return "Custom response"

# Register and use
LLMClientFactory.register_client(LLMProvider.OPENAI, CustomLLMClient)
```

### Custom Data Sources

```python
from fortune_module.data_ingestion import DataSourceHandler, DataIngestionManager

class CustomDataSource(DataSourceHandler):
    def validate_source(self):
        return True
    
    def get_temple_files(self, temple):
        # Your custom file discovery logic
        yield from []

manager = DataIngestionManager(rag_handler, data_source=CustomDataSource())
```

### Batch Processing

```python
# Process multiple questions
questions = [
    ("Will I find love?", "GuanYin100", 1),
    ("Is this job right for me?", "Mazu", 15),
    ("What about my health?", "Asakusa", 33)
]

results = []
for question, temple, poem_id in questions:
    result = system.ask_fortune(question, temple, poem_id)
    results.append(result)
```

## 🏛️ Available Temples

The system supports fortune poems from these temples:
- **GuanYin100**: 觀音一百籤 (100 poems)
- **GuanYu**: 關帝籤 (100 poems)  
- **Mazu**: 媽祖籤 (64 poems)
- **Asakusa**: 淺草寺籤 (100 poems)
- **ErawanShrine**: 四面佛籤 (30 poems)
- **Tianhou**: 天后籤 (varies)

Each poem contains:
- **Poem Text**: Traditional Chinese poetry
- **Analysis**: Interpretations in Chinese, English, and Japanese
- **Fortune Level**: Classification (上籤, 中籤, 下籤, etc.)
- **Metadata**: Temple-specific information

## 🧪 Testing

### Run Test Suite
```bash
# All tests
python -m fortune_module.test_system

# Unit tests only
python -m fortune_module.test_system --unit

# Integration tests
python -m fortune_module.test_system --integration

# With verbose output
python -m fortune_module.test_system --verbose
```

### Interactive Demo
```bash
# Setup system
python demo_system.py --setup

# Run demonstrations
python demo_system.py --demo

# Interactive mode
python demo_system.py --interactive

# Test LLM connectivity
python demo_system.py --test-llm
```

## 🔍 Data Flow Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   JSON Data     │───▶│  Data Ingestion  │───▶│   ChromaDB      │
│  (SourceCrawler)│    │  (Builder Pattern) │    │  (Repository)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌──────────────────┐    ┌─────────┴─────────┐
│    User Query   │───▶│   Interpreter    │◄───│   RAG Retrieval   │
│                 │    │ (Template Method)│    │                   │
└─────────────────┘    └─────────┬────────┘    └───────────────────┘
                                 │
┌─────────────────┐    ┌─────────▼────────┐    ┌─────────────────┐
│  LLM Response   │◄───│   LLM Client     │    │  FAQ Pipeline   │
│                 │    │ (Strategy/Factory)│    │ (Chain of Resp.)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📊 Performance Considerations

- **ChromaDB**: Optimized for similarity search with cosine distance
- **Embedding Model**: Multilingual sentence-transformers model
- **Caching**: ChromaDB handles internal caching
- **Batch Processing**: Efficient bulk operations for data ingestion
- **Memory Usage**: Configurable chunk sizes and query limits

## 🔐 Security Features

- **Input Validation**: All user inputs validated
- **SQL Injection Protection**: Parameterized queries
- **API Key Management**: Secure credential handling
- **Content Filtering**: FAQ approval workflow prevents inappropriate content
- **Error Handling**: Comprehensive exception handling

## 🐛 Troubleshooting

### Common Issues

1. **ChromaDB Connection Error**
   ```bash
   # Clear ChromaDB data
   rm -rf ./chroma_db
   # Re-run data ingestion
   python demo_system.py --setup
   ```

2. **OpenAI API Error**
   ```bash
   # Check API key
   echo $OPENAI_API_KEY
   # Test connectivity
   python demo_system.py --test-llm
   ```

3. **Missing Fortune Data**
   ```bash
   # Ensure SourceCrawler has run
   ls ../SourceCrawler/outputs/
   # Re-ingest data
   python -c "from fortune_module.data_ingestion import quick_ingest_all; quick_ingest_all(clear_existing=True)"
   ```

4. **Ollama Connection Issues**
   ```bash
   # Start Ollama server
   ollama serve
   # Pull required model
   ollama pull llama2
   ```

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use verbose demo
python demo_system.py --demo --verbose
```

## 📈 Future Enhancements

- [ ] Web API interface with FastAPI
- [ ] Multi-user session management  
- [ ] Advanced analytics and reporting
- [ ] Additional LLM provider support
- [ ] Real-time FAQ approval dashboard
- [ ] Mobile-responsive frontend
- [ ] Multi-language UI support
- [ ] Advanced search and filtering
- [ ] Export/import functionality
- [ ] Performance monitoring dashboard

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is part of the DivineWhispers fortune-telling system. See the main project license for details.

## 🙏 Acknowledgments

- Chinese temple fortune poem traditions
- ChromaDB for vector database capabilities
- OpenAI and Ollama for LLM support
- sentence-transformers for multilingual embeddings
- All contributors to the project

---

**Divine Whispers Team**  
*Bridging ancient wisdom with modern technology*