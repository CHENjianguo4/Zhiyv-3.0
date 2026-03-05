"""Alembic迁移环境配置

配置Alembic使用异步SQLAlchemy引擎进行数据库迁移
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import get_settings
from app.core.database import Base

# 导入所有模型以便Alembic能够检测到它们
from app.models import user  # noqa: F401

# Alembic Config对象，提供访问.ini文件的值
config = context.config

# 解释Python日志配置文件
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 添加模型的MetaData对象，用于'autogenerate'支持
target_metadata = Base.metadata

# 从应用配置获取数据库URL
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.mysql_url)


def run_migrations_offline() -> None:
    """在'离线'模式下运行迁移

    这将配置上下文仅使用URL而不是Engine，
    尽管这里也可以接受Engine。
    通过跳过Engine创建，我们甚至不需要DBAPI可用。

    在这里调用context.execute()会将给定的字符串发送到脚本输出。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """执行迁移的辅助函数"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """在异步模式下运行迁移"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在'在线'模式下运行迁移

    在这种情况下，我们需要创建一个Engine并将连接与上下文关联。
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
