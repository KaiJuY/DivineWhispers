# ChromaDB Data Synchronization Guide

This guide explains how to synchronize your fortune poem data from JSON files to ChromaDB for the DivineWhispers project.

## Overview

The DivineWhispers system uses ChromaDB as a vector database to store and retrieve fortune poem data. When you update JSON files in the `SourceCrawler` directory, you need to sync this data to ChromaDB for the backend API to serve the latest content.

## Data Flow

```
JSON Files (SourceCrawler/) → Data Ingestion → ChromaDB → Backend API → Frontend
```

## Quick Sync Commands

### 1. Sync All Temples (Recommended)
```bash
cd Backend
python -c "
from fortune_module.data_ingestion import quick_ingest_all
result = quick_ingest_all(clear_existing=True)
print(f'Synced all temples: {result}')
"
```

### 2. Sync Specific Temple
```bash
cd Backend
python -c "
from fortune_module.data_ingestion import quick_ingest_temple
result = quick_ingest_temple('YueLao', clear_existing=True)
print(f'Synced YueLao: {result}')
"
```

### 3. Using Command Line Interface
```bash
cd Backend
python -m fortune_module.data_ingestion --all --clear --verbose
```

## Detailed Sync Process

### Step 1: Navigate to Backend Directory
```bash
cd "C:\Users\KaiJu\Desktop\WorkSpace\My_Self\DivineWhispers\Backend"
```

### Step 2: Run Data Ingestion

#### Option A: Interactive Python Script
```python
import sys
import codecs
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

from fortune_module.unified_rag import UnifiedRAGHandler
from fortune_module.data_ingestion import DataIngestionManager

# Create RAG handler
rag = UnifiedRAGHandler()

# Clear existing data (recommended for fresh sync)
print("Clearing existing ChromaDB data...")
rag.clear_collection()

# Create ingestion manager
manager = DataIngestionManager(rag)

# Ingest all temples
print("Starting data ingestion...")
result = manager.ingest_all_temples()

print(f"Ingestion completed:")
print(f"- Total files processed: {result['total_files_processed']}")
print(f"- Total chunks created: {result['total_chunks_created']}")
print(f"- Total chunks ingested: {result['total_chunks_ingested']}")

if result['errors']:
    print(f"Errors encountered: {len(result['errors'])}")
    for error in result['errors'][:5]:  # Show first 5 errors
        print(f"  - {error}")
```

#### Option B: Command Line
```bash
# Sync all temples with verbose output
python -m fortune_module.data_ingestion --all --clear --verbose

# Sync specific temple
python -m fortune_module.data_ingestion --temple YueLao --clear --verbose

# Validate after sync
python -m fortune_module.data_ingestion --validate
```

### Step 3: Verify Sync Success

#### Check Collection Statistics
```python
from fortune_module.unified_rag import UnifiedRAGHandler

rag = UnifiedRAGHandler()
stats = rag.get_collection_stats()
print(f"ChromaDB Stats: {stats}")
```

#### Test Specific Poem Retrieval
```python
# Test a specific poem
chunks = rag.get_poem_by_temple_and_id('YueLao', 50)
print(f"Found {len(chunks)} chunks for YueLao_50")

for i, chunk in enumerate(chunks):
    content = chunk.get('content', '')[:100]
    print(f"Chunk {i+1}: {content}...")
```

#### Test API Endpoint
```bash
curl "http://localhost:8000/api/v1/fortune/fortunes/yue_lao/50" | python -m json.tool
```

## Temple Configuration

### Supported Temples
The system supports these temples by default:
- `GuanYu` - 關公廟
- `YueLao` - 月老廟
- `Asakusa` - 淺草寺
- `GuanYin100` - 觀音100籤
- `Tianhou` - 天后宮
- `Mazu` - 媽祖廟
- `ErawanShrine` - 四面佛

### Data Source Paths
The ingestion system looks for JSON files in these locations:
```
SourceCrawler/
├── outputs/
│   ├── YueLao/
│   │   ├── chuck_1.json
│   │   ├── chuck_2.json
│   │   └── ...
│   ├── Mazu/
│   └── ...
└── [temple_name]/
    ├── chuck_*.json
    └── poem_*.json
```

## Expected JSON Format

Each JSON file should follow this structure:
```json
{
  "id": 50,
  "title": "月老聖籤一百籤第五十籤",
  "subtitle": "",
  "fortune": "上平",
  "poem": "雛有善者，亦無如之何矣。",
  "analysis": {
    "zh": "Chinese analysis text...",
    "en": "English analysis text...",
    "jp": "Japanese analysis text...",
    "reference": "Reference information..."
  },
  "rag_analysis": "Additional RAG analysis...",
  "_llm_meta": {
    "model": "gpt-oss:20b",
    "timestamp": "2025-09-15 14:09:07"
  }
}
```

## Troubleshooting

### Common Issues

#### 1. Encoding Errors
**Problem**: Chinese characters appear as `�o���֪��D`
**Solution**:
```python
import sys
import codecs
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
```

#### 2. No Data Found
**Problem**: `No poems found for temple: [temple_name]`
**Solutions**:
- Check file paths in `SourceCrawler/outputs/[temple_name]/`
- Verify JSON file format
- Ensure file names match pattern `chuck_*.json` or `poem_*.json`

#### 3. Permission Errors
**Problem**: `Permission denied` accessing ChromaDB
**Solution**: Run with administrator privileges or check file permissions

#### 4. API Returns Old Data
**Problem**: API still returns outdated content after sync
**Solutions**:
1. Clear backend cache:
   ```python
   from app.services.poem_service import poem_service
   poem_service.cache.clear()
   ```
2. Restart backend server
3. Verify sync completed successfully

### Validation Commands

#### Check Ingestion Status
```python
from fortune_module.data_ingestion import DataIngestionManager
from fortune_module.unified_rag import UnifiedRAGHandler

rag = UnifiedRAGHandler()
manager = DataIngestionManager(rag)

# Validate all data
validation = manager.validate_ingestion()
print(f"Validation results: {validation}")
```

#### Manual Chunk Inspection
```python
from fortune_module.unified_rag import UnifiedRAGHandler

rag = UnifiedRAGHandler()

# List available poems for a temple
poems = rag.list_available_poems('YueLao')
print(f"YueLao has {len(poems)} poems")

# Check specific poem
chunks = rag.get_poem_by_temple_and_id('YueLao', 50)
for chunk in chunks:
    print(f"Language: {chunk.get('language')}")
    print(f"Content: {chunk.get('content')[:100]}...")
    print("---")
```

## Automation Scripts

### Daily Sync Script
Create `sync_daily.py`:
```python
#!/usr/bin/env python3
import logging
from datetime import datetime
from fortune_module.data_ingestion import quick_ingest_all

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync.log'),
        logging.StreamHandler()
    ]
)

def daily_sync():
    """Perform daily data synchronization"""
    try:
        logging.info("Starting daily sync...")
        result = quick_ingest_all(clear_existing=True)

        logging.info(f"Sync completed successfully:")
        logging.info(f"- Files processed: {result['total_files_processed']}")
        logging.info(f"- Chunks ingested: {result['total_chunks_ingested']}")

        if result['errors']:
            logging.warning(f"Errors encountered: {len(result['errors'])}")
            for error in result['errors']:
                logging.error(f"  - {error}")

        return True

    except Exception as e:
        logging.error(f"Daily sync failed: {e}")
        return False

if __name__ == "__main__":
    success = daily_sync()
    exit(0 if success else 1)
```

### Incremental Sync (Coming Soon)
For large datasets, incremental sync based on file modification times:
```python
# Future feature - track modified files only
def incremental_sync():
    # Compare file timestamps with last sync
    # Only process changed files
    pass
```

## Performance Considerations

### Large Datasets
- **Batch Processing**: The system processes files in batches of 50
- **Memory Usage**: Each temple requires ~100MB RAM during ingestion
- **Storage**: Each poem creates 4-6 chunks (~2KB each)

### Optimization Tips
1. **Selective Sync**: Update only changed temples using `--temple [name]`
2. **Validation**: Run `--validate` after each sync
3. **Monitoring**: Check logs for encoding or format errors
4. **Cleanup**: Use `--clear` to avoid duplicate data

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: Sync ChromaDB
on:
  push:
    paths:
      - 'SourceCrawler/outputs/**/*.json'

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          cd Backend
          pip install -r requirements.txt
      - name: Sync ChromaDB
        run: |
          cd Backend
          python -m fortune_module.data_ingestion --all --clear
```

## Monitoring and Maintenance

### Health Checks
```python
from app.services.poem_service import poem_service
import asyncio

async def health_check():
    health = await poem_service.health_check()
    print(f"ChromaDB Status: {health.chroma_db_status}")
    print(f"Total Poems: {health.total_poems}")
    print(f"Total Temples: {health.total_temples}")

asyncio.run(health_check())
```

### Regular Maintenance
1. **Weekly**: Full sync with `--clear` flag
2. **Daily**: Incremental sync (when available)
3. **Monthly**: Validation and cleanup
4. **On Updates**: Immediate sync after JSON changes

---

## Quick Reference

| Task | Command |
|------|---------|
| Sync all temples | `python -c "from fortune_module.data_ingestion import quick_ingest_all; quick_ingest_all(clear_existing=True)"` |
| Sync specific temple | `python -c "from fortune_module.data_ingestion import quick_ingest_temple; quick_ingest_temple('YueLao', clear_existing=True)"` |
| Check status | `python -c "from fortune_module.unified_rag import UnifiedRAGHandler; print(UnifiedRAGHandler().get_collection_stats())"` |
| Validate sync | `python -m fortune_module.data_ingestion --validate` |
| Clear cache | `python -c "from app.services.poem_service import poem_service; poem_service.cache.clear()"` |

---

**Need Help?** Check the logs in `Backend/logs/` or run commands with `--verbose` flag for detailed output.