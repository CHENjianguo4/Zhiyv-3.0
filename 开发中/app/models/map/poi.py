"""地图导航数据模型

包含MapPOI、IndoorMap表模型
"""

from datetime import datetime
from typing import Optional
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Index,
    String,
    Text,
    Numeric,
    Enum as SQLEnum,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class POIType(str, Enum):
    """兴趣点类型枚举"""
    
    BUILDING = "building"  # 建筑
    CANTEEN = "canteen"  # 食堂
    DORMITORY = "dormitory"  # 宿舍
    CLASSROOM = "classroom"  # 教室
    LIBRARY = "library"  # 图书馆
    SPORTS = "sports"  # 运动场
    GATE = "gate"  # 校门
    OTHER = "other"  # 其他


class MapPOI(Base):
    """地图兴趣点表

    存储校园地图上的点位信息
    """

    __tablename__ = "map_pois"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="POI ID",
    )

    # 关联
    school_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="学校ID",
    )

    # 基本信息
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="名称",
    )
    type: Mapped[POIType] = mapped_column(
        SQLEnum(POIType),
        nullable=False,
        index=True,
        comment="类型",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="描述",
    )
    images: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="图片列表",
    )
    
    # 坐标信息 (使用经纬度)
    latitude: Mapped[Decimal] = mapped_column(
        Numeric(10, 6),
        nullable=False,
        comment="纬度",
    )
    longitude: Mapped[Decimal] = mapped_column(
        Numeric(10, 6),
        nullable=False,
        comment="经度",
    )
    
    # 室内导航关联
    has_indoor_map: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否有室内地图",
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间",
    )

    # 索引
    __table_args__ = (
        Index("idx_poi_school_type", "school_id", "type"),
        Index("idx_poi_name", "name"),
    )


class IndoorMap(Base):
    """室内地图表

    存储建筑内部楼层和房间信息
    """

    __tablename__ = "indoor_maps"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="ID",
    )

    # 关联
    poi_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("map_pois.id"),
        nullable=False,
        index=True,
        comment="所属建筑ID",
    )

    # 楼层信息
    floor_name: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="楼层名称(如 F1, B1)",
    )
    floor_index: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="楼层索引(1, -1)",
    )
    map_url: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="楼层平面图URL",
    )
    
    # 房间数据
    rooms: Mapped[dict] = mapped_column(
        JSON,
        nullable=True,
        comment="房间布局数据(GeoJSON)",
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间",
    )
