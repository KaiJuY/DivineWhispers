# interpreter.py
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import uuid
import re
import logging
import json
import time
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
    
    def _validate_interpretation_response(self, response: str, question: str = "", attempt: int = 0) -> tuple[bool, dict, str]:
        """Validate LLM interpretation response for completeness and quality.

        Args:
            response: The LLM response to validate
            question: The original question (for quality checks)
            attempt: The current attempt number

        Returns:
            (is_valid, parsed_data, error_message)
        """
        required_keys = [
            "LineByLineInterpretation",
            "OverallDevelopment",
            "PositiveFactors",
            "Challenges",
            "SuggestedActions",
            "SupplementaryNotes",
            "Conclusion"
        ]

        min_lengths = {
            "LineByLineInterpretation": 100,  # Detailed line-by-line needs more content
            "OverallDevelopment": 50,
            "PositiveFactors": 50,
            "Challenges": 50,
            "SuggestedActions": 50,
            "SupplementaryNotes": 30,
            "Conclusion": 30
        }

        try:
            # Step 1: Parse JSON
            response_clean = response.strip()
            if not response_clean.startswith('{') or not response_clean.endswith('}'):
                return False, {}, f"Response is not a valid JSON object (attempt {attempt + 1})"

            try:
                parsed = json.loads(response_clean)
            except json.JSONDecodeError as e:
                return False, {}, f"JSON parsing failed: {str(e)} (attempt {attempt + 1})"

            # Step 2: Check structure
            if not isinstance(parsed, dict):
                return False, {}, f"Response is not a JSON object (attempt {attempt + 1})"

            # Step 3: Check required keys
            missing_keys = [key for key in required_keys if key not in parsed]
            if missing_keys:
                return False, {}, f"Missing required keys: {missing_keys} (attempt {attempt + 1})"

            # Step 4: Check for empty or invalid values
            validation_errors = []
            for key in required_keys:
                value = parsed[key]

                # Check if value exists and is string
                if not isinstance(value, str):
                    validation_errors.append(f"{key}: not a string")
                    continue

                # Check if value is empty or whitespace
                if not value.strip():
                    validation_errors.append(f"{key}: empty or whitespace only")
                    continue

                # Check minimum length
                if len(value.strip()) < min_lengths[key]:
                    validation_errors.append(f"{key}: too short ({len(value.strip())} chars, min {min_lengths[key]})")
                    continue

            if validation_errors:
                return False, {}, f"Validation errors: {'; '.join(validation_errors)} (attempt {attempt + 1})"

            # Step 5: Enhanced Quality checks
            quality_issues = self._check_content_quality(parsed, question, attempt)
            if quality_issues:
                return False, {}, f"Content quality issues: {'; '.join(quality_issues)} (attempt {attempt + 1})"

            if validation_errors:
                return False, {}, f"Validation errors: {'; '.join(validation_errors)} (attempt {attempt + 1})"

            # Log detailed validation success metrics
            content_stats = {key: len(str(parsed.get(key, ""))) for key in required_keys}
            line_by_line = parsed.get("LineByLineInterpretation", "")
            self.logger.info(
                f"VALIDATION_SUCCESS: Response passed all validation checks",
                extra={
                    "attempt": attempt + 1,
                    "content_stats": content_stats,
                    "total_content_length": sum(content_stats.values()),
                    "has_line_structure": "Line 1:" in line_by_line or "第一句:" in line_by_line,
                    "metric_type": "validation_success"
                }
            )
            return True, parsed, ""

        except Exception as e:
            self.logger.error(f"Validation error on attempt {attempt + 1}: {e}")
            return False, {}, f"Validation exception: {str(e)} (attempt {attempt + 1})"

    def _check_content_quality(self, parsed: dict, question: str, attempt: int) -> List[str]:
        """Enhanced content quality validation to detect generic/fallback content."""
        quality_issues = []

        line_by_line = parsed.get("LineByLineInterpretation", "")

        # Check for actual line-by-line structure
        if "Line 1:" not in line_by_line and "第一句:" not in line_by_line and "Line" not in line_by_line:
            quality_issues.append("LineByLineInterpretation: missing proper line-by-line structure")

        # Detect fallback/generic content patterns
        fallback_indicators = [
            "Due to technical difficulties",
            "technical difficulties",
            "system difficulties",
            "cannot provide detailed",
            "simplified due to technical",
            "由於技術困難",
            "技術問題",
            "系統困難"
        ]

        fallback_count = sum(1 for indicator in fallback_indicators if indicator in line_by_line.lower())
        if fallback_count >= 2:  # Multiple fallback indicators suggest generic content
            quality_issues.append(f"LineByLineInterpretation: appears to be fallback content ({fallback_count} indicators)")

        # Language consistency check
        question_lang = self._detect_language(question)
        response_lang = self._detect_language(line_by_line[:200])  # Check first 200 chars

        if question_lang != response_lang:
            quality_issues.append(f"Language mismatch: question in {question_lang}, response in {response_lang}")

        # Check for overly generic content
        generic_phrases = [
            "this fortune contains",
            "wisdom guidance",
            "maintain patience",
            "step by step",
            "stay patient"
        ]

        generic_count = sum(1 for phrase in generic_phrases if phrase in line_by_line.lower())
        if generic_count >= 3:  # Too many generic phrases
            quality_issues.append(f"LineByLineInterpretation: overly generic content ({generic_count} generic phrases)")

        # Check other sections for fallback content
        for key in ["OverallDevelopment", "PositiveFactors", "Challenges", "SuggestedActions"]:
            content = parsed.get(key, "")
            fallback_in_section = sum(1 for indicator in fallback_indicators if indicator in content.lower())
            if fallback_in_section >= 1:
                quality_issues.append(f"{key}: contains fallback content")

        return quality_issues

    def _generate_interpretation(self, question: str, context: str, temple: str, poem_id: int) -> str:
        """Generate interpretation using LLM with validation and auto-retry."""

        # Detect user's language for response
        user_language = self._detect_language(question)
        language_instruction = self._get_language_instruction(user_language)

        max_attempts = 3
        last_error = ""

        for attempt in range(max_attempts):
            try:
                # Generate prompt with increasing strictness for retries
                prompt = self._create_interpretation_prompt(
                    question, context, temple, poem_id,
                    language_instruction, attempt
                )

                self.logger.info(f"LLM generation attempt {attempt + 1}/{max_attempts}")

                # Generate response with timeout
                response = self.llm.generate(
                    prompt,
                    temperature=0.7 - (attempt * 0.1),  # Reduce temperature for retries
                    max_tokens=2500 + (attempt * 500)  # Increase tokens for retries
                )

                # Validate response
                is_valid, parsed_data, error_msg = self._validate_interpretation_response(response, question, attempt)

                if is_valid:
                    # Log success metrics
                    self.logger.info(
                        f"SUCCESS: Valid interpretation generated",
                        extra={
                            "attempt": attempt + 1,
                            "temple": temple,
                            "poem_id": poem_id,
                            "question_length": len(question),
                            "response_length": len(response),
                            "user_language": user_language,
                            "validation_success": True,
                            "metric_type": "interpretation_success"
                        }
                    )
                    return response
                else:
                    last_error = error_msg
                    # Log validation failure metrics
                    self.logger.warning(
                        f"VALIDATION_FAILURE: Attempt {attempt + 1} failed validation",
                        extra={
                            "attempt": attempt + 1,
                            "temple": temple,
                            "poem_id": poem_id,
                            "error_message": error_msg,
                            "response_length": len(response) if response else 0,
                            "user_language": user_language,
                            "validation_success": False,
                            "metric_type": "validation_failure"
                        }
                    )

                    # Exponential backoff between retries
                    if attempt < max_attempts - 1:
                        wait_time = 2 ** attempt  # 1s, 2s, 4s
                        self.logger.info(f"Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)

            except Exception as e:
                last_error = f"LLM generation failed: {str(e)}"
                self.logger.error(f"LLM generation failed on attempt {attempt + 1}: {e}")

                if attempt < max_attempts - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)

        # All attempts failed - return structured fallback
        self.logger.error(
            f"CRITICAL_FAILURE: All {max_attempts} interpretation attempts failed",
            extra={
                "temple": temple,
                "poem_id": poem_id,
                "question_length": len(question),
                "total_attempts": max_attempts,
                "final_error": last_error,
                "user_language": user_language,
                "fallback_used": True,
                "metric_type": "interpretation_critical_failure"
            }
        )
        return self._create_fallback_response(question, temple, poem_id, user_language)

    def _create_interpretation_prompt(self, question: str, context: str, temple: str,
                                    poem_id: int, language_instruction: str, attempt: int) -> str:
        """Create interpretation prompt with increasing strictness for retries."""

        # Base strictness increases with attempts
        strictness_levels = [
            "CRITICAL REQUIREMENT",
            "ABSOLUTELY MANDATORY REQUIREMENT",
            "FINAL STRICT REQUIREMENT - NO EXCEPTIONS"
        ]

        strictness = strictness_levels[min(attempt, 2)]

        # Add extra validation reminders for retries
        extra_validation = ""
        if attempt > 0:
            extra_validation = f"""

        {strictness}: This is attempt #{attempt + 1}. Previous attempts failed validation.
        - ALL 7 keys must be present and non-empty
        - LineByLineInterpretation must be detailed (100+ characters) with "Line 1:", "Line 2:" format
        - Each section must have substantial content (50+ characters minimum)
        - JSON must be perfectly valid and parseable
        - NO empty strings or whitespace-only content
        FAILURE TO MEET THESE REQUIREMENTS WILL RESULT IN SYSTEM ERROR.
        """

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

        {extra_validation}

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

        return prompt

    def _create_fallback_response(self, question: str, temple: str, poem_id: int, language: str) -> str:
        """Create a structured fallback response when all LLM attempts fail."""

        fallback_content = {
            "zh": {
                "line_by_line": f"關於{temple}第{poem_id}號籤詩的逐句解釋：由於技術問題，我們無法提供詳細的逐句分析。請稍後重試獲得完整解讀。",
                "overall": "目前系統遇到技術困難，無法提供完整的運勢分析。建議您稍後重新諮詢，以獲得更準確的神明指引。",
                "positive": "儘管遇到技術問題，您尋求神明指引的誠心必將獲得回應。保持耐心和信心，答案終將顯現。",
                "challenges": "當前的挑戰包括技術系統的暫時性問題，但這不會影響神明對您的關愛和指引。",
                "actions": "建議稍後重新進行占卜諮詢。在等待期間，可以靜心思考您的問題，準備更清晰的提問。",
                "notes": "技術問題是暫時的，但神明的智慧是永恆的。請保持信心，稍後重試將獲得完整的指引。",
                "conclusion": "雖然遇到暫時困難，但您的問題很重要，值得完整的解答。請稍後重試，神明的智慧將為您指明道路。"
            },
            "en": {
                "line_by_line": f"Regarding the line-by-line interpretation of {temple} poem #{poem_id}: Due to technical difficulties, we cannot provide detailed line-by-line analysis at this moment. Please try again later for a complete reading.",
                "overall": "The system is currently experiencing technical difficulties preventing a complete fortune analysis. We recommend consulting again later for more accurate divine guidance.",
                "positive": "Despite technical issues, your sincere desire for divine guidance will be answered. Maintain patience and faith - answers will manifest in time.",
                "challenges": "Current challenges include temporary system issues, but these won't affect the divine care and guidance meant for you.",
                "actions": "We recommend retrying your divination consultation later. During this waiting period, contemplate your question quietly to prepare clearer inquiries.",
                "notes": "Technical issues are temporary, but divine wisdom is eternal. Please maintain faith and retry later for complete guidance.",
                "conclusion": "Though facing temporary difficulties, your question is important and deserves a complete answer. Please try again later - divine wisdom will illuminate your path."
            }
        }

        content = fallback_content.get(language, fallback_content["en"])

        fallback_response = {
            "LineByLineInterpretation": content["line_by_line"],
            "OverallDevelopment": content["overall"],
            "PositiveFactors": content["positive"],
            "Challenges": content["challenges"],
            "SuggestedActions": content["actions"],
            "SupplementaryNotes": content["notes"],
            "Conclusion": content["conclusion"]
        }

        return json.dumps(fallback_response, ensure_ascii=False, indent=2)
        
        # This method is now implemented above with comprehensive validation and retry logic
    
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