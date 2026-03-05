"""FastAPI应用主入口

创建和配置FastAPI应用实例
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import (
    check_databases_health,
    close_databases,
    init_databases,
)
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.core.middleware import RequestIDMiddleware

# 初始化日志系统
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理

    在应用启动和关闭时执行必要的初始化和清理工作
    """
    settings = get_settings()

    # 启动时执行
    logger.info(
        "应用启动",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment.value,
    )

    # 初始化数据库连接
    try:
        await init_databases()
        logger.info("数据库连接初始化成功")
    except Exception as e:
        logger.error("数据库连接初始化失败", error=str(e))
        raise

    yield

    # 关闭时执行
    logger.info("开始关闭应用")

    # 关闭数据库连接
    try:
        await close_databases()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error("关闭数据库连接时出错", error=str(e))

    logger.info("应用关闭完成")


def create_app() -> FastAPI:
    """创建FastAPI应用实例

    Returns:
        配置好的FastAPI应用实例
    """
    settings = get_settings()

    # 创建FastAPI应用
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_development else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 添加请求ID追踪中间件
    app.add_middleware(RequestIDMiddleware)

    # 注册全局异常处理器
    register_exception_handlers(app)

    # 注册路由
    app.include_router(api_router)

    # 健康检查端点
    @app.get("/health", tags=["系统"])
    async def health_check():
        """健康检查端点

        检查应用和数据库连接状态
        """
        db_health = await check_databases_health()
        all_healthy = all(db_health.values())

        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "app": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment.value,
            "databases": db_health,
        }

    return app


# 创建应用实例
app = create_app()
