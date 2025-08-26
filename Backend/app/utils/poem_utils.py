"""
Poem processing utilities for the Fortune System
"""

import hashlib
import json
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import logging

logger = logging.getLogger(__name__)


def generate_poem_id(temple: str, poem_id: int, section: str = "main") -> str:
    """Generate a unique poem chunk ID"""
    return f"poem_{temple}_{poem_id}_{section}"


def generate_content_hash(content: str) -> str:
    """Generate a hash for content identification"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()[:8]


def extract_poem_content(poem_data: Dict) -> Dict[str, str]:
    """
    Extract and format poem content for different languages
    
    Args:
        poem_data: Raw poem data from JSON file
        
    Returns:
        Dict with formatted content for each language
    """
    formatted_content = {}
    
    try:
        # Basic poem info
        title = poem_data.get("title", "")
        fortune = poem_data.get("fortune", "")
        poem_text = poem_data.get("poem", "")
        analysis = poem_data.get("analysis", {})
        
        # Create formatted content for each language
        languages = ["zh", "en", "jp"]
        
        for lang in languages:
            if lang in analysis:
                content_parts = [
                    f"Title: {title}",
                    f"Fortune: {fortune}",
                    f"Poem: {poem_text}",
                    f"Analysis: {analysis[lang]}"
                ]
                formatted_content[lang] = "\n\n".join(content_parts)
        
        # If no language-specific analysis, create generic content
        if not formatted_content:
            base_content = f"Title: {title}\nFortune: {fortune}\nPoem: {poem_text}"
            formatted_content["zh"] = base_content
            
    except Exception as e:
        logger.error(f"Error formatting poem content: {e}")
        # Fallback content
        formatted_content["zh"] = str(poem_data)
    
    return formatted_content


def validate_poem_data(poem_data: Dict) -> bool:
    """
    Validate poem data structure
    
    Args:
        poem_data: Poem data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["id", "title", "fortune", "poem"]
    
    try:
        # Check required fields
        for field in required_fields:
            if field not in poem_data or not poem_data[field]:
                logger.warning(f"Missing or empty required field: {field}")
                return False
        
        # Check analysis structure
        if "analysis" in poem_data:
            analysis = poem_data["analysis"]
            if not isinstance(analysis, dict):
                logger.warning("Analysis field must be a dictionary")
                return False
            
            # Check if at least one language analysis exists
            valid_languages = ["zh", "en", "jp"]
            has_valid_analysis = any(
                lang in analysis and analysis[lang] 
                for lang in valid_languages
            )
            
            if not has_valid_analysis:
                logger.warning("No valid language analysis found")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating poem data: {e}")
        return False


def normalize_temple_name(temple_name: str) -> str:
    """
    Normalize temple name for consistent storage
    
    Args:
        temple_name: Raw temple name
        
    Returns:
        Normalized temple name
    """
    # Convert to lowercase and replace spaces with underscores
    normalized = re.sub(r'[^\w\s-]', '', temple_name.lower())
    normalized = re.sub(r'[-\s]+', '_', normalized)
    return normalized.strip('_')


def parse_fortune_type(fortune_str: str) -> str:
    """
    Parse and normalize fortune type
    
    Args:
        fortune_str: Raw fortune string
        
    Returns:
        Normalized fortune type
    """
    # Common fortune types mapping
    fortune_mapping = {
        "大吉": "great_fortune",
        "中吉": "good_fortune", 
        "小吉": "small_fortune",
        "吉": "fortune",
        "平": "neutral",
        "凶": "bad_fortune",
        "大凶": "great_misfortune"
    }
    
    # Try direct mapping first
    if fortune_str in fortune_mapping:
        return fortune_mapping[fortune_str]
    
    # Try partial matching
    for chinese, english in fortune_mapping.items():
        if chinese in fortune_str:
            return english
    
    # Default to original if no mapping found
    return fortune_str


def load_poem_from_file(file_path: Path) -> Optional[Dict]:
    """
    Load poem data from JSON file with error handling
    
    Args:
        file_path: Path to poem JSON file
        
    Returns:
        Poem data dictionary or None if error
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if validate_poem_data(data):
            return data
        else:
            logger.warning(f"Invalid poem data in file: {file_path}")
            return None
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {e}")
        return None
    except FileNotFoundError:
        logger.error(f"Poem file not found: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error loading poem file {file_path}: {e}")
        return None


def get_random_poem_selection(poems: List[Dict], count: int = 1) -> List[Dict]:
    """
    Get random selection of poems with weighted selection by fortune type
    
    Args:
        poems: List of poem dictionaries
        count: Number of poems to select
        
    Returns:
        List of randomly selected poems
    """
    if not poems or count <= 0:
        return []
    
    if len(poems) <= count:
        return poems.copy()
    
    # Implement weighted selection favoring positive fortunes
    fortune_weights = {
        "great_fortune": 3.0,
        "good_fortune": 2.5,
        "small_fortune": 2.0,
        "fortune": 1.5,
        "neutral": 1.0,
        "bad_fortune": 0.7,
        "great_misfortune": 0.3
    }
    
    # Calculate weights for each poem
    weighted_poems = []
    for poem in poems:
        fortune_type = parse_fortune_type(poem.get("fortune", ""))
        weight = fortune_weights.get(fortune_type, 1.0)
        weighted_poems.append((poem, weight))
    
    # Random selection with weights
    selected = []
    available_poems = weighted_poems.copy()
    
    for _ in range(count):
        if not available_poems:
            break
            
        # Calculate total weight
        total_weight = sum(weight for _, weight in available_poems)
        
        # Random selection
        r = random.uniform(0, total_weight)
        current_weight = 0
        
        for i, (poem, weight) in enumerate(available_poems):
            current_weight += weight
            if r <= current_weight:
                selected.append(poem)
                available_poems.pop(i)
                break
    
    return selected


def format_poem_for_llm_context(poem_data: Dict, language: str = "zh") -> str:
    """
    Format poem data for LLM context
    
    Args:
        poem_data: Poem data dictionary
        language: Target language for formatting
        
    Returns:
        Formatted poem text for LLM context
    """
    try:
        title = poem_data.get("title", "Unknown Title")
        fortune = poem_data.get("fortune", "Unknown Fortune")
        poem_text = poem_data.get("poem", "")
        analysis = poem_data.get("analysis", {})
        
        # Build context string
        context_parts = [
            f"**Poem Title**: {title}",
            f"**Fortune Level**: {fortune}",
            f"**Poem Text**:\n{poem_text}",
        ]
        
        # Add language-specific analysis if available
        if language in analysis and analysis[language]:
            context_parts.append(f"**Traditional Analysis**:\n{analysis[language]}")
        elif "zh" in analysis:  # Fallback to Chinese
            context_parts.append(f"**Traditional Analysis**:\n{analysis['zh']}")
        
        return "\n\n".join(context_parts)
        
    except Exception as e:
        logger.error(f"Error formatting poem for LLM: {e}")
        return f"Poem: {poem_data.get('title', 'Unknown')}"


def create_poem_embedding_content(poem_data: Dict, language: str = "zh") -> str:
    """
    Create content string optimized for embedding generation
    
    Args:
        poem_data: Poem data dictionary
        language: Target language
        
    Returns:
        Content string for embedding
    """
    try:
        content_parts = []
        
        # Add core poem content
        if poem_data.get("title"):
            content_parts.append(poem_data["title"])
        
        if poem_data.get("poem"):
            content_parts.append(poem_data["poem"])
        
        # Add analysis for the specified language
        analysis = poem_data.get("analysis", {})
        if language in analysis and analysis[language]:
            content_parts.append(analysis[language])
        
        return " ".join(content_parts)
        
    except Exception as e:
        logger.error(f"Error creating embedding content: {e}")
        return poem_data.get("title", "Unknown Poem")


def calculate_poem_similarity_score(poem1: Dict, poem2: Dict) -> float:
    """
    Calculate similarity score between two poems based on fortune type and content
    
    Args:
        poem1: First poem dictionary
        poem2: Second poem dictionary
        
    Returns:
        Similarity score between 0 and 1
    """
    try:
        score = 0.0
        
        # Fortune type similarity (40% weight)
        fortune1 = parse_fortune_type(poem1.get("fortune", ""))
        fortune2 = parse_fortune_type(poem2.get("fortune", ""))
        
        if fortune1 == fortune2:
            score += 0.4
        elif abs(get_fortune_score(fortune1) - get_fortune_score(fortune2)) <= 1:
            score += 0.2
        
        # Content similarity (30% weight) - simple keyword overlap
        content1 = poem1.get("poem", "").lower()
        content2 = poem2.get("poem", "").lower()
        
        words1 = set(content1.split())
        words2 = set(content2.split())
        
        if words1 and words2:
            overlap = len(words1.intersection(words2))
            union = len(words1.union(words2))
            content_similarity = overlap / union if union > 0 else 0
            score += 0.3 * content_similarity
        
        # Temple similarity (30% weight) - poems from same temple are more similar
        if poem1.get("temple") == poem2.get("temple"):
            score += 0.3
        
        return min(score, 1.0)
        
    except Exception as e:
        logger.error(f"Error calculating poem similarity: {e}")
        return 0.0


def get_fortune_score(fortune_type: str) -> int:
    """
    Get numerical score for fortune type (for similarity calculation)
    
    Args:
        fortune_type: Fortune type string
        
    Returns:
        Numerical score (higher = better fortune)
    """
    scores = {
        "great_fortune": 5,
        "good_fortune": 4,
        "small_fortune": 3,
        "fortune": 3,
        "neutral": 2,
        "bad_fortune": 1,
        "great_misfortune": 0
    }
    
    return scores.get(fortune_type, 2)  # Default to neutral


def detect_poem_themes(poem_text: str) -> List[str]:
    """
    Detect themes in poem text using keyword matching
    
    Args:
        poem_text: Poem text to analyze
        
    Returns:
        List of detected themes
    """
    theme_keywords = {
        "love": ["愛", "情", "戀", "夫", "妻", "marriage", "love", "relationship"],
        "career": ["事業", "工作", "職", "business", "career", "work", "job"],
        "health": ["健康", "病", "醫", "health", "illness", "medicine"],
        "wealth": ["財", "錢", "富", "money", "wealth", "fortune", "rich"],
        "family": ["家", "親", "children", "family", "relatives"],
        "travel": ["行", "遊", "旅", "travel", "journey", "trip"],
        "education": ["學", "教", "書", "study", "education", "learning"],
        "spiritual": ["神", "佛", "道", "spiritual", "divine", "religious"]
    }
    
    detected_themes = []
    poem_lower = poem_text.lower()
    
    for theme, keywords in theme_keywords.items():
        if any(keyword in poem_lower for keyword in keywords):
            detected_themes.append(theme)
    
    return detected_themes


def generate_search_suggestions(query: str, available_poems: List[Dict]) -> List[str]:
    """
    Generate search suggestions based on query and available poems
    
    Args:
        query: User search query
        available_poems: List of available poem dictionaries
        
    Returns:
        List of search suggestions
    """
    suggestions = set()
    query_lower = query.lower()
    
    # Extract common terms from poems
    for poem in available_poems[:100]:  # Limit for performance
        title = poem.get("title", "").lower()
        poem_text = poem.get("poem", "").lower()
        
        # Add title words
        title_words = [word for word in title.split() if len(word) > 2]
        suggestions.update(title_words[:3])
        
        # Add poem keywords
        poem_words = [word for word in poem_text.split() if len(word) > 2]
        suggestions.update(poem_words[:2])
    
    # Filter and rank suggestions
    filtered_suggestions = []
    for suggestion in suggestions:
        if query_lower in suggestion or suggestion in query_lower:
            filtered_suggestions.append(suggestion)
    
    return list(filtered_suggestions)[:5]  # Return top 5 suggestions