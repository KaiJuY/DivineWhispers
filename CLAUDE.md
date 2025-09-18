# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

DivineWhispers is a fortune-telling/divination system that crawls Chinese temple fortune poems (籤詩) from various temples and provides a vector-based retrieval system using ChromaDB.

### Core Components

1. **SourceCrawler/** - Web scraping system for temple fortune poems
   - `ITempleCrawler.py` - Abstract base class defining crawler interface
   - `CrawlerFactory.py` - Factory pattern for creating specific crawlers
   - Individual crawler implementations for different temples:
     - `GuanYuCrawler.py`, `MazuCrawler.py`, `YueLaoCrawler.py`
     - `GuanYin100Crawler.py`, `TianhouCrawler.py`, `AsakusaCrawler.py`
     - `ErawanShrineCrawler.py`, `ZhushengCrawler.py`
   - `main.py` - Entry point that runs all crawlers via factory pattern
   - Temple-specific data folders containing scraped JSON files (100 per temple)

2. **Backend/** - Vector database and retrieval system
   - `PoemChromaSystem.py` - ChromaDB-based fortune poem retrieval system
   - Uses sentence-transformers for multilingual embeddings
   - Provides LLM-ready context and prompts for fortune interpretation

### Data Structure

Each fortune poem JSON contains:
- `id` - Unique identifier
- `title` - Full title of the fortune
- `fortune` - Fortune category (大吉, 中吉, etc.)
- `poem` - The actual poem text
- `analysis` - Detailed interpretation in multiple languages (zh, en, jp)

### Common Development Commands

Since this is a Python project without package.json, common commands would be:

```bash
# Run the main crawler system
cd SourceCrawler
python main.py

# Run the ChromaDB retrieval system
cd Backend
python PoemChromaSystem.py

# Install dependencies (likely needed)
pip install chromadb sentence-transformers beautifulsoup4 urllib3
```

### Data Flow

1. Crawlers scrape fortune poems from temple websites
2. Data is stored in JSON format in temple-specific folders
3. ChromaDB system ingests JSON files and creates vector embeddings
4. Users can query the system for relevant fortune interpretations
5. System returns contextual LLM prompts for fortune telling responses

### Working with the Code

- All crawlers inherit from `TempleCrawler` abstract base class
- Factory pattern is used to instantiate specific crawlers
- ChromaDB system handles both data ingestion and similarity search
- The system is designed for multilingual support (Chinese, English, Japanese)
- Output files are organized by temple name in separate directories
- Focus on current job don't summary previous request again.