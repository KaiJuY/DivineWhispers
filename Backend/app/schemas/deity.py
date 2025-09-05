"""
Pydantic schemas for deity-related API responses
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel


class DeityInfo(BaseModel):
    """Basic deity information"""
    id: str
    name: str
    chinese_name: str
    description: str
    temple_mapping: str  # Maps to actual temple in the backend
    available_numbers: List[int]
    total_fortunes: int
    deity_image_url: Optional[str] = None
    

class DeityResponse(BaseModel):
    """Detailed deity response"""
    deity: DeityInfo
    fortune_categories: Dict[str, int]  # e.g., {"great_fortune": 20, "good_fortune": 30}
    sample_fortunes: List[str]  # Sample fortune titles


class DeityListResponse(BaseModel):
    """List of all deities response"""
    deities: List[DeityInfo]
    total_count: int


class FortuneNumberInfo(BaseModel):
    """Information about a specific fortune number"""
    number: int
    is_available: bool
    fortune_category: Optional[str] = None
    title: Optional[str] = None


class FortuneNumbersResponse(BaseModel):
    """Response for deity fortune numbers (1-100 grid)"""
    deity_id: str
    deity_name: str
    numbers: List[FortuneNumberInfo]  # All numbers 1-100
    total_available: int