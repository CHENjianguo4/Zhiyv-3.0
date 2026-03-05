"""测试自定义异常类

测试各种业务异常的创建和属性
"""

import pytest

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BaseAPIException,
    ConflictError,
    ContentAuditError,
    InsufficientBalanceError,
    InsufficientCreditError,
    InternalServerError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
    UnverifiedUserError,
    ValidationError,
)


def test_base_api_exception():
    """测试基础API异常"""
    exc = BaseAPIException(
        message="测试错误",
        code=400,
        error_type="TestError",
        details=[{"field": "test", "message": "测试"}],
    )

    assert exc.message == "测试错误"
    assert exc.code == 400
    assert exc.error_type == "TestError"
    assert len(exc.details) == 1
    assert str(exc) == "测试错误"


def test_validation_error():
    """测试参数验证错误"""
    exc = ValidationError(
        message="参数错误",
        details=[
            {"field": "name", "message": "名称不能为空"},
            {"field": "age", "message": "年龄必须大于0"},
        ],
    )

    assert exc.message == "参数错误"
    assert exc.code == 400
    assert exc.error_type == "ValidationError"
    assert len(exc.details) == 2


def test_validation_error_default_message():
    """测试参数验证错误的默认消息"""
    exc = ValidationError()

    assert exc.message == "参数验证失败"
    assert exc.code == 400


def test_authentication_error():
    """测试认证错误"""
    exc = AuthenticationError(message="Token无效")

    assert exc.message == "Token无效"
    assert exc.code == 401
    assert exc.error_type == "AuthenticationError"


def test_authorization_error():
    """测试授权错误"""
    exc = AuthorizationError(message="权限不足")

    assert exc.message == "权限不足"
    assert exc.code == 403
    assert exc.error_type == "AuthorizationError"


def test_not_found_error():
    """测试资源不存在错误"""
    exc = NotFoundError(message="用户不存在")

    assert exc.message == "用户不存在"
    assert exc.code == 404
    assert exc.error_type == "NotFoundError"


def test_conflict_error():
    """测试资源冲突错误"""
    exc = ConflictError(message="用户名已存在")

    assert exc.message == "用户名已存在"
    assert exc.code == 409
    assert exc.error_type == "ConflictError"


def test_rate_limit_error():
    """测试请求频率限制错误"""
    exc = RateLimitError()

    assert exc.message == "请求过于频繁，请稍后再试"
    assert exc.code == 429
    assert exc.error_type == "RateLimitError"


def test_internal_server_error():
    """测试服务器内部错误"""
    exc = InternalServerError()

    assert exc.message == "服务器内部错误"
    assert exc.code == 500
    assert exc.error_type == "InternalServerError"


def test_service_unavailable_error():
    """测试服务不可用错误"""
    exc = ServiceUnavailableError()

    assert exc.message == "服务暂时不可用"
    assert exc.code == 503
    assert exc.error_type == "ServiceUnavailableError"


def test_insufficient_credit_error():
    """测试信用分不足错误"""
    exc = InsufficientCreditError(message="信用分低于60分，无法接单")

    assert exc.message == "信用分低于60分，无法接单"
    assert exc.code == 403
    assert exc.error_type == "InsufficientCreditError"


def test_unverified_user_error():
    """测试未认证用户错误"""
    exc = UnverifiedUserError()

    assert exc.message == "请先完成校园身份认证"
    assert exc.code == 403
    assert exc.error_type == "UnverifiedUserError"


def test_content_audit_error():
    """测试内容审核失败错误"""
    exc = ContentAuditError(
        message="内容包含敏感词",
        details=[{"keyword": "敏感词1"}],
    )

    assert exc.message == "内容包含敏感词"
    assert exc.code == 400
    assert exc.error_type == "ContentAuditError"
    assert len(exc.details) == 1


def test_insufficient_balance_error():
    """测试余额不足错误"""
    exc = InsufficientBalanceError(message="账户余额不足，无法完成支付")

    assert exc.message == "账户余额不足，无法完成支付"
    assert exc.code == 400
    assert exc.error_type == "InsufficientBalanceError"


def test_exception_inheritance():
    """测试异常继承关系"""
    exc = ValidationError()

    assert isinstance(exc, BaseAPIException)
    assert isinstance(exc, Exception)
