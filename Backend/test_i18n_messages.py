"""
Test script for i18n SSE messages
"""

import sys
import io

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app.i18n import get_message, SSE_MESSAGES


def test_basic_messages():
    """Test basic message retrieval"""
    print("Testing basic messages:")
    print("-" * 60)

    # Test Chinese
    print(f"Chinese initializing: {get_message('zh', 'initializing')}")
    print(f"Chinese RAG start: {get_message('zh', 'rag_start')}")
    print(f"Chinese LLM start: {get_message('zh', 'llm_start')}")
    print(f"Chinese completed: {get_message('zh', 'completed')}")
    print()

    # Test English
    print(f"English initializing: {get_message('en', 'initializing')}")
    print(f"English RAG start: {get_message('en', 'rag_start')}")
    print(f"English LLM start: {get_message('en', 'llm_start')}")
    print(f"English completed: {get_message('en', 'completed')}")
    print()

    # Test Japanese
    print(f"Japanese initializing: {get_message('ja', 'initializing')}")
    print(f"Japanese RAG start: {get_message('ja', 'rag_start')}")
    print(f"Japanese LLM start: {get_message('ja', 'llm_start')}")
    print(f"Japanese completed: {get_message('ja', 'completed')}")
    print()


def test_formatted_messages():
    """Test messages with format parameters"""
    print("Testing formatted messages:")
    print("-" * 60)

    # Test progress messages
    for lang in ['zh', 'en', 'ja']:
        print(f"\n{lang.upper()}:")
        print(f"  Start: {get_message(lang, 'progress_start', operation='test')}")
        print(f"  Processing: {get_message(lang, 'progress_processing', operation='test')}")
        print(f"  Complete: {get_message(lang, 'progress_complete', operation='test')}")

    # Test adaptive messages
    for lang in ['zh', 'en', 'ja']:
        print(f"\n{lang.upper()}:")
        print(f"  Early: {get_message(lang, 'progress_early', stage_name='RAG')}")
        print(f"  Middle: {get_message(lang, 'progress_middle', stage_name='RAG')}")
        print(f"  Late: {get_message(lang, 'progress_late', stage_name='RAG')}")
        print(f"  Overtime: {get_message(lang, 'progress_overtime', stage_name='RAG')}")


def test_llm_streaming_messages():
    """Test LLM streaming messages"""
    print("\nTesting LLM streaming messages:")
    print("-" * 60)

    for lang in ['zh', 'en', 'ja']:
        print(f"\n{lang.upper()}:")
        print(f"  Streaming: {get_message(lang, 'llm_streaming', partial_text='Hello world')}")
        print(f"  Progress: {get_message(lang, 'llm_streaming_progress', token_count=100)}")


def test_fallback():
    """Test fallback behavior"""
    print("\nTesting fallback behavior:")
    print("-" * 60)

    # Test unsupported language (should fallback to Chinese)
    print(f"French (fallback to zh): {get_message('fr', 'initializing')}")

    # Test missing key (should fallback to Chinese)
    print(f"Missing key (fallback): {get_message('en', 'nonexistent_key')}")


def test_all_rag_steps():
    """Test all RAG processing steps"""
    print("\nTesting all RAG steps:")
    print("-" * 60)

    rag_steps = [
        'rag_start',
        'rag_processing_connect',
        'rag_processing_vector',
        'rag_processing_search',
        'rag_processing_score',
        'rag_processing_sort',
        'rag_processing_prepare',
        'rag_complete'
    ]

    for lang in ['zh', 'en', 'ja']:
        print(f"\n{lang.upper()} RAG Steps:")
        for step in rag_steps:
            print(f"  {step}: {get_message(lang, step)}")


def test_all_llm_steps():
    """Test all LLM processing steps"""
    print("\nTesting all LLM steps:")
    print("-" * 60)

    llm_steps = [
        'llm_start',
        'llm_processing_load',
        'llm_processing_analyze',
        'llm_processing_context',
        'llm_processing_generate',
        'llm_processing_optimize',
        'llm_processing_wisdom',
        'llm_processing_check',
        'llm_processing_polish',
        'llm_processing_format',
        'llm_processing_final',
        'llm_complete'
    ]

    for lang in ['zh', 'en', 'ja']:
        print(f"\n{lang.upper()} LLM Steps:")
        for step in llm_steps:
            print(f"  {step}: {get_message(lang, step)}")


def test_message_coverage():
    """Verify all languages have all keys"""
    print("\nTesting message coverage:")
    print("-" * 60)

    languages = ['zh', 'en', 'ja']
    all_keys = set()

    # Collect all keys from all languages
    for lang in languages:
        all_keys.update(SSE_MESSAGES[lang].keys())

    # Check each language has all keys
    for lang in languages:
        missing_keys = all_keys - set(SSE_MESSAGES[lang].keys())
        if missing_keys:
            print(f"❌ {lang.upper()} missing keys: {missing_keys}")
        else:
            print(f"✅ {lang.upper()} has all {len(all_keys)} keys")

    print(f"\nTotal unique message keys: {len(all_keys)}")


if __name__ == "__main__":
    test_basic_messages()
    test_formatted_messages()
    test_llm_streaming_messages()
    test_fallback()
    test_all_rag_steps()
    test_all_llm_steps()
    test_message_coverage()

    print("\n" + "=" * 60)
    print("✅ All i18n tests completed!")
