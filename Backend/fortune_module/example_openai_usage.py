"""
Example: Using OpenAI Structured Output with FortuneInterpretation Schema

This example demonstrates how to use the Pydantic schema for structured output
with OpenAI API in production, compared to the Ollama flow used in development.
"""

from schemas import FortuneInterpretation
from llm_client import LLMClientFactory
from models import LLMProvider
import json


def example_openai_structured_output():
    """Example of using OpenAI with structured output."""

    print("=== OpenAI Structured Output Example ===\n")

    # Create OpenAI client
    openai_client = LLMClientFactory.create_client(
        provider=LLMProvider.OPENAI,
        api_key="your-api-key-here",
        model="gpt-4o-mini"  # or gpt-4, gpt-3.5-turbo
    )

    # Sample context and question
    context = """
    === SELECTED FORTUNE POEM ===
    Temple: GuanYu
    Poem #60

    The clouds part to reveal the bright moon,
    Spring arrives and flowers bloom abundantly,
    Past difficulties transform into blessings,
    Your sincere heart will be rewarded.

    Fortune Level: 上上籤 (Excellent Fortune)
    """

    question = "I'm worried about my career prospects. What does this fortune tell me?"

    # Create prompt
    prompt = f"""
    You are a wise fortune interpretation assistant.

    CONTEXT:
    {context}

    USER QUESTION: {question}

    Please provide a detailed interpretation following the 7-section structure:
    1. LineByLineInterpretation: Detailed line-by-line analysis with "Line 1:", "Line 2:" labels
    2. OverallDevelopment: Current situation and future trends (4-5 sentences)
    3. PositiveFactors: Strengths and opportunities (4-5 sentences)
    4. Challenges: Risks and difficulties (4-5 sentences)
    5. SuggestedActions: Practical advice (4-5 sentences)
    6. SupplementaryNotes: Additional insights (4-5 sentences)
    7. Conclusion: Reassuring message (4-5 sentences)
    """

    # Generate with structured output
    # OpenAI will automatically return JSON matching FortuneInterpretation schema
    response_json = openai_client.generate(
        prompt=prompt,
        response_format=FortuneInterpretation,  # Pydantic schema
        temperature=0.7,
        max_tokens=2500
    )

    print("✅ OpenAI returned structured JSON:")
    print(response_json)

    # Parse the JSON
    interpretation = json.loads(response_json)

    print("\n📋 Parsed Fields:")
    print(f"- LineByLineInterpretation: {len(interpretation['LineByLineInterpretation'])} chars")
    print(f"- OverallDevelopment: {len(interpretation['OverallDevelopment'])} chars")
    print(f"- PositiveFactors: {len(interpretation['PositiveFactors'])} chars")
    print(f"- Challenges: {len(interpretation['Challenges'])} chars")
    print(f"- SuggestedActions: {len(interpretation['SuggestedActions'])} chars")
    print(f"- SupplementaryNotes: {len(interpretation['SupplementaryNotes'])} chars")
    print(f"- Conclusion: {len(interpretation['Conclusion'])} chars")

    return interpretation


def example_ollama_json_output():
    """Example of using Ollama with manual JSON parsing (development flow)."""

    print("\n=== Ollama JSON Output Example ===\n")

    # Create Ollama client
    ollama_client = LLMClientFactory.create_client(
        provider=LLMProvider.OLLAMA,
        base_url="http://localhost:11434",
        model="llama3.2:latest"
    )

    # For Ollama, we need to explicitly instruct JSON format in the prompt
    context = """
    === SELECTED FORTUNE POEM ===
    Temple: GuanYu
    Poem #60

    The clouds part to reveal the bright moon,
    Spring arrives and flowers bloom abundantly,
    Past difficulties transform into blessings,
    Your sincere heart will be rewarded.

    Fortune Level: 上上籤 (Excellent Fortune)
    """

    question = "I'm worried about my career prospects. What does this fortune tell me?"

    # Create prompt with explicit JSON format instructions
    prompt = f"""
    You are a wise fortune interpretation assistant.

    CONTEXT:
    {context}

    USER QUESTION: {question}

    CRITICAL: Return ONLY a valid JSON object with these exact keys:
    {{
        "LineByLineInterpretation": "Detailed line-by-line analysis...",
        "OverallDevelopment": "4-5 sentences...",
        "PositiveFactors": "4-5 sentences...",
        "Challenges": "4-5 sentences...",
        "SuggestedActions": "4-5 sentences...",
        "SupplementaryNotes": "4-5 sentences...",
        "Conclusion": "4-5 sentences..."
    }}

    Do NOT include any text before or after the JSON object.
    """

    # Generate response
    response = ollama_client.generate(
        prompt=prompt,
        temperature=0.7,
        max_tokens=2500
    )

    print("✅ Ollama returned text (needs manual JSON parsing):")
    print(response[:200] + "...")

    # Parse the JSON manually (may fail if format is wrong)
    try:
        interpretation = json.loads(response.strip())
        print("\n✅ Successfully parsed JSON from Ollama response")
    except json.JSONDecodeError as e:
        print(f"\n❌ Failed to parse JSON: {e}")
        print("⚠️ This is why OpenAI structured output is more reliable!")
        return None

    return interpretation


def comparison_summary():
    """Compare the two approaches."""

    print("\n" + "="*70)
    print("COMPARISON: OpenAI Structured Output vs Ollama Manual JSON")
    print("="*70)

    print("""
    ╔═══════════════════════════╦══════════════════╦═══════════════════╗
    ║ Feature                   ║ OpenAI (Prod)    ║ Ollama (Dev)      ║
    ╠═══════════════════════════╬══════════════════╬═══════════════════╣
    ║ Schema Enforcement        ║ ✅ Automatic     ║ ❌ Manual         ║
    ║ JSON Validity Guarantee   ║ ✅ 100%          ║ ⚠️ Best effort    ║
    ║ Validation Needed         ║ ❌ Minimal       ║ ✅ Required       ║
    ║ Retry Logic               ║ ⚠️ Rare          ║ ⚠️ Often needed   ║
    ║ Prompt Complexity         ║ ✅ Simple        ║ ⚠️ Complex        ║
    ║ Development Cost          ║ 💰 Paid API      ║ ✅ Free (local)   ║
    ║ Response Time             ║ ⚡ Fast          ║ ⚠️ Slower         ║
    ║ Quality Consistency       ║ ✅ High          ║ ⚠️ Variable       ║
    ╚═══════════════════════════╩══════════════════╩═══════════════════╝

    RECOMMENDATION:
    - Development: Use Ollama (free, local) with manual validation
    - Production: Use OpenAI (paid) with response_format for reliability

    The system automatically detects which client is being used and adjusts:
    - OpenAI: Uses FortuneInterpretation schema with response_format
    - Ollama: Uses detailed prompt with manual JSON validation
    """)


if __name__ == "__main__":
    print("DivineWhispers - OpenAI Structured Output Integration\n")

    # Show comparison
    comparison_summary()

    print("\n" + "="*70)
    print("To run actual examples, uncomment the function calls below")
    print("and provide your OpenAI API key")
    print("="*70)

    # Uncomment to run examples:
    # example_openai_structured_output()
    # example_ollama_json_output()
