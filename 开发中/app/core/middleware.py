"""中间件

定义应用使用的各种中间件
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """请求ID追踪中间件

    为每个请求生成唯一的request_id，用于日志追踪和问题排查
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """处理请求

        Args:
            request: 请求对象
            call_next: 下一个处理函数

        Returns:
            响应对象
        """
        # 生成或获取request_id
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # 将request_id存储到request.state中，供后续使用
        request.state.request_id = request_id

        # 记录请求开始
        start_time = time.time()
        logger.info(
            "请求开始",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
        )

        # 处理请求
        response = await call_next(request)

        # 计算请求处理时间
        process_time = time.time() - start_time

        # 添加request_id到响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        # 记录请求完成
        logger.info(
            "请求完成",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time=f"{process_time:.3f}s",
        )

        return response


def get_request_id(request: Request) -> str:
    """从请求中获取request_id

    Args:
        request: 请求对象

    Returns:
        请求ID
    """
    return getattr(request.state, "request_id", "")
