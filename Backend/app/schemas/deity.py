"""
Pydantic schemas for deity-related API responses
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel


class NumberRange(BaseModel):
    """Number range representation"""
    start: int
    end: int


class FortuneNumber(BaseModel):
    """Individual fortune number information"""
    number: int
    is_available: bool
    fortune_category: Optional[str] = None
    title: Optional[str] = None


class Collection(BaseModel):
    """Fortune collection information"""
    id: str
    name: str
    description: str
    number_range: NumberRange
    temple_mapping: str
    numbers: List[FortuneNumber] = []  # Always include individual numbers


class DeityInfo(BaseModel):
    """Basic deity information"""
    id: str
    name: str
    chinese_name: str
    description: str
    collections: List[Collection]
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


class CollectionNumbersResponse(BaseModel):
    """Response for collection fortune numbers"""
    deity_id: str
    deity_name: str
    collections: List[Collection]