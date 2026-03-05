"""地图导航API接口"""

from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.map.map_service import MapService
from app.repositories.map.map_repo import MapRepository
from app.models.map.poi import POIType
from app.core.response import success_response, error_response

router = APIRouter()

# 依赖注入
async def get_map_service(
    db: AsyncSession = Depends(get_db),
) -> MapService:
    repo = MapRepository(db)
    return MapService(repo)


class POICreate(BaseModel):
    name: str = Field(..., max_length=100)
    type: POIType
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)
    description: Optional[str] = None
    images: Optional[List[str]] = None


@router.post("/pois", response_model=dict)
async def create_poi(
    data: POICreate,
    current_user: User = Depends(get_current_user),
    service: MapService = Depends(get_map_service),
):
    """创建POI"""
    # TODO: 权限验证
    poi = await service.create_poi(
        school_id=current_user.school_id,
        name=data.name,
        type=data.type,
        latitude=data.latitude,
        longitude=data.longitude,
        description=data.description,
        images=data.images
    )
    return success_response(data={"id": poi.id}, message="POI创建成功")


@router.get("/pois", response_model=dict)
async def list_pois(
    type: Optional[POIType] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    service: MapService = Depends(get_map_service),
):
    """获取POI列表"""
    pois = await service.list_pois(
        current_user.school_id, type, keyword, page, page_size
    )
    return success_response(
        data=[
            {
                "id": p.id,
                "name": p.name,
                "type": p.type,
                "lat": float(p.latitude),
                "lng": float(p.longitude),
                "has_indoor": p.has_indoor_map
            } for p in pois
        ]
    )


@router.get("/pois/{poi_id}", response_model=dict)
async def get_poi_detail(
    poi_id: int,
    current_user: User = Depends(get_current_user),
    service: MapService = Depends(get_map_service),
):
    """获取POI详情"""
    detail = await service.get_poi_detail(poi_id)
    return success_response(data=detail)
