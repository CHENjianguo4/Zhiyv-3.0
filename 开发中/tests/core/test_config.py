"""测试配置管理模块"""

import pytest

from app.core.config import Environment, Settings, get_settings


def test_default_settings():
    """测试默认配置"""
    settings = Settings()

    assert settings.environment == Environment.DEVELOPMENT
    assert settings.app_name == "知域校园互动社交平台"
    assert settings.debug is True
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.log_level == "INFO"


def test_environment_properties():
    """测试环境判断属性"""
    # 开发环境
    dev_settings = Settings(environment=Environment.DEVELOPMENT)
    assert dev_settings.is_development is True
    assert dev_settings.is_testing is False
    assert dev_settings.is_production is False

    # 测试环境
    test_settings = Settings(environment=Environment.TESTING)
    assert test_settings.is_development is False
    assert test_settings.is_testing is True
    assert test_settings.is_production is False

    # 生产环境
    prod_settings = Settings(environment=Environment.PRODUCTION)
    assert prod_settings.is_development is False
    assert prod_settings.is_testing is False
    assert prod_settings.is_production is True


def test_get_settings_singleton():
    """测试配置单例"""
    settings1 = get_settings()
    settings2 = get_settings()

    # 应该返回同一个实例
    assert settings1 is settings2
