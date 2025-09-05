"""
Deity API endpoints for Divine Whispers
Provides deity-to-temple mapping and fortune selection services
"""

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas.deity import (
    DeityResponse, DeityListResponse, FortuneNumbersResponse
)
from app.services.deity_service import deity_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/deities", tags=["Deities"])


@router.get("", response_model=DeityListResponse)
async def get_deities():
    """
    Get list of all available deities with their temple mappings
    This endpoint provides the mapping needed for the frontend deity selection UI
    """
    try:
        deities = await deity_service.get_all_deities()
        
        return DeityListResponse(
            deities=deities,
            total_count=len(deities)
        )
        
    except Exception as e:
        logger.error(f"Error getting deities: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{deity_id}", response_model=DeityResponse)
async def get_deity_details(deity_id: str):
    """
    Get detailed information about a specific deity
    """
    try:
        deity = await deity_service.get_deity_by_id(deity_id)
        
        if not deity:
            raise HTTPException(status_code=404, detail="Deity not found")
        
        return deity
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting deity {deity_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{deity_id}/numbers", response_model=FortuneNumbersResponse)
async def get_deity_fortune_numbers(deity_id: str):
    """
    Get available fortune numbers for a specific deity
    Returns the 1-100 grid data needed for the fortune selection UI
    """
    try:
        numbers_data = await deity_service.get_deity_fortune_numbers(deity_id)
        
        if not numbers_data:
            raise HTTPException(status_code=404, detail="Deity not found or no fortunes available")
        
        return numbers_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting fortune numbers for deity {deity_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")