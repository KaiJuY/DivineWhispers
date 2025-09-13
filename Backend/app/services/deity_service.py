"""
Deity Service - Maps UI deities to backend temple systems
"""

import logging
from typing import Dict, List, Optional

from app.schemas.deity import (
    DeityInfo, DeityResponse, DeityListResponse, 
    FortuneNumberInfo, FortuneNumbersResponse
)
from app.services.poem_service import poem_service
from app.utils.poem_utils import parse_fortune_type

logger = logging.getLogger(__name__)


class DeityService:
    """Service for managing deity-to-temple mappings and fortune data"""
    
    def __init__(self):
        # Maps UI deity IDs to backend temple names
        self.deity_to_temple_mapping = {
            "guan_yin": "GuanYin100",
            "mazu": "Mazu", 
            "guan_yu": "GuanYu",
            "yue_lao": "YueLao",
            "zhu_sheng": "Zhusheng",
            "asakusa": "Asakusa",
            "erawan_shrine": "ErawanShrine"
        }
        
        # UI deity information
        self.deity_info = {
            "guan_yin": {
                "id": "guan_yin",
                "name": "Guan Yin",
                "chinese_name": "觀音",
                "description": "Goddess of Mercy and Compassion. Provides guidance for life decisions, relationships, and spiritual growth.",
                "deity_image_url": "/assets/GuanYin.jpg"
            },
            "mazu": {
                "id": "mazu",
                "name": "Mazu",
                "chinese_name": "媽祖",
                "description": "Sea Goddess and protector of fishermen. Offers guidance for travel, safety, and protection.",
                "deity_image_url": "/assets/Mazu.png"
            },
            "guan_yu": {
                "id": "guan_yu",
                "name": "Guan Yu",
                "chinese_name": "關羽",
                "description": "God of War, Loyalty, and Justice. Provides counsel on business, loyalty, and righteous decisions.",
                "deity_image_url": "/assets/GuanYu.jpg"
            },
            "yue_lao": {
                "id": "yue_lao",
                "name": "Yue Lao",
                "chinese_name": "月老",
                "description": "God of Love and Marriage. Specializes in matters of romance, relationships, and matchmaking.",
                "deity_image_url": "/assets/YueLao.png"
            },
            "zhu_sheng": {
                "id": "zhu_sheng",
                "name": "Zhu Sheng",
                "chinese_name": "朱聖",
                "description": "Patron of Students and Learning. Offers guidance for academic success and career advancement.",
                "deity_image_url": "/assets/TheGoddessofChildBirth.jpg"
            },
            "asakusa": {
                "id": "asakusa",
                "name": "Asakusa Kannon",
                "chinese_name": "淺草觀音",
                "description": "Buddhist temple deity. Provides wisdom for general life guidance and spiritual enlightenment.",
                "deity_image_url": "/assets/Asakusa.jpg"
            },
            "erawan_shrine": {
                "id": "erawan_shrine",
                "name": "Erawan Shrine",
                "chinese_name": "四面佛",
                "description": "Four-faced Buddha. Offers comprehensive guidance covering love, career, health, and fortune.",
                "deity_image_url": "/assets/ErawanShrine.jpg"
            }
        }
    
    async def get_all_deities(self) -> List[DeityInfo]:
        """Get list of all available deities with their information"""
        try:
            deities = []
            
            for deity_id, info in self.deity_info.items():
                temple_name = self.deity_to_temple_mapping[deity_id]
                
                # Get temple stats to determine available numbers
                temple_stats = await poem_service.get_temple_stats(temple_name)
                
                if temple_stats:
                    total_fortunes = temple_stats.total_poems
                    available_numbers = list(range(1, min(101, total_fortunes + 1)))
                else:
                    # Fallback to standard 1-100 range
                    total_fortunes = 100
                    available_numbers = list(range(1, 101))
                
                deity = DeityInfo(
                    id=info["id"],
                    name=info["name"],
                    chinese_name=info["chinese_name"], 
                    description=info["description"],
                    temple_mapping=temple_name,
                    available_numbers=available_numbers,
                    total_fortunes=total_fortunes,
                    deity_image_url=info["deity_image_url"]
                )
                
                deities.append(deity)
            
            return deities
            
        except Exception as e:
            logger.error(f"Error getting all deities: {e}")
            # Return fallback data
            return [
                DeityInfo(
                    id=deity_id,
                    name=info["name"],
                    chinese_name=info["chinese_name"],
                    description=info["description"], 
                    temple_mapping=self.deity_to_temple_mapping[deity_id],
                    available_numbers=list(range(1, 101)),
                    total_fortunes=100,
                    deity_image_url=info["deity_image_url"]
                )
                for deity_id, info in self.deity_info.items()
            ]
    
    async def get_deity_by_id(self, deity_id: str) -> Optional[DeityResponse]:
        """Get detailed information about a specific deity"""
        if deity_id not in self.deity_info:
            return None
        
        try:
            temple_name = self.deity_to_temple_mapping[deity_id]
            info = self.deity_info[deity_id]
            
            # Get temple statistics 
            temple_stats = await poem_service.get_temple_stats(temple_name)
            
            if temple_stats:
                total_fortunes = temple_stats.total_poems
                available_numbers = list(range(1, min(101, total_fortunes + 1)))
                fortune_categories = temple_stats.fortune_categories
            else:
                total_fortunes = 100
                available_numbers = list(range(1, 101))
                fortune_categories = {"good_fortune": 50, "great_fortune": 30, "neutral": 20}
            
            # Get sample fortunes
            sample_fortunes = await self._get_sample_fortunes(temple_name, 3)
            
            deity_info = DeityInfo(
                id=info["id"],
                name=info["name"],
                chinese_name=info["chinese_name"],
                description=info["description"],
                temple_mapping=temple_name,
                available_numbers=available_numbers,
                total_fortunes=total_fortunes,
                deity_image_url=info["deity_image_url"]
            )
            
            return DeityResponse(
                deity=deity_info,
                fortune_categories=fortune_categories,
                sample_fortunes=sample_fortunes
            )
            
        except Exception as e:
            logger.error(f"Error getting deity {deity_id}: {e}")
            return None
    
    async def get_deity_fortune_numbers(self, deity_id: str) -> Optional[FortuneNumbersResponse]:
        """Get available fortune numbers (1-100 grid) for a deity"""
        if deity_id not in self.deity_info:
            return None
            
        try:
            temple_name = self.deity_to_temple_mapping[deity_id]
            info = self.deity_info[deity_id]
            
            # Get all poems for this temple to determine availability
            poems = await poem_service.search_similar_poems(
                query="", 
                top_k=100,
                temple_filter=temple_name
            )
            
            # Create mapping of available poem numbers
            available_poem_numbers = set()
            poem_info_map = {}
            
            for poem in poems:
                poem_num = poem.poem_id
                if 1 <= poem_num <= 100:
                    available_poem_numbers.add(poem_num)
                    poem_info_map[poem_num] = {
                        "fortune_category": parse_fortune_type(poem.fortune),
                        "title": poem.title
                    }
            
            # Generate the 1-100 grid
            numbers = []
            for num in range(1, 101):
                is_available = num in available_poem_numbers
                poem_info = poem_info_map.get(num, {})
                
                number_info = FortuneNumberInfo(
                    number=num,
                    is_available=is_available,
                    fortune_category=poem_info.get("fortune_category") if is_available else None,
                    title=poem_info.get("title") if is_available else None
                )
                numbers.append(number_info)
            
            return FortuneNumbersResponse(
                deity_id=deity_id,
                deity_name=info["name"],
                numbers=numbers,
                total_available=len(available_poem_numbers)
            )
            
        except Exception as e:
            logger.error(f"Error getting fortune numbers for deity {deity_id}: {e}")
            return None
    
    async def _get_sample_fortunes(self, temple_name: str, count: int = 3) -> List[str]:
        """Get sample fortune titles from a temple"""
        try:
            poems = await poem_service.search_similar_poems(
                query="fortune guidance", 
                top_k=count,
                temple_filter=temple_name
            )
            
            return [poem.title for poem in poems if poem.title]
            
        except Exception:
            return [
                "Ancient wisdom guides your path",
                "Fortune favors the prepared mind", 
                "Balance brings harmony to life"
            ]
    
    def get_temple_name(self, deity_id: str) -> Optional[str]:
        """Get backend temple name for a deity ID"""
        return self.deity_to_temple_mapping.get(deity_id)


# Global service instance
deity_service = DeityService()