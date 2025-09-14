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
                "description": ["The Goddess", "of", "Mercy"],
                "deity_image_url": "/assets/GuanYin.jpg"
            },
            "mazu": {
                "id": "mazu",
                "name": "Mazu",
                "chinese_name": "媽祖",
                "description": ["The Goddess", "of", "The sea"],
                "deity_image_url": "/assets/Mazu.png"
            },
            "guan_yu": {
                "id": "guan_yu",
                "name": "Guan Yu",
                "chinese_name": "關羽",
                "description": ["The God", "of", "War and Wealth"],
                "deity_image_url": "/assets/GuanYu.jpg"
            },
            "yue_lao": {
                "id": "yue_lao",
                "name": "Yue Lao",
                "chinese_name": "月老",
                "description": ["The God", "of", "Marriage"],
                "deity_image_url": "/assets/YueLao.png"
            },
            "zhu_sheng": {
                "id": "zhu_sheng",
                "name": "Zhu Sheng",
                "chinese_name": "註生娘娘",
                "description": ["The Goddess", "of", "Child Birth"],
                "deity_image_url": "/assets/TheGoddessofChildBirth.jpg"
            },
            "asakusa": {
                "id": "asakusa",
                "name": "Asakusa Kannon",
                "chinese_name": "淺草觀音",
                "description": ["Buddhist Temple"],
                "deity_image_url": "/assets/Asakusa.jpg"
            },
            "erawan_shrine": {
                "id": "erawan_shrine",
                "name": "Erawan Shrine",
                "chinese_name": "四面佛",
                "description": ["Buddhist Temple"],
                "deity_image_url": "/assets/ErawanShrine.jpg"
            }
        }


    async def get_all_deities(self) -> List[DeityInfo]:
        """Get list of all available deities with their information"""
        try:
            deities = []

            # Performance Optimization: Skip expensive poem_service calls
            # Since all temples currently return 0 poems, use static data for speed
            # TODO: Add cache layer when temples have actual poems

            # Process each deity using static configuration
            for deity_id, info in self.deity_info.items():
                temple_name = self.deity_to_temple_mapping[deity_id]

                # Static configuration for fast response
                total_fortunes = 100
                end_number = 100

                # Create collection for this deity (no numbers array needed)
                collection = Collection(
                    id=f"{deity_id}_standard",
                    name="Standard Collection",
                    description=f"Traditional {total_fortunes} fortune poems",
                    number_range=NumberRange(start=1, end=end_number),
                    temple_mapping=temple_name
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
            # Return fallback data
            fallback_deities = []
            for deity_id, info in self.deity_info.items():
                temple_name = self.deity_to_temple_mapping[deity_id]

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
                        temple_mapping=temple_name
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

            # Performance Optimization: Use static data instead of expensive poem_service calls
            # Since all temples currently return 0 poems, use static data for speed
            total_fortunes = 100
            end_number = 100
            fortune_categories = {"good_fortune": 50, "great_fortune": 30, "neutral": 20}

            # Static sample fortunes instead of expensive search
            sample_fortunes = [
                "Ancient wisdom guides your path",
                "Fortune favors the prepared mind",
                "Balance brings harmony to life"
            ]

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

            # Performance Optimization: Use static data instead of expensive poem_service calls
            # Since all temples currently return 0 poems, use static data for speed
            total_fortunes = 100
            end_number = 100

            # Create collection for this deity (no numbers array needed)
            collection = Collection(
                id=f"{deity_id}_standard",
                name="Standard Collection",
                description=f"Traditional {total_fortunes} fortune poems",
                number_range=NumberRange(start=1, end=end_number),
                temple_mapping=temple_name
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
        # Performance Optimization: Return static sample fortunes instead of expensive search
        # Since all temples currently return 0 poems, use static data for speed
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