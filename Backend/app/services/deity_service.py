"""
Deity Service - Maps UI deities to backend temple systems
"""

import logging
from typing import Dict, List, Optional

from app.schemas.deity import (
    DeityInfo, DeityResponse, DeityListResponse,
    Collection, NumberRange, CollectionNumbersResponse, FortuneNumber
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

    async def _generate_numbers_data(self, temple_name: str, start: int, end: int) -> List[FortuneNumber]:
        """Generate numbers data with availability status for a temple"""
        numbers = []

        try:
            # Get available poems from the temple to determine which numbers are available
            temple_stats = await poem_service.get_temple_stats(temple_name)

            # For now, we'll check if poems exist for each number
            # In a real system, this would query the actual poem database
            available_numbers = set()
            if temple_stats and temple_stats.total_poems > 0:
                # Assume first N numbers are available based on total poems
                for i in range(1, min(end + 1, temple_stats.total_poems + 1)):
                    available_numbers.add(i)
            else:
                # For demo purposes, mark some numbers as available even when no poems are loaded
                # This ensures the frontend can display the numbers grid properly
                for i in range(1, min(21, end + 1)):  # Mark first 20 numbers as available
                    available_numbers.add(i)

            # Generate numbers list
            for number in range(start, end + 1):
                is_available = number in available_numbers
                numbers.append(FortuneNumber(
                    number=number,
                    is_available=is_available,
                    fortune_category=None,  # Could be populated if we have category data
                    title=None  # Could be populated if we have title data
                ))

        except Exception as e:
            logger.warning(f"Error generating numbers data for {temple_name}: {e}")
            # Fallback: mark first 20 numbers as available for demo
            for number in range(start, end + 1):
                is_available = number <= 20  # First 20 numbers available
                numbers.append(FortuneNumber(
                    number=number,
                    is_available=is_available,
                    fortune_category=None,
                    title=None
                ))

        return numbers

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
                    end_number = min(100, total_fortunes)
                else:
                    # Fallback to standard 1-100 range
                    total_fortunes = 100
                    end_number = 100

                # Generate numbers data for this collection
                numbers_data = await self._generate_numbers_data(temple_name, 1, end_number)

                # Create collection for this deity
                collection = Collection(
                    id=f"{deity_id}_standard",
                    name="Standard Collection",
                    description=f"Traditional {total_fortunes} fortune poems",
                    number_range=NumberRange(start=1, end=end_number),
                    temple_mapping=temple_name,
                    numbers=numbers_data
                )

                deity = DeityInfo(
                    id=info["id"],
                    name=info["name"],
                    chinese_name=info["chinese_name"],
                    description=info["description"],
                    collections=[collection],
                    total_fortunes=total_fortunes,
                    deity_image_url=info["deity_image_url"]
                )

                deities.append(deity)

            return deities

        except Exception as e:
            logger.error(f"Error getting all deities: {e}")
            # Return fallback data with numbers
            fallback_deities = []
            for deity_id, info in self.deity_info.items():
                temple_name = self.deity_to_temple_mapping[deity_id]
                # Generate fallback numbers data
                fallback_numbers = [
                    FortuneNumber(
                        number=i,
                        is_available=i <= 20,  # First 20 numbers available for demo
                        fortune_category=None,
                        title=None
                    )
                    for i in range(1, 101)  # 1-100
                ]

                fallback_deities.append(DeityInfo(
                    id=deity_id,
                    name=info["name"],
                    chinese_name=info["chinese_name"],
                    description=info["description"],
                    collections=[Collection(
                        id=f"{deity_id}_standard",
                        name="Standard Collection",
                        description="Traditional 100 fortune poems",
                        number_range=NumberRange(start=1, end=100),
                        temple_mapping=temple_name,
                        numbers=fallback_numbers
                    )],
                    total_fortunes=100,
                    deity_image_url=info["deity_image_url"]
                ))

            return fallback_deities
    
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
                end_number = min(100, total_fortunes)
                fortune_categories = temple_stats.fortune_categories
            else:
                total_fortunes = 100
                end_number = 100
                fortune_categories = {"good_fortune": 50, "great_fortune": 30, "neutral": 20}

            # Get sample fortunes
            sample_fortunes = await self._get_sample_fortunes(temple_name, 3)

            # Create collection for this deity
            collection = Collection(
                id=f"{deity_id}_standard",
                name="Standard Collection",
                description=f"Traditional {total_fortunes} fortune poems",
                number_range=NumberRange(start=1, end=end_number),
                temple_mapping=temple_name
            )

            deity_info = DeityInfo(
                id=info["id"],
                name=info["name"],
                chinese_name=info["chinese_name"],
                description=info["description"],
                collections=[collection],
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
    
    async def get_deity_collections(self, deity_id: str) -> Optional[CollectionNumbersResponse]:
        """Get collection information for a deity"""
        if deity_id not in self.deity_info:
            return None

        try:
            temple_name = self.deity_to_temple_mapping[deity_id]
            info = self.deity_info[deity_id]

            # Get temple stats to determine available numbers
            temple_stats = await poem_service.get_temple_stats(temple_name)

            if temple_stats:
                total_fortunes = temple_stats.total_poems
                end_number = min(100, total_fortunes)
            else:
                total_fortunes = 100
                end_number = 100

            # Generate numbers data for this collection
            numbers_data = await self._generate_numbers_data(temple_name, 1, end_number)

            # Create collection for this deity
            collection = Collection(
                id=f"{deity_id}_standard",
                name="Standard Collection",
                description=f"Traditional {total_fortunes} fortune poems",
                number_range=NumberRange(start=1, end=end_number),
                temple_mapping=temple_name,
                numbers=numbers_data
            )

            return CollectionNumbersResponse(
                deity_id=deity_id,
                deity_name=info["name"],
                collections=[collection]
            )

        except Exception as e:
            logger.error(f"Error getting collections for deity {deity_id}: {e}")
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