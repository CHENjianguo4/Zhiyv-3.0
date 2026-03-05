"""全局异常处理器

捕获所有异常并返回统一格式的错误响应
"""

from typing import Union

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import BaseAPIException
from app.core.logging import get_logger
from app.core.middleware import get_request_id
from app.core.response import error_response

logger = get_logger(__name__)


async def base_api_exception_handler(
    request: Request, exc: BaseAPIException
) -> JSONResponse:
    """处理自定义API异常

    Args:
        request: 请求对象
        exc: 异常对象

    Returns:
        JSON响应
    """
    request_id = get_request_id(request)

    # 记录异常日志
    logger.warning(
        "业务异常",
        request_id=request_id,
        path=str(request.url.path),
        error_type=exc.error_type,
        message=exc.message,
        details=exc.details,
    )

    # 构建错误详情
    error_detail = {
        "type": exc.error_type,
        "details": exc.details,
    }

    # 创建错误响应
    response = error_response(
        message=exc.message,
        code=exc.code,
        error=error_detail,
        request_id=request_id,
        path=str(request.url.path),
    )

    return JSONResponse(
        status_code=exc.code,
        content=response.model_dump(),
    )


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, PydanticValidationError],
) -> JSONResponse:
    """处理参数验证异常

    Args:
        request: 请求对象
        exc: 异常对象

    Returns:
        JSON响应
    """
    request_id = get_request_id(request)

    # 提取验证错误详情
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:])  # 跳过'body'
        details.append(
            {
                "field": field,
                "message": error["msg"],
                "type": error["type"],
            }
        )

    # 记录异常日志
    logger.warning(
        "参数验证失败",
        request_id=request_id,
        path=str(request.url.path),
        details=details,
    )

    # 构建错误详情
    error_detail = {
        "type": "ValidationError",
        "details": details,
    }

    # 创建错误响应
    response = error_response(
        message="参数验证失败",
        code=status.HTTP_400_BAD_REQUEST,
        error=error_detail,
        request_id=request_id,
        path=str(request.url.path),
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=response.model_dump(),
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """处理HTTP异常

    Args:
        request: 请求对象
        exc: 异常对象

    Returns:
        JSON响应
    """
    request_id = get_request_id(request)

    # 记录异常日志
    logger.warning(
        "HTTP异常",
        request_id=request_id,
        path=str(request.url.path),
        status_code=exc.status_code,
        detail=exc.detail,
    )

    # 创建错误响应
    response = error_response(
        message=exc.detail,
        code=exc.status_code,
        request_id=request_id,
        path=str(request.url.path),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(),
    )


async def general_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """处理未捕获的异常

    Args:
        request: 请求对象
        exc: 异常对象

    Returns:
        JSON响应
    """
    request_id = get_request_id(request)

    # 记录异常日志（包含堆栈信息）
    logger.error(
        "未捕获的异常",
        request_id=request_id,
        path=str(request.url.path),
        error_type=type(exc).__name__,
        error=str(exc),
        exc_info=True,
    )

    # 创建错误响应（不暴露内部错误详情）
    response = error_response(
        message="服务器内部错误",
        code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error={
            "type": "InternalServerError",
            "details": [],
        },
        request_id=request_id,
        path=str(request.url.path),
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(),
    )


def register_exception_handlers(app) -> None:
    """注册所有异常处理器

    Args:
        app: FastAPI应用实例
    """
    # 注册自定义API异常处理器
    app.add_exception_handler(BaseAPIException, base_api_exception_handler)

    # 注册参数验证异常处理器
    app.add_exception_handler(
        RequestValidationError, validation_exception_handler
    )
    app.add_exception_handler(
        PydanticValidationError, validation_exception_handler
    )

    # 注册HTTP异常处理器
    app.add_exception_handler(
        StarletteHTTPException, http_exception_handler
    )

    # 注册通用异常处理器（捕获所有未处理的异常）
    app.add_exception_handler(Exception, general_exception_handler)
