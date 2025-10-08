# schemas.py
"""Pydantic schemas for OpenAI structured output (response_format)"""

from pydantic import BaseModel, Field


class FortuneInterpretation(BaseModel):
    """Structured schema for OpenAI API response_format.

    This schema ensures OpenAI returns properly structured fortune interpretations
    matching our 7-section format.
    """

    LineByLineInterpretation: str = Field(
        ...,
        description=(
            "Multi-paragraph line-by-line interpretation. "
            "Must label each poem line (e.g., 'Line 1:', 'Line 2:') and connect imagery to the user's question. "
            "Include temple name and poem number for authenticity. "
            "Minimum 100 characters."
        ),
        min_length=100
    )

    OverallDevelopment: str = Field(
        ...,
        description=(
            "Describe the current situation or atmosphere, and explain the future trend or possible direction "
            "(short-term vs long-term). Should be 4-5 sentences providing comprehensive situational analysis."
        ),
        min_length=50
    )

    PositiveFactors: str = Field(
        ...,
        description=(
            "Mention conditions, people, or resources that may help. "
            "Highlight internal strengths or external opportunities. "
            "Should be 4-5 sentences."
        ),
        min_length=50
    )

    Challenges: str = Field(
        ...,
        description=(
            "Point out risks, blind spots, or difficulties. "
            "Identify factors that may slow down or block progress. "
            "Should be 4-5 sentences."
        ),
        min_length=50
    )

    SuggestedActions: str = Field(
        ...,
        description=(
            "Practical advice: specific actions that can be taken. "
            "Mindset advice: attitudes to maintain (patience, courage, letting go, etc.). "
            "Should be 4-5 sentences."
        ),
        min_length=50
    )

    SupplementaryNotes: str = Field(
        ...,
        description=(
            "If relevant, add extra insights depending on the type of question "
            "(e.g., love, career, health, wealth). Should be 4-5 sentences."
        ),
        min_length=30
    )

    Conclusion: str = Field(
        ...,
        description="End with a short, reassuring message. Should be 4-5 sentences.",
        min_length=30
    )

    class Config:
        # Example for documentation
        json_schema_extra = {
            "example": {
                "LineByLineInterpretation": "Line 1: The poem speaks of clouds parting to reveal the sun...",
                "OverallDevelopment": "Your current situation shows signs of gradual improvement...",
                "PositiveFactors": "You possess the inner strength and wisdom needed...",
                "Challenges": "Be aware of potential obstacles that may arise...",
                "SuggestedActions": "Take deliberate steps forward with confidence...",
                "SupplementaryNotes": "In matters of career, this fortune suggests...",
                "Conclusion": "Trust in the guidance provided and maintain your faith..."
            }
        }
