"""地图导航仓储层

提供地图POI和室内地图的数据访问
"""

from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.map.poi import MapPOI, IndoorMap, POIType


class MapRepository:
    """地图仓储类"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_poi(self, poi: MapPOI) -> MapPOI:
        """创建POI"""
        self.session.add(poi)
        await self.session.flush()
        await self.session.refresh(poi)
        return poi

    async def get_poi(self, poi_id: int) -> Optional[MapPOI]:
        """获取POI详情"""
        query = select(MapPOI).where(MapPOI.id == poi_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_pois(
        self,
        school_id: int,
        type: Optional[POIType] = None,
        keyword: Optional[str] = None,
        offset: int = 0,
        limit: int = 20
    ) -> List[MapPOI]:
        """获取POI列表"""
        query = select(MapPOI).where(MapPOI.school_id == school_id)
        
        if type:
            query = query.where(MapPOI.type == type)
        if keyword:
            query = query.where(
                or_(
                    MapPOI.name.contains(keyword),
                    MapPOI.description.contains(keyword)
                )
            )
            
        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_indoor_map(self, indoor_map: IndoorMap) -> IndoorMap:
        """创建室内地图"""
        self.session.add(indoor_map)
        await self.session.flush()
        await self.session.refresh(indoor_map)
        return indoor_map

    async def get_indoor_maps(self, poi_id: int) -> List[IndoorMap]:
        """获取建筑的所有楼层地图"""
        query = select(IndoorMap).where(
            IndoorMap.poi_id == poi_id
        ).order_by(IndoorMap.floor_index)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_poi(self, poi: MapPOI) -> MapPOI:
        """更新POI信息"""
        self.session.add(poi)
        return poi
