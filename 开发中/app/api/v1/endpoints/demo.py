"""演示端点

演示统一响应格式和错误处理的使用
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)
from app.core.middleware import get_request_id
from app.core.response import BaseResponse, success_response

router = APIRouter()


class DemoRequest(BaseModel):
    """演示请求模型"""

    name: str = Field(..., min_length=1, max_length=50, description="姓名")
    age: int = Field(..., ge=0, le=150, description="年龄")


class DemoResponse(BaseModel):
    """演示响应模型"""

    message: str
    name: str
    age: int


@router.get("/success", response_model=BaseResponse[DemoResponse])
async def demo_success(request: Request) -> BaseResponse[DemoResponse]:
    """演示成功响应

    Returns:
        统一格式的成功响应
    """
    request_id = get_request_id(request)

    data = DemoResponse(
        message="这是一个成功的响应示例",
        name="张三",
        age=20,
    )

    return success_response(
        data=data,
        message="操作成功",
        request_id=request_id,
    )


@router.post("/validation", response_model=BaseResponse[DemoResponse])
async def demo_validation(
    request: Request, body: DemoRequest
) -> BaseResponse[DemoResponse]:
    """演示参数验证

    如果参数不符合要求，会自动返回验证错误响应

    Args:
        request: 请求对象
        body: 请求体

    Returns:
        统一格式的成功响应
    """
    request_id = get_request_id(request)

    data = DemoResponse(
        message="参数验证通过",
        name=body.name,
        age=body.age,
    )

    return success_response(
        data=data,
        message="操作成功",
        request_id=request_id,
    )


@router.get("/custom-validation-error")
async def demo_custom_validation_error():
    """演示自定义验证错误

    Raises:
        ValidationError: 自定义验证错误
    """
    raise ValidationError(
        message="自定义验证错误",
        details=[
            {"field": "studentId", "message": "学号格式不正确"},
            {"field": "email", "message": "邮箱格式不正确"},
        ],
    )


@router.get("/authentication-error")
async def demo_authentication_error():
    """演示认证错误

    Raises:
        AuthenticationError: 认证错误
    """
    raise AuthenticationError(message="Token已过期，请重新登录")


@router.get("/authorization-error")
async def demo_authorization_error():
    """演示授权错误

    Raises:
        AuthorizationError: 授权错误
    """
    raise AuthorizationError(message="您没有权限执行此操作")


@router.get("/not-found-error")
async def demo_not_found_error():
    """演示资源不存在错误

    Raises:
        NotFoundError: 资源不存在错误
    """
    raise NotFoundError(message="用户不存在")


@router.get("/internal-error")
async def demo_internal_error():
    """演示服务器内部错误

    Raises:
        Exception: 未捕获的异常
    """
    # 故意抛出一个未捕获的异常
    raise Exception("这是一个未捕获的异常")
