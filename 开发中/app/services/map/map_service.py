"""地图导航服务层

提供POI管理、路径规划等业务逻辑
"""

from typing import List, Optional
from decimal import Decimal

from app.core.logging import get_logger
from app.repositories.map.map_repo import MapRepository
from app.models.map.poi import MapPOI, IndoorMap, POIType
from app.core.exceptions import ValidationError, ResourceNotFoundError

logger = get_logger(__name__)


class MapService:
    """地图服务类"""

    def __init__(self, repo: MapRepository):
        self.repo = repo

    async def create_poi(
        self,
        school_id: int,
        name: str,
        type: POIType,
        latitude: Decimal,
        longitude: Decimal,
        description: Optional[str] = None,
        images: Optional[list] = None
    ) -> MapPOI:
        """创建POI"""
        poi = MapPOI(
            school_id=school_id,
            name=name,
            type=type,
            latitude=latitude,
            longitude=longitude,
            description=description,
            images=images,
            has_indoor_map=False
        )
        
        created_poi = await self.repo.create_poi(poi)
        logger.info(f"POI created: {created_poi.id} - {name}")
        return created_poi

    async def list_pois(
        self,
        school_id: int,
        type: Optional[POIType] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[MapPOI]:
        """获取POI列表"""
        offset = (page - 1) * page_size
        return await self.repo.list_pois(school_id, type, keyword, offset, page_size)

    async def get_poi_detail(self, poi_id: int) -> dict:
        """获取POI详情（包含室内地图）"""
        poi = await self.repo.get_poi(poi_id)
        if not poi:
            raise ResourceNotFoundError(f"POI {poi_id} not found")
            
        result = {
            "id": poi.id,
            "name": poi.name,
            "type": poi.type,
            "latitude": float(poi.latitude),
            "longitude": float(poi.longitude),
            "description": poi.description,
            "images": poi.images,
            "has_indoor_map": poi.has_indoor_map,
            "indoor_maps": []
        }
        
        if poi.has_indoor_map:
            indoor_maps = await self.repo.get_indoor_maps(poi_id)
            result["indoor_maps"] = [
                {
                    "id": m.id,
                    "floor_name": m.floor_name,
                    "floor_index": m.floor_index,
                    "map_url": m.map_url,
                    "rooms": m.rooms
                } for m in indoor_maps
            ]
            
        return result

    async def add_indoor_map(
        self,
        poi_id: int,
        floor_name: str,
        floor_index: int,
        map_url: str,
        rooms: Optional[dict] = None
    ) -> IndoorMap:
        """添加室内地图"""
        poi = await self.repo.get_poi(poi_id)
        if not poi:
            raise ResourceNotFoundError(f"POI {poi_id} not found")
            
        indoor_map = IndoorMap(
            poi_id=poi_id,
            floor_name=floor_name,
            floor_index=floor_index,
            map_url=map_url,
            rooms=rooms
        )
        
        created_map = await self.repo.create_indoor_map(indoor_map)
        
        # 更新POI状态
        if not poi.has_indoor_map:
            poi.has_indoor_map = True
            await self.repo.update_poi(poi)
            
        return created_map
