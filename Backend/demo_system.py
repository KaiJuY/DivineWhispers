#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# demo_system.py - Fortune System Demonstration Script
"""
Demonstration script for the Fortune Poem RAG System.

This script shows how to:
1. Initialize the system
2. Ingest fortune poem data 
3. Perform fortune consultations
4. Manage FAQ pipeline
5. System administration tasks

Usage:
    python demo_system.py --setup          # Setup and ingest data
    python demo_system.py --demo           # Run demonstration
    python demo_system.py --interactive    # Interactive mode
    python demo_system.py --test-llm       # Test LLM connectivity
"""

# Fix Unicode output on Windows
import sys
import io
import os

if sys.platform == "win32":
    # Set console to UTF-8 on Windows
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'
import sys
import json
import logging
from pathlib import Path

# Add fortune_module to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fortune_module'))

try:
    from fortune_module import (
        FortuneSystem, create_openai_system, create_ollama_system, 
        LLMProvider, SystemConfig, create_fortune_system
    )
    from fortune_module.data_ingestion import create_ingestion_manager, quick_ingest_all
    from fortune_module.llm_client import LLMClientFactory
except ImportError as e:
    print(f"Error importing fortune_module: {e}")
    print("Make sure you're running from the correct directory and all dependencies are installed.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_llm_connectivity():
    """Test LLM connectivity for different providers."""
    print("=== Testing LLM Connectivity ===\n")
    
    # Test OpenAI (requires API key)
    print("1. Testing OpenAI connectivity...")
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            client = LLMClientFactory.create_client(
                LLMProvider.OPENAI,
                api_key=openai_key,
                model="gpt-3.5-turbo"
            )
            response = client.generate("Say 'Hello from OpenAI!'", max_tokens=10)
            print(f"   ✓ OpenAI connected successfully: {response[:50]}...")
        except Exception as e:
            print(f"   ✗ OpenAI connection failed: {e}")
    else:
        print("   - OpenAI API key not found (set OPENAI_API_KEY environment variable)")
    
    # Test Ollama
    print("\n2. Testing Ollama connectivity...")
    try:
        client = LLMClientFactory.create_client(
            LLMProvider.OLLAMA,
            base_url="http://localhost:11434",
            model="gpt-oss:20b"
        )
        response = client.generate("Say 'Hello from Ollama!'", max_tokens=10)
        print(f"   ✓ Ollama connected successfully: {response[:50]}...")
    except Exception as e:
        print(f"   ✗ Ollama connection failed: {e}")
        print("   Make sure Ollama is running and gpt-oss:20b model is available")
    
    # Test Mock client (always works)
    print("\n3. Testing Mock LLM client...")
    try:
        client = LLMClientFactory.create_mock_client("Hello from Mock LLM!")
        response = client.generate("Test prompt")
        print(f"   ✓ Mock client works: {response[:50]}...")
    except Exception as e:
        print(f"   ✗ Mock client failed: {e}")

def setup_system():
    """Set up the fortune system and ingest data."""
    print("=== Setting Up Fortune System ===\n")
    
    # Check data availability
    data_path = Path("../SourceCrawler/outputs/")
    if not data_path.exists():
        print(f"❌ Data directory not found: {data_path.absolute()}")
        print("Please make sure the SourceCrawler has generated the poem data.")
        return False
    
    print(f"📁 Found data directory: {data_path.absolute()}")
    
    # List available temples
    temples = [d.name for d in data_path.iterdir() if d.is_dir()]
    print(f"🏛️  Available temples: {', '.join(temples)}")
    
    if not temples:
        print("❌ No temple directories found in data path")
        return False
    
    # Ingest data
    print("\n⚡ Starting data ingestion...")
    try:
        results = quick_ingest_all(clear_existing=True)
        
        print(f"✅ Data ingestion completed!")
        print(f"   📊 Total files processed: {results['total_files_processed']}")
        print(f"   📦 Total chunks created: {results['total_chunks_created']}")
        print(f"   💾 Total chunks ingested: {results['total_chunks_ingested']}")
        
        if results['errors']:
            print(f"   ⚠️  Errors encountered: {len(results['errors'])}")
            for error in results['errors'][:3]:  # Show first 3 errors
                print(f"      - {error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data ingestion failed: {e}")
        return False

def create_demo_system():
    """Create a fortune system for demonstration."""
    print("=== Creating Fortune System ===\n")
    
    # Try different LLM providers
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if openai_key:
        print("🤖 Using OpenAI LLM provider...")
        try:
            system = create_openai_system(
                api_key=openai_key,
                model="gpt-3.5-turbo"
            )
            print("✅ OpenAI system created successfully")
            return system
        except Exception as e:
            print(f"❌ OpenAI system creation failed: {e}")
    
    # Try Ollama
    print("🦙 Trying Ollama LLM provider...")
    try:
        system = create_ollama_system(
            model="gpt-oss:20b",
            base_url="http://localhost:11434"
        )
        # Test with a simple generation
        response = system.llm.generate("Hello", max_tokens=5)
        print("✅ Ollama system created successfully")
        return system
    except Exception as e:
        print(f"❌ Ollama system creation failed: {e}")
    
    # Fall back to mock system
    print("🎭 Using mock LLM for demonstration...")
    try:
        system = FortuneSystem(
            llm_provider=LLMProvider.OPENAI,  # Will be replaced with mock
            llm_config={"api_key": "mock"}
        )
        # Replace with mock client
        mock_client = LLMClientFactory.create_mock_client(
            "This is a demonstration interpretation from the Fortune System. "
            "The selected poem suggests positive outcomes and favorable circumstances. "
            "Trust in your path and maintain patience as opportunities unfold."
        )
        system.llm = mock_client
        print("✅ Mock system created for demonstration")
        return system
    except Exception as e:
        print(f"❌ Mock system creation failed: {e}")
        return None

def demonstrate_fortune_consultation():
    """Demonstrate fortune consultation features."""
    print("=== Fortune Consultation Demonstration ===\n")
    
    # Create system
    system = create_demo_system()
    if not system:
        print("❌ Could not create fortune system")
        return
    
    # Check system health
    print("🏥 System health check:")
    health = system.health_check()
    for component, status in health.items():
        status_icon = "✅" if status == "healthy" else "❌"
        print(f"   {status_icon} {component}: {status}")
    
    if health["overall"] != "healthy":
        print("\n⚠️  System not fully healthy, but continuing with demonstration...")
    
    # Get system statistics
    print("\n📊 System statistics:")
    stats = system.get_system_stats()
    if "rag_collection" in stats:
        rag_stats = stats["rag_collection"]
        print(f"   📦 Total chunks: {rag_stats.get('total_chunks', 0)}")
        print(f"   📜 Poem chunks: {rag_stats.get('poem_chunks', 0)}")
        print(f"   ❓ FAQ chunks: {rag_stats.get('faq_chunks', 0)}")
        print(f"   🏛️  Temples: {rag_stats.get('unique_temples', 0)}")
    
    # List available poems
    print("\n🏛️  Available temples and poems:")
    temples = system.rag.get_collection_stats().get("temple_list", [])
    for temple in temples[:3]:  # Show first 3 temples
        poems = system.list_available_poems(temple)
        print(f"   {temple}: {len(poems)} poems available")
        if poems:
            # Show first poem as example
            example = poems[0]
            print(f"      Example: Poem #{example['poem_id']} - {example['title'][:50]}...")
    
    # Demonstrate fortune consultation
    if temples:
        print("\n🔮 Fortune Consultation Demo:")
        temple = temples[0]
        poems = system.list_available_poems(temple)
        
        if poems:
            poem = poems[0]
            question = "What does my future hold in terms of career and success?"
            
            print(f"   🙏 Question: {question}")
            print(f"   🏛️  Temple: {temple}")
            print(f"   📜 Poem: #{poem['poem_id']} - {poem['title']}")
            
            try:
                result = system.ask_fortune(
                    question=question,
                    temple=temple,
                    poem_id=poem['poem_id'],
                    additional_context=True,
                    capture_faq=True
                )
                
                print(f"\n✨ Interpretation:")
                print("   " + "="*60)
                # Format the interpretation with indentation
                lines = result.interpretation.split('\n')
                for line in lines:
                    print(f"   {line}")
                print("   " + "="*60)
                
                print(f"\n📋 Consultation Metadata:")
                print(f"   🎯 Confidence: {result.confidence:.2f}")
                print(f"   📚 Additional sources: {result.sources['poems']} poems, {result.sources['faqs']} FAQs")
                print(f"   🏛️  Temple sources: {', '.join(result.temple_sources)}")
                
            except Exception as e:
                print(f"   ❌ Consultation failed: {e}")

def demonstrate_faq_management():
    """Demonstrate FAQ management features."""
    print("\n=== FAQ Management Demonstration ===\n")
    
    system = create_demo_system()
    if not system:
        return
    
    # Get FAQ statistics
    print("📊 FAQ Pipeline Statistics:")
    pending_faqs = system.get_pending_faqs()
    print(f"   📝 Pending FAQs: {len(pending_faqs)}")
    
    if pending_faqs:
        print("\n📋 Recent FAQ entries:")
        for i, faq in enumerate(pending_faqs[:3]):  # Show first 3
            print(f"   {i+1}. Session: {faq.session_id}")
            print(f"      Q: {faq.question[:80]}...")
            print(f"      A: {faq.answer[:80]}...")
            print(f"      Category: {faq.category}")
            print(f"      Status: {faq.status}")
            print()
        
        # Demonstrate approval process
        print("🔄 Demonstrating FAQ approval process:")
        sample_faq = pending_faqs[0]
        
        # Process through approval chain
        result = system.process_faq_approval(sample_faq.session_id)
        print(f"   📝 Processing result: {result.get('approval_status', 'unknown')}")
        print(f"   💭 Decision: {result.get('final_decision', 'none')}")
        
        if result.get('approval_status') == 'auto_approved':
            # Auto-approve it
            success = system.approve_faq(
                session_id=sample_faq.session_id,
                approved_by="demo_system"
            )
            if success:
                print("   ✅ FAQ automatically approved and added to knowledge base")
            else:
                print("   ❌ FAQ approval failed")

def interactive_mode():
    """Run interactive consultation mode."""
    print("=== Interactive Fortune Consultation ===\n")
    
    system = create_demo_system()
    if not system:
        print("❌ Could not initialize system for interactive mode")
        return
    
    # Get available temples
    temples = system.rag.get_collection_stats().get("temple_list", [])
    if not temples:
        print("❌ No temples available. Please run setup first.")
        return
    
    print(f"🏛️  Available temples: {', '.join(temples)}")
    print("\nWelcome to the Divine Whispers Fortune System!")
    print("You can ask questions and get interpretations from ancient temple wisdom.")
    print("Type 'quit' to exit, 'help' for commands.\n")
    
    while True:
        try:
            command = input("🔮 Enter your command: ").strip()
            
            if command.lower() in ['quit', 'exit', 'q']:
                print("🙏 Thank you for using Divine Whispers. May fortune be with you!")
                break
            
            elif command.lower() in ['help', 'h']:
                print("\n📋 Available commands:")
                print("  ask <question>     - Ask a fortune question")
                print("  random            - Get random poem consultation")
                print("  temples           - List available temples")
                print("  stats             - Show system statistics")
                print("  health            - Check system health")
                print("  help              - Show this help")
                print("  quit              - Exit the system")
                print()
            
            elif command.lower() == 'temples':
                print(f"\n🏛️  Available temples ({len(temples)}):")
                for temple in temples:
                    poems = system.list_available_poems(temple)
                    print(f"   📜 {temple}: {len(poems)} poems")
                print()
            
            elif command.lower() == 'stats':
                stats = system.get_system_stats()
                rag_stats = stats.get("rag_collection", {})
                print(f"\n📊 System Statistics:")
                print(f"   📦 Total chunks: {rag_stats.get('total_chunks', 0)}")
                print(f"   📜 Poem chunks: {rag_stats.get('poem_chunks', 0)}")
                print(f"   ❓ FAQ chunks: {rag_stats.get('faq_chunks', 0)}")
                print(f"   🏛️  Temples: {rag_stats.get('unique_temples', 0)}")
                print()
            
            elif command.lower() == 'health':
                health = system.health_check()
                print(f"\n🏥 System Health:")
                for component, status in health.items():
                    status_icon = "✅" if status == "healthy" else "❌"
                    print(f"   {status_icon} {component}: {status}")
                print()
            
            elif command.lower() == 'random':
                print("\n🎲 Getting random poem for consultation...")
                try:
                    random_poem = system.random_poem()
                    question = "What guidance can you offer me today?"
                    
                    result = system.ask_fortune(
                        question=question,
                        temple=random_poem.temple,
                        poem_id=random_poem.poem_id
                    )
                    
                    print(f"🏛️  Temple: {random_poem.temple}")
                    print(f"📜 Poem: #{random_poem.poem_id}")
                    print(f"❓ Question: {question}")
                    print(f"\n✨ Interpretation:")
                    print("─" * 60)
                    print(result.interpretation)
                    print("─" * 60)
                    print()
                    
                except Exception as e:
                    print(f"❌ Random consultation failed: {e}\n")
            
            elif command.lower().startswith('ask '):
                question, temple, chuckid = command.split('|')
                question = question[4:].strip()
                if not question:
                    print("❌ Please provide a question after 'ask'\n")
                    continue
                if not temple:
                    print("❌ Please provide a temple after 'ask'\n")
                    continue
                if not chuckid:
                    print("❌ Please provide a poem ID after 'ask'\n")
                    continue
                # Use first available temple and a random poem
                # import random
                # temple = random.choice(temples)
                poems = system.list_available_poems(temple)
                
                if not poems:
                    print(f"❌ No poems available for temple {temple}\n")
                    continue
                
                # poem = random.choice(poems)

                print(f"\n🔍 Consulting the wisdom of {temple}...")
                print(f"📜 Selected poem: #{chuckid} ...")
                
                try:
                    result = system.ask_fortune(
                        question=question,
                        temple=temple,
                        poem_id=int(chuckid)
                    )
                    
                    print(f"\n✨ Interpretation:")
                    print("─" * 60)
                    print(result.interpretation)
                    print("─" * 60)
                    print(f"🎯 Confidence: {result.confidence:.2f}")
                    print()
                    
                except Exception as e:
                    print(f"❌ Consultation failed: {e}\n")
            
            else:
                print(f"❓ Unknown command: '{command}'. Type 'help' for available commands.\n")
        
        except KeyboardInterrupt:
            print("\n\n🙏 Thank you for using Divine Whispers. May fortune be with you!")
            break
        except EOFError:
            break

def main():
    """Main demonstration function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fortune System Demonstration")
    parser.add_argument("--setup", action="store_true", help="Setup system and ingest data")
    parser.add_argument("--demo", action="store_true", help="Run full demonstration")
    parser.add_argument("--interactive", action="store_true", help="Interactive consultation mode")
    parser.add_argument("--test-llm", action="store_true", help="Test LLM connectivity")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("*** Divine Whispers Fortune System Demo ***")
    print("=" * 50)
    
    if args.test_llm:
        test_llm_connectivity()
    
    elif args.setup:
        success = setup_system()
        if success:
            print("\n✅ Setup completed successfully!")
            print("You can now run demonstrations with --demo or --interactive")
        else:
            print("\n❌ Setup failed. Please check the errors above.")
    
    elif args.interactive:
        interactive_mode()
    
    elif args.demo:
        # Check if data is available
        config = SystemConfig()
        from fortune_module.unified_rag import UnifiedRAGHandler
        rag = UnifiedRAGHandler()
        stats = rag.get_collection_stats()
        
        if stats.get('total_chunks', 0) == 0:
            print("\n⚠️  No data found in the system.")
            print("Please run --setup first to ingest the poem data.")
            return
        
        demonstrate_fortune_consultation()
        demonstrate_faq_management()
        
        print("\n✅ Demonstration completed!")
        print("Try --interactive mode for hands-on experience.")
    
    else:
        print("\nUsage examples:")
        print("  python demo_system.py --setup       # First-time setup")
        print("  python demo_system.py --demo        # Run demonstrations")
        print("  python demo_system.py --interactive # Interactive mode")
        print("  python demo_system.py --test-llm    # Test LLM connectivity")
        print("\nFor help: python demo_system.py --help")

if __name__ == "__main__":
    main()