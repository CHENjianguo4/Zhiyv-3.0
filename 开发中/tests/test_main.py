"""测试应用主入口和基础功能"""

import pytest


def test_health_check(client):
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "app" in data
    assert "version" in data
    assert "environment" in data


def test_api_docs_available_in_dev(client):
    """测试开发环境下API文档可访问"""
    # Swagger UI
    response = client.get("/docs")
    assert response.status_code == 200

    # ReDoc
    response = client.get("/redoc")
    assert response.status_code == 200
