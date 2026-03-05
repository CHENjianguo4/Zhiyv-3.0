"""自定义异常类

定义业务逻辑中使用的各种异常类型
"""

from typing import Any, Optional


class BaseAPIException(Exception):
    """API异常基类

    所有自定义异常都应该继承此类

    Attributes:
        message: 错误消息
        code: HTTP状态码
        error_type: 错误类型
        details: 错误详情
    """

    def __init__(
        self,
        message: str,
        code: int = 400,
        error_type: str = "APIError",
        details: Optional[list[dict[str, Any]]] = None,
    ):
        self.message = message
        self.code = code
        self.error_type = error_type
        self.details = details or []
        super().__init__(self.message)


class ValidationError(BaseAPIException):
    """参数验证错误

    当请求参数不符合要求时抛出此异常
    """

    def __init__(
        self,
        message: str = "参数验证失败",
        details: Optional[list[dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            code=400,
            error_type="ValidationError",
            details=details,
        )


class AuthenticationError(BaseAPIException):
    """认证错误

    当用户未登录或Token无效时抛出此异常
    """

    def __init__(
        self,
        message: str = "认证失败",
        details: Optional[list[dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            code=401,
            error_type="AuthenticationError",
            details=details,
        )


# 为了兼容性，添加别名
AuthenticationException = AuthenticationError


class BusinessException(BaseAPIException):
    """业务逻辑异常

    当业务逻辑执行失败时抛出此异常
    """

    def __init__(
        self,
        message: str = "业务处理失败",
        error_code: str = "BUSINESS_ERROR",
        details: Optional[list[dict[str, Any]]] = None,
    ):
        self.error_code = error_code
        super().__init__(
            message=message,
            code=400,
            error_type="BusinessException",
            details=details,
        )


class AuthorizationError(BaseAPIException):
    """授权错误

    当用户权限不足时抛出此异常
    """

    def __init__(
        self,
        message: str = "权限不足",
        details: Optional[list[dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            code=403,
            error_type="AuthorizationError",
            details=details,
        )


class NotFoundError(BaseAPIException):
    """资源不存在错误

    当请求的资源不存在时抛出此异常
    """

    def __init__(
        self,
        message: str = "资源不存在",
        details: Optional[list[dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            code=404,
            error_type="NotFoundError",
            details=details,
        )


class ConflictError(BaseAPIException):
    """资源冲突错误

    当资源冲突（如重复提交）时抛出此异常
    """

    def __init__(
        self,
        message: str = "资源冲突",
        details: Optional[list[dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            code=409,
            error_type="ConflictError",
            details=details,
        )


class RateLimitError(BaseAPIException):
    """请求频率限制错误

    当请求频率超过限制时抛出此异常
    """

    def __init__(
        self,
        message: str = "请求过于频繁，请稍后再试",
        details: Optional[list[dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            code=429,
            error_type="RateLimitError",
            details=details,
        )


class InternalServerError(BaseAPIException):
    """服务器内部错误

    当服务器发生未预期的错误时抛出此异常
    """

    def __init__(
        self,
        message: str = "服务器内部错误",
        details: Optional[list[dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            code=500,
            error_type="InternalServerError",
            details=details,
        )


class ServiceUnavailableError(BaseAPIException):
    """服务不可用错误

    当依赖的服务不可用时抛出此异常
    """

    def __init__(
        self,
        message: str = "服务暂时不可用",
        details: Optional[list[dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            code=503,
            error_type="ServiceUnavailableError",
            details=details,
        )


class InsufficientCreditError(BaseAPIException):
    """信用分不足错误

    当用户信用分不足以执行某操作时抛出此异常
    """

    def __init__(
        self,
        message: str = "信用分不足",
        details: Optional[list[dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            code=403,
            error_type="InsufficientCreditError",
            details=details,
        )


class UnverifiedUserError(BaseAPIException):
    """未认证用户错误

    当未完成校园身份认证的用户尝试执行需要认证的操作时抛出此异常
    """

    def __init__(
        self,
        message: str = "请先完成校园身份认证",
        details: Optional[list[dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            code=403,
            error_type="UnverifiedUserError",
            details=details,
        )


class ContentAuditError(BaseAPIException):
    """内容审核失败错误

    当内容审核未通过时抛出此异常
    """

    def __init__(
        self,
        message: str = "内容审核未通过",
        details: Optional[list[dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            code=400,
            error_type="ContentAuditError",
            details=details,
        )


class InsufficientBalanceError(BaseAPIException):
    """余额不足错误

    当用户余额不足以完成交易时抛出此异常
    """

    def __init__(
        self,
        message: str = "余额不足",
        details: Optional[list[dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            code=400,
            error_type="InsufficientBalanceError",
            details=details,
        )


class PermissionDeniedError(BaseAPIException):
    """权限拒绝错误

    当用户没有权限执行某操作时抛出此异常
    """

    def __init__(
        self,
        message: str = "权限不足",
        details: Optional[list[dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            code=403,
            error_type="PermissionDeniedError",
            details=details,
        )


class ResourceNotFoundError(BaseAPIException):
    """资源未找到错误

    当请求的资源不存在时抛出此异常
    """

    def __init__(
        self,
        message: str = "资源不存在",
        details: Optional[list[dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            code=404,
            error_type="ResourceNotFoundError",
            details=details,
        )
