"""
Fortune-telling related Pydantic schemas
"""

from datetime import datetime
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class PoemData(BaseModel):
    """Fortune poem data structure"""
    id: str = Field(..., description="Unique poem identifier")
    temple: str = Field(..., description="Temple name")
    poem_id: int = Field(..., description="Numerical poem ID")
    title: str = Field(..., description="Poem title")
    fortune: str = Field(..., description="Fortune level (大吉, 中吉, etc.)")
    poem: str = Field(..., description="The actual poem text")
    analysis: Dict[str, str] = Field(..., description="Multi-language analysis")
    

class PoemSearchQuery(BaseModel):
    """Poem search query parameters"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    temple: Optional[str] = Field(None, description="Filter by temple name")
    fortune_type: Optional[str] = Field(None, description="Filter by fortune type")
    limit: Optional[int] = Field(10, ge=1, le=50, description="Maximum results to return")


class PoemSearchResult(BaseModel):
    """Single poem search result"""
    temple: str
    poem_id: int
    title: str
    fortune: str
    relevance_score: float
    snippet: str = Field(..., description="Relevant text snippet")


class PoemSearchResponse(BaseModel):
    """Poem search response"""
    query: str
    results: List[PoemSearchResult]
    total_found: int
    search_time_ms: int


class FortuneDrawRequest(BaseModel):
    """Request for fortune drawing"""
    question: Optional[str] = Field(None, max_length=1000, description="Optional question for context")
    temple_preference: Optional[str] = Field(None, description="Preferred temple (optional)")
    language: str = Field("zh", description="Preferred language for interpretation")
    
    @validator("language")
    def validate_language(cls, v):
        if v not in ["zh", "en", "jp"]:
            raise ValueError("Language must be one of: zh, en, jp")
        return v


class FortuneInterpretRequest(BaseModel):
    """Request for specific poem interpretation"""
    poem_id: str = Field(..., description="Specific poem ID to interpret")
    question: str = Field(..., min_length=1, max_length=1000, description="User's question")
    language: str = Field("zh", description="Preferred language for interpretation")
    additional_context: Optional[str] = Field(None, max_length=500, description="Additional context")
    
    @validator("language")
    def validate_language(cls, v):
        if v not in ["zh", "en", "jp"]:
            raise ValueError("Language must be one of: zh, en, jp")
        return v


class FortuneJobResponse(BaseModel):
    """Response for fortune job creation"""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status")
    estimated_completion_time: int = Field(..., description="Estimated completion time in seconds")
    points_charged: int = Field(..., description="Points deducted for this service")
    message: str = Field(..., description="Status message")


class FortuneResult(BaseModel):
    """Complete fortune interpretation result"""
    poem: PoemData
    interpretation: str = Field(..., description="Personalized interpretation")
    confidence: float = Field(..., ge=0, le=1, description="Interpretation confidence score")
    additional_sources: List[str] = Field(default=[], description="Additional source references")
    temple_sources: List[str] = Field(default=[], description="Contributing temples")
    generated_at: datetime
    language: str
    job_id: str


class FortuneCategoryResponse(BaseModel):
    """Fortune categories list"""
    categories: List[str] = Field(..., description="Available fortune categories")
    category_counts: Dict[str, int] = Field(..., description="Count of poems per category")


class TempleStatsResponse(BaseModel):
    """Temple statistics response"""
    temple_name: str
    total_poems: int
    fortune_categories: Dict[str, int]
    languages_available: List[str]


class FortuneSystemHealthResponse(BaseModel):
    """Fortune system health check response"""
    chroma_db_status: str
    total_poems: int
    total_temples: int
    last_updated: Optional[datetime]
    cache_status: str
    system_load: str


class FortuneHistoryEntry(BaseModel):
    """User's fortune history entry"""
    job_id: str
    poem_id: str
    temple: str
    question: str
    created_at: datetime
    status: str
    points_cost: int


class FortuneHistoryResponse(BaseModel):
    """User's fortune history"""
    entries: List[FortuneHistoryEntry]
    total_count: int
    total_points_spent: int


class PoemDetailResponse(BaseModel):
    """Detailed poem information"""
    poem: PoemData
    related_poems: List[PoemSearchResult] = Field(default=[], description="Similar poems")
    interpretation_count: int = Field(0, description="How many times this poem has been interpreted")
    average_rating: Optional[float] = Field(None, description="Average user rating")


class FortuneAdminStatsResponse(BaseModel):
    """Admin statistics for fortune system"""
    total_poems_in_db: int
    total_temples: int
    total_interpretations_generated: int
    average_interpretation_time_ms: int
    popular_temples: Dict[str, int]
    popular_fortune_types: Dict[str, int]
    system_performance: Dict[str, Union[str, int, float]]
    chroma_db_health: Dict[str, Union[str, int]]


# Error response schemas
class FortuneErrorResponse(BaseModel):
    """Fortune service error response"""
    error_code: str
    message: str
    details: Optional[Dict] = None


class InsufficientPointsError(FortuneErrorResponse):
    """Insufficient points error"""
    error_code: str = "INSUFFICIENT_POINTS"
    required_points: int
    current_points: int


class PoemNotFoundError(FortuneErrorResponse):
    """Poem not found error"""
    error_code: str = "POEM_NOT_FOUND"
    poem_id: str


class SystemUnavailableError(FortuneErrorResponse):
    """System unavailable error"""
    error_code: str = "SYSTEM_UNAVAILABLE"
    retry_after_seconds: Optional[int] = None