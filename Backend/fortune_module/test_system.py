#!/usr/bin/env python3
# test_system.py - Comprehensive Test Suite for Fortune System
"""
Comprehensive test suite for the Fortune Poem RAG System.

This module provides unit tests, integration tests, and system tests
for all components of the fortune system.

Usage:
    python test_system.py                    # Run all tests
    python test_system.py --unit            # Run only unit tests  
    python test_system.py --integration     # Run only integration tests
    python test_system.py --system          # Run only system tests
    python test_system.py --verbose         # Verbose output
"""

import unittest
import tempfile
import shutil
import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import logging

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the fortune module components
from models import *
from config import SystemConfig
from unified_rag import UnifiedRAGHandler
from llm_client import LLMClientFactory, MockLLMClient
from faq_pipeline import FAQPipeline
from interpreter import PoemInterpreter, InterpreterFactory
from data_ingestion import DataIngestionManager, PoemChunkBuilder
from . import FortuneSystem, create_fortune_system

# Test data
SAMPLE_POEM_DATA = {
    "id": 1,
    "title": "Test Fortune Poem",
    "subtitle": "Test Subtitle",
    "fortune": "上籤",
    "poem": "天開地闢結良緣、日吉時良萬事全、若得此籤非小可、人行中正帝王宣。",
    "analysis": {
        "zh": "這是一個測試分析",
        "en": "This is a test analysis",
        "jp": "これはテスト分析です"
    },
    "rag_analysis": "This is RAG analysis for testing"
}

class TestConfig(unittest.TestCase):
    """Test the SystemConfig singleton."""
    
    def setUp(self):
        # Reset singleton for each test
        SystemConfig.reset_instance()
    
    def test_singleton_behavior(self):
        """Test that SystemConfig behaves as singleton."""
        config1 = SystemConfig()
        config2 = SystemConfig()
        self.assertIs(config1, config2)
    
    def test_default_config(self):
        """Test default configuration values."""
        config = SystemConfig()
        self.assertEqual(config.chroma_persist_path, "./chroma_db")
        self.assertEqual(config.collection_name, "fortune_knowledge")
        self.assertEqual(config.default_llm_provider, "openai")
        self.assertTrue(config.auto_capture_faq)
    
    def test_config_update(self):
        """Test configuration updates."""
        config = SystemConfig()
        config.update_config(chroma_persist_path="/tmp/test", auto_capture_faq=False)
        self.assertEqual(config.chroma_persist_path, "/tmp/test")
        self.assertFalse(config.auto_capture_faq)
    
    def test_llm_config_retrieval(self):
        """Test LLM configuration retrieval."""
        config = SystemConfig()
        openai_config = config.get_llm_config("openai")
        self.assertIn("model", openai_config)
        
        ollama_config = config.get_llm_config("ollama")
        self.assertIn("base_url", ollama_config)
        self.assertIn("model", ollama_config)

class TestModels(unittest.TestCase):
    """Test the data models."""
    
    def test_poem_chunk_creation(self):
        """Test PoemChunk creation."""
        chunk = PoemChunk(
            chunk_id="test_chunk_1",
            temple="TestTemple",
            poem_id=1,
            title="Test Poem",
            fortune="上籤",
            content="Test content",
            language="zh"
        )
        
        self.assertEqual(chunk.chunk_type, ChunkType.POEM)
        self.assertEqual(chunk.temple, "TestTemple")
        self.assertIsInstance(chunk.metadata, dict)
    
    def test_faq_chunk_creation(self):
        """Test FAQChunk creation."""
        chunk = FAQChunk(
            chunk_id="faq_test_1",
            category="love",
            question="Test question?",
            answer="Test answer",
            content="Q: Test question?\n\nA: Test answer",
            language="en"
        )
        
        self.assertEqual(chunk.chunk_type, ChunkType.FAQ)
        self.assertEqual(chunk.category, "love")
    
    def test_pending_faq_creation(self):
        """Test PendingFAQ creation."""
        from datetime import datetime
        
        pending = PendingFAQ(
            question="Test question?",
            answer="Test answer",
            category="general",
            language="en",
            session_id="test-session-123",
            created_at=datetime.now()
        )
        
        self.assertEqual(pending.status, "pending")
        self.assertEqual(pending.session_id, "test-session-123")

class TestLLMClients(unittest.TestCase):
    """Test LLM client implementations."""
    
    def test_mock_client_creation(self):
        """Test MockLLMClient creation and usage."""
        mock_client = LLMClientFactory.create_mock_client("Test response")
        response = mock_client.generate("Test prompt")
        self.assertIn("Test response", response)
    
    def test_factory_registration(self):
        """Test LLM client factory registration."""
        available_providers = LLMClientFactory.list_available_providers()
        self.assertIn(LLMProvider.OPENAI, available_providers)
        self.assertIn(LLMProvider.OLLAMA, available_providers)
    
    @patch('openai.OpenAI')
    def test_openai_client_creation(self, mock_openai):
        """Test OpenAI client creation."""
        try:
            client = LLMClientFactory.create_client(
                LLMProvider.OPENAI,
                api_key="test-key",
                model="gpt-3.5-turbo"
            )
            self.assertTrue(client.validate_config())
        except ImportError:
            self.skipTest("OpenAI package not available")
    
    def test_invalid_provider(self):
        """Test invalid provider handling."""
        with self.assertRaises(ValueError):
            LLMClientFactory.create_client("invalid_provider", {})

class TestRAGHandler(unittest.TestCase):
    """Test the UnifiedRAGHandler."""
    
    def setUp(self):
        """Set up test with temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.config = SystemConfig()
        self.config.update_config(chroma_persist_path=self.test_dir)
        
        # Create RAG handler with test directory
        self.rag = UnifiedRAGHandler(
            collection_name="test_collection",
            persist_path=self.test_dir
        )
    
    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)
    
    def test_poem_chunk_addition(self):
        """Test adding poem chunks to RAG."""
        chunk = PoemChunk(
            chunk_id="test_poem_1",
            temple="TestTemple",
            poem_id=1,
            title="Test Poem",
            fortune="上籤",
            content="Test poem content",
            language="zh"
        )
        
        success = self.rag.add_poem_chunks([chunk])
        self.assertTrue(success)
        
        # Verify retrieval
        retrieved_chunks = self.rag.get_poem_by_temple_and_id("TestTemple", 1)
        self.assertEqual(len(retrieved_chunks), 1)
        self.assertEqual(retrieved_chunks[0]["chunk_id"], "test_poem_1")
    
    def test_faq_chunk_addition(self):
        """Test adding FAQ chunks to RAG."""
        from datetime import datetime
        
        chunk = FAQChunk(
            chunk_id="faq_test_1",
            category="love",
            question="Test question?",
            answer="Test answer",
            content="Q: Test question?\n\nA: Test answer",
            language="en",
            created_at=datetime.now()
        )
        
        success = self.rag.add_faq_chunk(chunk)
        self.assertTrue(success)
    
    def test_query_functionality(self):
        """Test RAG query functionality."""
        # Add some test data
        chunk = PoemChunk(
            chunk_id="query_test_1",
            temple="TestTemple",
            poem_id=1,
            title="Love Poem",
            fortune="上籤",
            content="This is about love and relationships",
            language="en"
        )
        
        self.rag.add_poem_chunks([chunk])
        
        # Query for relevant content
        result = self.rag.query("love relationship", top_k=5)
        self.assertIsInstance(result, RAGResult)
        self.assertGreaterEqual(len(result.chunks), 0)
    
    def test_collection_stats(self):
        """Test collection statistics."""
        stats = self.rag.get_collection_stats()
        self.assertIn("total_chunks", stats)
        self.assertIn("poem_chunks", stats)
        self.assertIn("faq_chunks", stats)

class TestFAQPipeline(unittest.TestCase):
    """Test the FAQ pipeline and approval workflow."""
    
    def setUp(self):
        """Set up test with temporary database."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_faq.db")
        
        # Create mock RAG handler
        self.mock_rag = Mock(spec=UnifiedRAGHandler)
        self.mock_rag.query.return_value = RAGResult(chunks=[], scores=[], query="test")
        self.mock_rag.add_faq_chunk.return_value = True
        
        self.faq_pipeline = FAQPipeline(
            db_path=self.db_path,
            rag_handler=self.mock_rag
        )
    
    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)
    
    def test_capture_interaction(self):
        """Test capturing user interactions."""
        faq_id = self.faq_pipeline.capture_interaction(
            question="Test question?",
            answer="Test answer",
            category="general",
            language="en",
            session_id="test-session-1"
        )
        
        self.assertGreater(faq_id, 0)
    
    def test_get_pending_faqs(self):
        """Test retrieving pending FAQs."""
        # Add some test data
        self.faq_pipeline.capture_interaction(
            question="Test question?",
            answer="Test answer",
            category="general",
            language="en",
            session_id="test-session-2"
        )
        
        pending_faqs = self.faq_pipeline.get_pending_faqs()
        self.assertEqual(len(pending_faqs), 1)
        self.assertEqual(pending_faqs[0].question, "Test question?")
    
    def test_approve_faq(self):
        """Test FAQ approval process."""
        # Capture an interaction
        self.faq_pipeline.capture_interaction(
            question="Test approval question?",
            answer="Test approval answer",
            category="general",
            language="en",
            session_id="approve-test-1"
        )
        
        # Approve it
        success = self.faq_pipeline.approve_faq(
            session_id="approve-test-1",
            approved_by="test-admin"
        )
        
        self.assertTrue(success)
        self.mock_rag.add_faq_chunk.assert_called_once()
    
    def test_reject_faq(self):
        """Test FAQ rejection process."""
        # Capture an interaction
        self.faq_pipeline.capture_interaction(
            question="Test reject question?",
            answer="Test reject answer",
            category="general",
            language="en",
            session_id="reject-test-1"
        )
        
        # Reject it
        success = self.faq_pipeline.reject_faq(
            session_id="reject-test-1",
            rejected_by="test-admin",
            reason="Not suitable"
        )
        
        self.assertTrue(success)
    
    def test_approval_chain_processing(self):
        """Test FAQ approval chain processing."""
        # Capture an interaction
        self.faq_pipeline.capture_interaction(
            question="Test chain processing question?",
            answer="Test chain processing answer",
            category="general",
            language="en",
            session_id="chain-test-1"
        )
        
        # Process through approval chain
        result = self.faq_pipeline.process_faq_approval("chain-test-1")
        
        self.assertIn("approval_status", result)
        self.assertIn("final_decision", result)

class TestDataIngestion(unittest.TestCase):
    """Test the data ingestion system."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create test data structure
        self.test_data_dir = os.path.join(self.test_dir, "test_outputs")
        self.temple_dir = os.path.join(self.test_data_dir, "TestTemple")
        os.makedirs(self.temple_dir)
        
        # Create test JSON file
        test_file = os.path.join(self.temple_dir, "chuck_1.json")
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(SAMPLE_POEM_DATA, f, ensure_ascii=False, indent=2)
        
        # Mock RAG handler
        self.mock_rag = Mock(spec=UnifiedRAGHandler)
        self.mock_rag.add_poem_chunks.return_value = True
        self.mock_rag.delete_chunks_by_temple.return_value = True
        
        # Create ingestion manager
        self.builder = PoemChunkBuilder()
        self.manager = DataIngestionManager(
            rag_handler=self.mock_rag,
            builder=self.builder
        )
        
        # Override data source path
        self.manager.config.update_config(source_data_path=self.test_data_dir)
        from data_ingestion import FileSystemDataSource
        self.manager.data_source = FileSystemDataSource(self.test_data_dir)
    
    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)
    
    def test_poem_chunk_builder(self):
        """Test the PoemChunkBuilder."""
        chunks = (self.builder
                 .reset()
                 .set_temple_info("TestTemple")
                 .set_basic_info(SAMPLE_POEM_DATA)
                 .build_poem_chunks())
        
        self.assertGreater(len(chunks), 0)
        
        # Check first chunk
        chunk = chunks[0]
        self.assertEqual(chunk.temple, "TestTemple")
        self.assertEqual(chunk.poem_id, 1)
        self.assertEqual(chunk.fortune, "上籤")
    
    def test_temple_ingestion(self):
        """Test ingesting data for a temple."""
        stats = self.manager.ingest_temple_data("TestTemple")
        
        self.assertEqual(stats["temple"], "TestTemple")
        self.assertGreater(stats["files_processed"], 0)
        self.assertGreater(stats["chunks_created"], 0)
        
        # Verify RAG handler was called
        self.mock_rag.add_poem_chunks.assert_called()

class TestInterpreter(unittest.TestCase):
    """Test the poem interpreter."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock dependencies
        self.mock_rag = Mock(spec=UnifiedRAGHandler)
        self.mock_llm = Mock()
        self.mock_faq = Mock(spec=FAQPipeline)
        
        # Configure mocks
        self.mock_rag.get_poem_by_temple_and_id.return_value = [{
            "chunk_id": "test_chunk_1",
            "temple": "TestTemple",
            "poem_id": 1,
            "title": "Test Poem",
            "fortune": "上籤",
            "content": "Test poem content",
            "language": "zh"
        }]
        
        self.mock_rag.query.return_value = RAGResult(
            chunks=[],
            scores=[],
            query="test query"
        )
        
        self.mock_llm.generate.return_value = "Test interpretation response"
        self.mock_faq.capture_interaction.return_value = 1
        
        self.interpreter = InterpreterFactory.create_poem_interpreter(
            self.mock_rag, self.mock_llm, self.mock_faq
        )
    
    def test_interpretation_process(self):
        """Test the complete interpretation process."""
        result = self.interpreter.interpret(
            question="Test question?",
            temple="TestTemple",
            poem_id=1,
            additional_context_k=2,
            capture_faq=True
        )
        
        self.assertIsInstance(result, InterpretationResult)
        self.assertEqual(result.interpretation, "Test interpretation response")
        self.assertEqual(result.selected_poem.temple, "TestTemple")
        self.assertEqual(result.selected_poem.poem_id, 1)
        
        # Verify dependencies were called
        self.mock_rag.get_poem_by_temple_and_id.assert_called_with("TestTemple", 1)
        self.mock_llm.generate.assert_called_once()
        self.mock_faq.capture_interaction.assert_called_once()
    
    def test_input_validation(self):
        """Test input validation."""
        with self.assertRaises(ValueError):
            self.interpreter.interpret("", "TestTemple", 1)  # Empty question
        
        with self.assertRaises(ValueError):
            self.interpreter.interpret("Test?", "", 1)  # Empty temple
        
        with self.assertRaises(ValueError):
            self.interpreter.interpret("Test?", "TestTemple", 0)  # Invalid poem ID

class TestFortuneSystemIntegration(unittest.TestCase):
    """Integration tests for the complete Fortune System."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create system with mock LLM
        self.system = FortuneSystem(
            llm_provider=LLMProvider.OPENAI,
            llm_config={"api_key": "test-key"},  # This will fail, but we'll mock it
            config_overrides={"chroma_persist_path": self.test_dir}
        )
        
        # Replace LLM with mock
        self.system.llm = Mock()
        self.system.llm.generate.return_value = "Mock interpretation response"
    
    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)
    
    @patch('fortune_module.llm_client.LLMClientFactory.create_client')
    def test_system_initialization(self, mock_create_client):
        """Test Fortune System initialization."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        system = FortuneSystem(
            llm_provider=LLMProvider.OPENAI,
            llm_config={"api_key": "test-key"}
        )
        
        self.assertIsNotNone(system.rag)
        self.assertIsNotNone(system.llm)
        self.assertIsNotNone(system.faq_pipeline)
        self.assertIsNotNone(system.interpreter)
    
    def test_health_check(self):
        """Test system health check."""
        # Mock the RAG query to return some results
        mock_result = RAGResult(chunks=[{"test": "data"}], scores=[0.5], query="test")
        self.system.rag.query = Mock(return_value=mock_result)
        
        health = self.system.health_check()
        
        self.assertIn("rag", health)
        self.assertIn("llm", health)
        self.assertIn("faq_pipeline", health)
        self.assertIn("overall", health)
    
    def test_configuration_management(self):
        """Test configuration management."""
        original_k = self.system.config.max_poems_per_query
        
        self.system.update_config(max_poems_per_query=5)
        self.assertEqual(self.system.config.max_poems_per_query, 5)
        self.assertNotEqual(self.system.config.max_poems_per_query, original_k)

class TestSystemEndToEnd(unittest.TestCase):
    """End-to-end system tests."""
    
    @unittest.skipIf(os.getenv("SKIP_E2E_TESTS"), "End-to-end tests skipped")
    def test_complete_workflow(self):
        """Test complete fortune consultation workflow."""
        # This test requires actual data and can be skipped in CI
        pass
    
    def test_convenience_functions(self):
        """Test convenience factory functions."""
        with patch('fortune_module.llm_client.LLMClientFactory.create_client') as mock_create:
            mock_create.return_value = Mock()
            
            # Test create_fortune_system
            system = create_fortune_system("openai", api_key="test")
            self.assertIsInstance(system, FortuneSystem)
            
            # Test invalid provider
            with self.assertRaises(ValueError):
                create_fortune_system("invalid_provider")

def run_tests(test_type=None, verbose=False):
    """Run the test suite."""
    # Configure logging
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)
    
    # Determine which tests to run
    if test_type == "unit":
        test_classes = [
            TestConfig, TestModels, TestLLMClients, TestRAGHandler,
            TestFAQPipeline, TestDataIngestion, TestInterpreter
        ]
    elif test_type == "integration":
        test_classes = [TestFortuneSystemIntegration]
    elif test_type == "system":
        test_classes = [TestSystemEndToEnd]
    else:
        # Run all tests
        test_classes = [
            TestConfig, TestModels, TestLLMClients, TestRAGHandler,
            TestFAQPipeline, TestDataIngestion, TestInterpreter,
            TestFortuneSystemIntegration, TestSystemEndToEnd
        ]
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fortune System Test Suite")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--system", action="store_true", help="Run only system tests")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    test_type = None
    if args.unit:
        test_type = "unit"
    elif args.integration:
        test_type = "integration"
    elif args.system:
        test_type = "system"
    
    success = run_tests(test_type=test_type, verbose=args.verbose)
    
    sys.exit(0 if success else 1)