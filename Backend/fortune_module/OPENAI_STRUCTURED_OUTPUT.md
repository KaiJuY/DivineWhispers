# OpenAI Structured Output Integration

## Overview

This system now supports **OpenAI's structured output** feature using Pydantic schemas, providing guaranteed JSON format in production while maintaining Ollama compatibility for development.

## What Changed

### 1. New Pydantic Schema (`schemas.py`)

```python
from pydantic import BaseModel, Field

class FortuneInterpretation(BaseModel):
    """Structured schema for OpenAI API response_format"""

    LineByLineInterpretation: str = Field(..., min_length=100)
    OverallDevelopment: str = Field(..., min_length=50)
    PositiveFactors: str = Field(..., min_length=50)
    Challenges: str = Field(..., min_length=50)
    SuggestedActions: str = Field(..., min_length=50)
    SupplementaryNotes: str = Field(..., min_length=30)
    Conclusion: str = Field(..., min_length=30)
```

### 2. Enhanced LLM Client (`llm_client.py`)

The `OpenAIClient.generate()` method now supports `response_format`:

```python
# Use structured output
response = llm.generate(
    prompt=prompt,
    response_format=FortuneInterpretation,  # Pydantic schema
    temperature=0.7,
    max_tokens=2500
)
# Returns valid JSON string guaranteed to match schema
```

### 3. Smart Detection (`interpreter.py`)

The interpreter automatically detects which client is being used:

- **OpenAI**: Uses simplified prompt + `response_format` schema
- **Ollama**: Uses detailed prompt with explicit JSON formatting instructions

## Usage Examples

### Production (OpenAI)

```python
from fortune_module import LLMClientFactory, LLMProvider
from fortune_module.schemas import FortuneInterpretation

# Create OpenAI client
client = LLMClientFactory.create_client(
    provider=LLMProvider.OPENAI,
    api_key="sk-...",
    model="gpt-4o-mini"
)

# Generate with guaranteed structure
response_json = client.generate(
    prompt="Interpret this fortune poem...",
    response_format=FortuneInterpretation,
    temperature=0.7
)

# response_json is guaranteed valid JSON matching schema
import json
interpretation = json.loads(response_json)
print(interpretation["LineByLineInterpretation"])
```

### Development (Ollama)

```python
from fortune_module import LLMClientFactory, LLMProvider

# Create Ollama client
client = LLMClientFactory.create_client(
    provider=LLMProvider.OLLAMA,
    base_url="http://localhost:11434",
    model="llama3.2:latest"
)

# Generate with detailed prompt (manual JSON validation)
response = client.generate(
    prompt="Return only valid JSON: {...}",
    temperature=0.7
)

# May need validation and retry logic
```

## Benefits of Structured Output

| Feature | OpenAI (Prod) | Ollama (Dev) |
|---------|---------------|--------------|
| **Schema Enforcement** | ✅ Automatic | ❌ Manual |
| **JSON Validity** | ✅ 100% guaranteed | ⚠️ Best effort |
| **Validation Needed** | ❌ Minimal | ✅ Required |
| **Retry Logic** | ⚠️ Rare | ⚠️ Often needed |
| **Prompt Complexity** | ✅ Simple | ⚠️ Complex |
| **Cost** | 💰 Paid API | ✅ Free (local) |
| **Response Time** | ⚡ Fast | ⚠️ Slower |
| **Quality Consistency** | ✅ High | ⚠️ Variable |

## Configuration

### Environment Variables

```env
# For OpenAI (Production)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional

# For Ollama (Development)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest
```

### In Code

The system automatically detects the LLM provider and adjusts:

```python
# interpreter.py automatically detects
use_structured_output = self._should_use_structured_output()

if use_structured_output:
    # OpenAI: Use FortuneInterpretation schema
    gen_kwargs["response_format"] = FortuneInterpretation
    prompt = self._create_structured_output_prompt(...)
else:
    # Ollama: Use detailed JSON format instructions
    prompt = self._create_interpretation_prompt(...)
```

## Migration Guide

### Switching from Development to Production

1. **Set environment variables:**
   ```env
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-your-key-here
   OPENAI_MODEL=gpt-4o-mini
   ```

2. **No code changes needed!** The system automatically:
   - Detects OpenAI client
   - Uses `FortuneInterpretation` schema
   - Generates simpler prompts
   - Returns guaranteed valid JSON

3. **Test the integration:**
   ```bash
   cd Backend
   python -m fortune_module.example_openai_usage
   ```

### Switching from Production to Development

1. **Set environment variables:**
   ```env
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.2:latest
   ```

2. **Start Ollama:**
   ```bash
   ollama serve
   ollama pull llama3.2:latest
   ```

3. **No code changes needed!** System automatically reverts to manual validation.

## Files Modified

### New Files
- ✅ `fortune_module/schemas.py` - Pydantic schema definition
- ✅ `fortune_module/example_openai_usage.py` - Usage examples
- ✅ `fortune_module/OPENAI_STRUCTURED_OUTPUT.md` - This documentation

### Modified Files
- ✅ `fortune_module/llm_client.py` - Added structured output support
- ✅ `fortune_module/interpreter.py` - Added auto-detection and dual-prompt logic

## Testing

See `example_openai_usage.py` for complete examples demonstrating:

1. ✅ OpenAI structured output with guaranteed JSON
2. ✅ Ollama manual JSON parsing with validation
3. ✅ Side-by-side comparison
4. ✅ Migration patterns

## Recommendations

- **Development**: Use Ollama (free, local)
- **Staging**: Test with OpenAI (low volume)
- **Production**: Use OpenAI with structured output (reliable, fast, high quality)

## Additional Notes

- **No breaking changes**: Existing Ollama-based flows continue to work
- **Automatic detection**: System chooses the right approach based on LLM client
- **Backward compatible**: All validation logic remains for Ollama
- **Future-proof**: Easy to add more LLM providers (Claude, Gemini, etc.)

## References

- [OpenAI Structured Outputs Documentation](https://platform.openai.com/docs/guides/structured-outputs)
- [Pydantic BaseModel Documentation](https://docs.pydantic.dev/latest/concepts/models/)
- DivineWhispers Fortune Module: `fortune_module/interpreter.py`
