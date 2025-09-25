# interpreter.py
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import uuid
import re
import logging
from .models import InterpretationResult, ChunkType, SelectedPoem
from .unified_rag import UnifiedRAGHandler
from .llm_client import BaseLLMClient
from .faq_pipeline import FAQPipeline
from .config import SystemConfig

# Template Method Pattern - Base interpreter class
class BaseInterpreter(ABC):
    """Base interpreter class using Template Method pattern."""
    
    def __init__(self, rag_handler: UnifiedRAGHandler, llm_client: BaseLLMClient, faq_pipeline: FAQPipeline):
        self.rag = rag_handler
        self.llm = llm_client
        self.faq_pipeline = faq_pipeline
        self.config = SystemConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    # Template Method - defines the algorithm structure
    def interpret(self, question: str, temple: str, poem_id: int, 
                 additional_context_k: int = None, capture_faq: bool = None) -> InterpretationResult:
        """Template method that defines the interpretation workflow."""
        
        additional_context_k = additional_context_k or self.config.max_poems_per_query
        capture_faq = capture_faq if capture_faq is not None else self.config.auto_capture_faq
        
        self.logger.info(f"Starting interpretation for {temple} poem #{poem_id}")
        
        # Step 1: Validate inputs
        self._validate_inputs(question, temple, poem_id)
        
        # Step 2: Retrieve the selected poem
        selected_poem_chunks = self._retrieve_selected_poem(temple, poem_id)
        
        # Step 3: Get additional context via RAG
        additional_chunks = self._get_additional_context(question, temple, poem_id, additional_context_k)
        
        # Step 4: Prepare context for LLM
        context = self._prepare_context(selected_poem_chunks, additional_chunks, temple, poem_id)
        
        # Step 5: Generate interpretation
        interpretation = self._generate_interpretation(question, context, temple, poem_id)
        
        # Step 6: Post-process interpretation
        interpretation = self._post_process_interpretation(interpretation, question)
        
        # Step 7: Build result
        result = self._build_result(interpretation, temple, poem_id, selected_poem_chunks, additional_chunks, question)
        
        # Step 8: Capture FAQ if enabled (after result is built)
        if capture_faq:
            self._capture_faq_interaction(question, result)
        
        self.logger.info(f"Interpretation completed for {temple} poem #{poem_id}")
        return result
    
    # Abstract methods - subclasses must implement these
    @abstractmethod
    def _prepare_context(self, selected_chunks: List[Dict], additional_chunks: List[Dict], 
                        temple: str, poem_id: int) -> str:
        """Prepare the context string for LLM generation."""
        pass
    
    @abstractmethod
    def _generate_interpretation(self, question: str, context: str, temple: str, poem_id: int) -> str:
        """Generate the interpretation using LLM."""
        pass
    
    # Concrete methods - common implementation for all subclasses
    def _validate_inputs(self, question: str, temple: str, poem_id: int):
        """Validate input parameters."""
        if not question or len(question.strip()) < 3:
            raise ValueError("Question must be at least 3 characters long")
        
        if not temple or not temple.strip():
            raise ValueError("Temple name is required")
        
        if not isinstance(poem_id, int) or poem_id <= 0:
            raise ValueError("Poem ID must be a positive integer")
    
    def _retrieve_selected_poem(self, temple: str, poem_id: int) -> List[Dict]:
        """Retrieve the selected poem chunks."""
        selected_poem_chunks = self.rag.get_poem_by_temple_and_id(temple, poem_id)
        if not selected_poem_chunks:
            raise ValueError(f"Poem not found: {temple} poem #{poem_id}")
        
        self.logger.debug(f"Retrieved {len(selected_poem_chunks)} chunks for selected poem")
        return selected_poem_chunks
    
    def _get_additional_context(self, question: str, temple: str, poem_id: int, 
                              additional_context_k: int) -> List[Dict]:
        """Get additional context via RAG (excluding the selected poem)."""
        if additional_context_k <= 0:
            return []
        
        # Get extra results in case selected poem appears
        rag_result = self.rag.query(question, top_k=additional_context_k + 2)
        
        # Filter out the selected poem
        additional_chunks = [
            c for c in rag_result.chunks 
            if not (c.get("temple") == temple and c.get("poem_id") == poem_id)
        ]
        
        # Limit to requested amount
        additional_chunks = additional_chunks[:additional_context_k]
        
        self.logger.debug(f"Retrieved {len(additional_chunks)} additional context chunks")
        return additional_chunks
    
    def _post_process_interpretation(self, interpretation: str, question: str) -> str:
        """Post-process the interpretation (can be overridden by subclasses)."""
        # Basic cleanup
        interpretation = interpretation.strip()
        
        # Ensure the interpretation is not empty
        if not interpretation:
            return "I apologize, but I'm unable to provide a specific interpretation at this moment. Please try rephrasing your question."
        
        return interpretation
    
    def _detect_category(self, question: str) -> str:
        """Simple category detection based on keywords."""
        question_lower = question.lower()
        
        # Define keyword patterns for each category
        categories = {
            'love': ['love', 'relationship', 'marriage', 'partner', 'romance', 'dating', 'heart', '愛', '戀'],
            'career': ['career', 'job', 'work', 'business', 'employment', 'profession', '工作', '事業', '職業'],
            'health': ['health', 'illness', 'recovery', 'medical', 'disease', 'wellness', '健康', '疾病', '醫療'],
            'wealth': ['money', 'wealth', 'financial', 'income', 'fortune', 'prosperity', '財', '錢', '財運'],
            'family': ['family', 'parents', 'children', 'siblings', 'relatives', '家庭', '家人', '父母'],
            'education': ['study', 'education', 'school', 'exam', 'learning', 'knowledge', '學習', '教育', '考試']
        }
        
        for category, keywords in categories.items():
            if any(keyword in question_lower for keyword in keywords):
                return category
        
        return "general"
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection."""
        # Count characters in different scripts
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        japanese_chars = sum(1 for char in text if '\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff')
        total_chars = len(text)
        
        if chinese_chars / total_chars > 0.3:
            return "zh"
        elif japanese_chars / total_chars > 0.2:
            return "jp"
        else:
            return "en"
    
    def _capture_faq_interaction(self, question: str, result: 'InterpretationResult'):
        """Capture the complete consultation for potential FAQ creation."""
        try:
            session_id = str(uuid.uuid4())
            category = self._detect_category(question)
            language = self._detect_language(question)
            
            # Build comprehensive FAQ answer with complete consultation information
            selected_poem = result.selected_poem
            poem_info = ""
            if selected_poem.chunks:
                # Extract poem title and content from chunks
                for chunk in selected_poem.chunks:
                    if chunk.get('title'):
                        poem_info = f"\n**Poem**: {chunk.get('title', 'Unknown')}\n"
                        if chunk.get('content'):
                            # Get first 200 chars of poem content
                            poem_content = chunk['content'][:200] + "..." if len(chunk['content']) > 200 else chunk['content']
                            poem_info += f"**Content**: {poem_content}\n"
                        break
            
            # Build rich FAQ answer
            faq_answer = f"""**Fortune Consultation Details**

**Temple**: {selected_poem.temple}
**Poem ID**: #{selected_poem.poem_id}{poem_info}
**Confidence**: {result.confidence:.2f}
**Additional Sources**: {result.sources['poems']} poems, {result.sources['faqs']} FAQs
**Temple Sources**: {', '.join(result.temple_sources)}

---

**Interpretation**:
{result.interpretation}

---
*This consultation was generated using the DivineWhispers fortune system with RAG-enhanced interpretation.*"""
            
            self.faq_pipeline.capture_interaction(
                question=question,
                answer=faq_answer,
                category=category,
                language=language,
                session_id=session_id
            )
            
            self.logger.info(f"Captured comprehensive FAQ interaction: {session_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to capture FAQ interaction: {e}")
    
    def _calculate_confidence(self, additional_chunks: List[Dict], rag_scores: List[float] = None) -> float:
        """Calculate confidence score based on context quality."""
        if not additional_chunks:
            return 0.7  # Medium confidence with no additional context
        
        if rag_scores:
            # Confidence based on RAG similarity scores (lower distance = higher confidence)
            avg_score = sum(rag_scores[:len(additional_chunks)]) / len(additional_chunks)
            confidence = max(0.1, min(1.0, 1 - avg_score))
        else:
            # Basic confidence based on number of context chunks
            confidence = min(1.0, 0.5 + (len(additional_chunks) * 0.1))
        
        return confidence
    
    def _build_result(self, interpretation: str, temple: str, poem_id: int,
                     selected_chunks: List[Dict], additional_chunks: List[Dict], 
                     question: str) -> InterpretationResult:
        """Build the final interpretation result."""
        
        # Separate chunks by type
        poem_chunks = [c for c in additional_chunks if c["chunk_type"] == ChunkType.POEM.value]
        faq_chunks = [c for c in additional_chunks if c["chunk_type"] == ChunkType.FAQ.value]
        
        # Get temple sources
        temple_sources = list(set([temple] + [c.get("temple", "") for c in poem_chunks if c.get("temple")]))
        
        # Calculate confidence
        confidence = self._calculate_confidence(additional_chunks)
        
        selected_poem = SelectedPoem(
            temple=temple,
            poem_id=poem_id,
            chunks=selected_chunks
        )
        
        return InterpretationResult(
            interpretation=interpretation,
            selected_poem=selected_poem,
            relevant_chunks=additional_chunks,
            sources={
                "poems": len(poem_chunks),
                "faqs": len(faq_chunks)
            },
            temple_sources=temple_sources,
            confidence=confidence
        )

# Concrete implementation for poem interpretation
class PoemInterpreter(BaseInterpreter):
    """Concrete poem interpreter implementation using Template Method pattern."""
    
    def _prepare_context(self, selected_chunks: List[Dict], additional_chunks: List[Dict], 
                        temple: str, poem_id: int) -> str:
        """Prepare context for poem interpretation."""
        context_parts = []
        
        # Add selected poem
        selected_poem_content = "\n".join([chunk["content"] for chunk in selected_chunks])
        context_parts.append(
            f"=== SELECTED FORTUNE POEM ===\nTemple: {temple}\nPoem #{poem_id}\n\n{selected_poem_content}"
        )
        
        # Add additional context
        poem_chunks = [c for c in additional_chunks if c["chunk_type"] == ChunkType.POEM.value]
        faq_chunks = [c for c in additional_chunks if c["chunk_type"] == ChunkType.FAQ.value]
        
        # Limit additional poems
        max_poems = self.config.max_poems_per_query
        for i, chunk in enumerate(poem_chunks[:max_poems]):
            context_parts.append(
                f"=== RELATED POEM {i+1} ===\n"
                f"Temple: {chunk.get('temple', 'Unknown')}\n"
                f"Fortune Level: {chunk.get('fortune', 'Unknown')}\n\n"
                f"{chunk['content']}"
            )
        
        # Limit FAQ context
        max_faqs = self.config.max_faqs_per_query
        for i, chunk in enumerate(faq_chunks[:max_faqs]):
            context_parts.append(
                f"=== RELATED FAQ {i+1} ===\n"
                f"Category: {chunk.get('category', 'General')}\n\n"
                f"{chunk['content']}"
            )
        
        return "\n\n".join(context_parts)
    
    def _generate_interpretation(self, question: str, context: str, temple: str, poem_id: int) -> str:
        """Generate interpretation using LLM."""
        
        # Detect user's language for response
        user_language = self._detect_language(question)
        language_instruction = self._get_language_instruction(user_language)
        
        prompt = f"""
        You are a wise fortune interpretation assistant specializing in Chinese temple divination and oracle reading.
        Your role is to provide thoughtful, supportive guidance based on traditional fortune poems.

        CONTEXT:
        {context}

        USER QUESTION: {question}

        INTERPRETATION GUIDELINES:
        1. Focus primarily on the SELECTED FORTUNE POEM from {temple} (Poem #{poem_id}) - this is the main oracle for the user.
        2. Use the related poems and FAQs as supporting wisdom to enrich your interpretation.
        3. Consider the fortune level and symbolic meanings in the poems.
        4. Provide practical, constructive guidance that helps the user understand their situation.
        5. Be supportive and encouraging while maintaining traditional wisdom.
        6. Connect the poem's imagery and meaning to the user's specific question.
        7. Mention the temple name and poem number in your response for authenticity.
        8. {language_instruction}

        OUTPUT FORMAT REQUIREMENTS:
        - RETURN ONLY A SINGLE JSON OBJECT. Do not output any text before or after the JSON (no plain text headings, no extra commentary).
        - The JSON object MUST contain exactly **7 keys**, and they must appear in this order:
        1. "LineByLineInterpretation"
        2. "OverallDevelopment"
        3. "PositiveFactors"
        4. "Challenges"
        5. "SuggestedActions"
        6. "SupplementaryNotes"
        7. "Conclusion"
        - "LineByLineInterpretation" (the new/added key) must contain a multi-paragraph string that provides a **detailed line-by-line explanation** of the selected poem. It should:
        - Explicitly label each poem line (for example "Line 1:", "Line 2:", ...).
        - Connect each line's imagery to the user's question and situation.
        - Mention the temple name ({temple}) and poem number (#{poem_id}) somewhere within this text for authenticity.
        - Be allowed to be longer than 4–5 sentences (i.e., free-form, multi-paragraph).
        - The remaining six keys ("OverallDevelopment", "PositiveFactors", "Challenges", "SuggestedActions", "SupplementaryNotes", "Conclusion") must each contain a string of **4–5 sentences**, grounded in the selected poem and the user's question.
        - All content (including the full LineByLineInterpretation) must be inside the JSON string values — **no free text outside JSON**.
        - Ensure the JSON is valid and machine-readable (properly escaped, use double quotes for keys and strings).

        JSON SCHEMA (example descriptions only — output must follow these keys exactly):
        {{
        "LineByLineInterpretation": "Multi-paragraph line-by-line interpretation. Must label lines and connect imagery to the user's question. Include temple name and poem number.",
        "OverallDevelopment": "Describe the current situation or atmosphere, and explain the future trend or possible direction (short-term vs long-term). (4–5 sentences.)",
        "PositiveFactors": "Mention conditions, people, or resources that may help. Highlight internal strengths or external opportunities. (4–5 sentences.)",
        "Challenges": "Point out risks, blind spots, or difficulties. Identify factors that may slow down or block progress. (4–5 sentences.)",
        "SuggestedActions": "Practical advice: specific actions that can be taken. Mindset advice: attitudes to maintain (patience, courage, letting go, etc.). (4–5 sentences.)",
        "SupplementaryNotes": "If relevant, add extra insights depending on the type of question (e.g., love, career, health, wealth). (4–5 sentences.)",
        "Conclusion": "End with a short, reassuring message. (4–5 sentences.)"
        }}

        FINAL INSTRUCTION:
        Analyze the selected fortune poem step by step. Produce **only** the single JSON object described above (with "LineByLineInterpretation" as the first key) and follow the specified format exactly otherwise you will be *penalized*. Do not output any commentary or section headers outside the JSON.
        """



        try:
            interpretation = self.llm.generate(
                prompt,
                temperature=0.7,
                max_tokens=2000
            )
            
            return interpretation
            
        except Exception as e:
            self.logger.error(f"LLM generation failed: {e}")
            return f"I apologize, but I'm experiencing technical difficulties providing an interpretation right now. The {temple} temple poem #{poem_id} you've selected is significant and deserves proper attention. Please try again in a moment."
    
    def _get_language_instruction(self, user_language: str) -> str:
        """Get language-specific instruction for the LLM."""
        if user_language == "zh":
            return "請用繁體中文回答，保持傳統占卜的智慧和文化背景"
        elif user_language == "jp":
            return "日本語で回答してください。伝統的な占いの知恵と文化的背景を保持してください"
        else:
            return "Respond in English while maintaining the wisdom and cultural context of traditional divination"

# Factory for creating different types of interpreters
class InterpreterFactory:
    """Factory for creating interpreter instances."""
    
    @staticmethod
    def create_poem_interpreter(rag_handler: UnifiedRAGHandler, llm_client: BaseLLMClient, 
                              faq_pipeline: FAQPipeline) -> PoemInterpreter:
        """Create a poem interpreter instance."""
        return PoemInterpreter(rag_handler, llm_client, faq_pipeline)
    
    @staticmethod
    def create_custom_interpreter(interpreter_class: type, rag_handler: UnifiedRAGHandler, 
                                llm_client: BaseLLMClient, faq_pipeline: FAQPipeline):
        """Create a custom interpreter instance."""
        if not issubclass(interpreter_class, BaseInterpreter):
            raise ValueError("Custom interpreter must inherit from BaseInterpreter")
        
        return interpreter_class(rag_handler, llm_client, faq_pipeline)