"""测试统一响应格式

测试BaseResponse和ErrorResponse的创建和序列化
"""

import pytest
from pydantic import BaseModel

from app.core.response import (
    BaseResponse,
    ErrorResponse,
    error_response,
    success_response,
)


class SampleData(BaseModel):
    """示例数据模型"""

    name: str
    age: int


def test_success_response_with_data():
    """测试创建带数据的成功响应"""
    data = SampleData(name="张三", age=20)
    response = success_response(
        data=data,
        message="操作成功",
        request_id="test-request-id",
    )

    assert isinstance(response, BaseResponse)
    assert response.code == 200
    assert response.message == "操作成功"
    assert response.data == data
    assert response.request_id == "test-request-id"
    assert response.timestamp > 0


def test_success_response_without_data():
    """测试创建不带数据的成功响应"""
    response = success_response(
        message="操作成功",
        request_id="test-request-id",
    )

    assert isinstance(response, BaseResponse)
    assert response.code == 200
    assert response.message == "操作成功"
    assert response.data is None
    assert response.request_id == "test-request-id"


def test_success_response_custom_code():
    """测试创建自定义状态码的成功响应"""
    response = success_response(
        message="资源已创建",
        code=201,
        request_id="test-request-id",
    )

    assert response.code == 201
    assert response.message == "资源已创建"


def test_error_response():
    """测试创建错误响应"""
    error_detail = {
        "type": "ValidationError",
        "details": [
            {"field": "name", "message": "名称不能为空"},
        ],
    }

    response = error_response(
        message="参数验证失败",
        code=400,
        error=error_detail,
        request_id="test-request-id",
        path="/api/v1/test",
    )

    assert isinstance(response, ErrorResponse)
    assert response.code == 400
    assert response.message == "参数验证失败"
    assert response.error == error_detail
    assert response.request_id == "test-request-id"
    assert response.path == "/api/v1/test"
    assert response.timestamp > 0


def test_error_response_without_details():
    """测试创建不带详情的错误响应"""
    response = error_response(
        message="服务器错误",
        code=500,
        request_id="test-request-id",
    )

    assert response.code == 500
    assert response.message == "服务器错误"
    assert response.error is None


def test_response_serialization():
    """测试响应序列化为JSON"""
    data = SampleData(name="李四", age=25)
    response = success_response(
        data=data,
        request_id="test-request-id",
    )

    # 序列化为字典
    response_dict = response.model_dump()

    assert response_dict["code"] == 200
    assert response_dict["message"] == "success"
    assert response_dict["data"]["name"] == "李四"
    assert response_dict["data"]["age"] == 25
    assert response_dict["request_id"] == "test-request-id"
    assert "timestamp" in response_dict


def test_error_response_serialization():
    """测试错误响应序列化为JSON"""
    error_detail = {
        "type": "NotFoundError",
        "details": [],
    }

    response = error_response(
        message="资源不存在",
        code=404,
        error=error_detail,
        request_id="test-request-id",
        path="/api/v1/users/999",
    )

    # 序列化为字典
    response_dict = response.model_dump()

    assert response_dict["code"] == 404
    assert response_dict["message"] == "资源不存在"
    assert response_dict["error"]["type"] == "NotFoundError"
    assert response_dict["request_id"] == "test-request-id"
    assert response_dict["path"] == "/api/v1/users/999"
    assert "timestamp" in response_dict
