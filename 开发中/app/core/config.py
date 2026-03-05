"""应用配置管理

支持开发、测试、生产三种环境配置
"""

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """环境枚举"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """应用配置类

    从环境变量和.env文件加载配置
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用基础配置
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="运行环境",
    )
    app_name: str = Field(
        default="知域校园互动社交平台",
        description="应用名称",
    )
    app_version: str = Field(
        default="0.1.0",
        description="应用版本",
    )
    debug: bool = Field(
        default=True,
        description="调试模式",
    )
    host: str = Field(
        default="0.0.0.0",
        description="服务监听地址",
    )
    port: int = Field(
        default=8000,
        description="服务监听端口",
    )

    # 日志配置
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="日志级别",
    )
    log_format: Literal["json", "console"] = Field(
        default="json",
        description="日志格式",
    )

    # MySQL数据库配置
    mysql_host: str = Field(
        default="localhost",
        description="MySQL主机地址",
    )
    mysql_port: int = Field(
        default=3306,
        description="MySQL端口",
    )
    mysql_user: str = Field(
        default="root",
        description="MySQL用户名",
    )
    mysql_password: str = Field(
        default="",
        description="MySQL密码",
    )
    mysql_database: str = Field(
        default="zhiyu",
        description="MySQL数据库名",
    )
    mysql_pool_size: int = Field(
        default=10,
        description="MySQL连接池大小",
    )
    mysql_max_overflow: int = Field(
        default=20,
        description="MySQL连接池最大溢出",
    )
    mysql_pool_recycle: int = Field(
        default=3600,
        description="MySQL连接回收时间（秒）",
    )
    mysql_echo: bool = Field(
        default=False,
        description="是否打印SQL语句",
    )

    # MongoDB配置
    mongodb_host: str = Field(
        default="localhost",
        description="MongoDB主机地址",
    )
    mongodb_port: int = Field(
        default=27017,
        description="MongoDB端口",
    )
    mongodb_user: str = Field(
        default="",
        description="MongoDB用户名",
    )
    mongodb_password: str = Field(
        default="",
        description="MongoDB密码",
    )
    mongodb_database: str = Field(
        default="zhiyu",
        description="MongoDB数据库名",
    )
    mongodb_max_pool_size: int = Field(
        default=100,
        description="MongoDB最大连接池大小",
    )
    mongodb_min_pool_size: int = Field(
        default=10,
        description="MongoDB最小连接池大小",
    )

    # Redis配置
    redis_host: str = Field(
        default="localhost",
        description="Redis主机地址",
    )
    redis_port: int = Field(
        default=6379,
        description="Redis端口",
    )
    redis_password: str = Field(
        default="",
        description="Redis密码",
    )
    redis_db: int = Field(
        default=0,
        description="Redis数据库编号",
    )
    redis_max_connections: int = Field(
        default=50,
        description="Redis最大连接数",
    )
    redis_socket_timeout: int = Field(
        default=5,
        description="Redis socket超时时间（秒）",
    )
    redis_socket_connect_timeout: int = Field(
        default=5,
        description="Redis连接超时时间（秒）",
    )

    # JWT配置
    jwt_secret_key: str = Field(
        default="your-secret-key-change-this-in-production",
        description="JWT密钥",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT加密算法",
    )
    jwt_expire_minutes: int = Field(
        default=1440,  # 24小时
        description="JWT访问令牌过期时间（分钟）",
    )
    jwt_refresh_expire_minutes: int = Field(
        default=10080,  # 7天
        description="JWT刷新令牌过期时间（分钟）",
    )

    # 微信配置
    wechat_app_id: str = Field(
        default="",
        description="微信小程序AppID",
    )
    wechat_app_secret: str = Field(
        default="",
        description="微信小程序AppSecret",
    )

    @property
    def mysql_url(self) -> str:
        """构建MySQL连接URL"""
        if self.mysql_password:
            return (
                f"mysql+asyncmy://{self.mysql_user}:{self.mysql_password}"
                f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
                f"?charset=utf8mb4"
            )
        return (
            f"mysql+asyncmy://{self.mysql_user}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            f"?charset=utf8mb4"
        )

    @property
    def mongodb_url(self) -> str:
        """构建MongoDB连接URL"""
        if self.mongodb_user and self.mongodb_password:
            return (
                f"mongodb://{self.mongodb_user}:{self.mongodb_password}"
                f"@{self.mongodb_host}:{self.mongodb_port}"
            )
        return f"mongodb://{self.mongodb_host}:{self.mongodb_port}"

    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.environment == Environment.TESTING

    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment == Environment.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    """获取配置单例

    使用lru_cache确保配置只加载一次
    """
    return Settings()
