"""日志系统配置

使用structlog提供结构化日志
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from app.core.config import get_settings


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """添加应用上下文信息到日志"""
    settings = get_settings()
    event_dict["app"] = settings.app_name
    event_dict["version"] = settings.app_version
    event_dict["environment"] = settings.environment.value
    return event_dict


def setup_logging() -> None:
    """配置日志系统

    根据环境配置选择合适的日志格式和处理器
    """
    settings = get_settings()

    # 配置标准库logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )

    # 配置structlog处理器链
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        add_app_context,
    ]

    # 根据环境选择渲染器
    if settings.log_format == "json" or settings.is_production:
        # 生产环境使用JSON格式
        processors.append(structlog.processors.format_exc_info)
        processors.append(structlog.processors.JSONRenderer())
    else:
        # 开发环境使用彩色控制台输出
        processors.append(structlog.processors.ExceptionRenderer())
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # 配置structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """获取logger实例

    Args:
        name: logger名称，通常使用模块的__name__

    Returns:
        配置好的logger实例
    """
    return structlog.get_logger(name)
