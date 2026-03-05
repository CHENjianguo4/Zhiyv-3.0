"""统一响应格式

定义API的统一响应模型和工具函数
"""

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

# 泛型类型变量，用于响应数据
T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """统一API响应模型

    所有API接口都应该返回此格式的响应

    Attributes:
        code: HTTP状态码
        message: 响应消息
        data: 响应数据（泛型）
        timestamp: 响应时间戳（Unix时间戳，秒）
        request_id: 请求追踪ID
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": 200,
                "message": "success",
                "data": {},
                "timestamp": 1234567890,
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
            }
        }
    )

    code: int = Field(description="HTTP状态码")
    message: str = Field(description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    timestamp: int = Field(description="响应时间戳（Unix时间戳，秒）")
    request_id: str = Field(description="请求追踪ID")


class ErrorDetail(BaseModel):
    """错误详情

    用于描述具体的错误信息

    Attributes:
        field: 错误字段名（可选）
        message: 错误消息
    """

    field: Optional[str] = Field(default=None, description="错误字段名")
    message: str = Field(description="错误消息")


class ErrorResponse(BaseModel):
    """错误响应模型

    当API返回错误时使用此格式

    Attributes:
        code: HTTP状态码
        message: 错误消息
        error: 错误详情
        timestamp: 响应时间戳（Unix时间戳，秒）
        request_id: 请求追踪ID
        path: 请求路径
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": 400,
                "message": "参数错误",
                "error": {
                    "type": "ValidationError",
                    "details": [
                        {"field": "studentId", "message": "学号格式不正确"}
                    ],
                },
                "timestamp": 1234567890,
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "path": "/api/v1/auth/verify-identity",
            }
        }
    )

    code: int = Field(description="HTTP状态码")
    message: str = Field(description="错误消息")
    error: Optional[dict[str, Any]] = Field(default=None, description="错误详情")
    timestamp: int = Field(description="响应时间戳（Unix时间戳，秒）")
    request_id: str = Field(description="请求追踪ID")
    path: Optional[str] = Field(default=None, description="请求路径")


def success_response(
    data: Optional[T] = None,
    message: str = "success",
    code: int = 200,
    request_id: str = "",
) -> BaseResponse[T]:
    """创建成功响应

    Args:
        data: 响应数据
        message: 响应消息
        code: HTTP状态码
        request_id: 请求追踪ID

    Returns:
        统一格式的成功响应
    """
    return BaseResponse(
        code=code,
        message=message,
        data=data,
        timestamp=int(datetime.now().timestamp()),
        request_id=request_id,
    )


def error_response(
    message: str,
    code: int = 400,
    error: Optional[dict[str, Any]] = None,
    request_id: str = "",
    path: Optional[str] = None,
) -> ErrorResponse:
    """创建错误响应

    Args:
        message: 错误消息
        code: HTTP状态码
        error: 错误详情
        request_id: 请求追踪ID
        path: 请求路径

    Returns:
        统一格式的错误响应
    """
    return ErrorResponse(
        code=code,
        message=message,
        error=error,
        timestamp=int(datetime.now().timestamp()),
        request_id=request_id,
        path=path,
    )
