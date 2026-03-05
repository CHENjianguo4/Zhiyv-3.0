"""数据库管理CLI工具

提供数据库初始化、健康检查等命令行工具
"""

import asyncio
import sys

from app.core.database import (
    check_databases_health,
    close_databases,
    init_databases,
)
from app.core.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


async def init_db():
    """初始化数据库连接"""
    try:
        logger.info("开始初始化数据库连接")
        await init_databases()
        logger.info("数据库连接初始化成功")
        await close_databases()
        return 0
    except Exception as e:
        logger.error("数据库连接初始化失败", error=str(e))
        return 1


async def check_db():
    """检查数据库连接健康状态"""
    try:
        logger.info("开始检查数据库连接")
        await init_databases()

        health = await check_databases_health()

        logger.info("数据库健康检查结果", health=health)

        for db_name, is_healthy in health.items():
            status = "✓ 健康" if is_healthy else "✗ 不健康"
            print(f"{db_name}: {status}")

        await close_databases()

        # 如果所有数据库都健康，返回0，否则返回1
        return 0 if all(health.values()) else 1
    except Exception as e:
        logger.error("数据库健康检查失败", error=str(e))
        return 1


def main():
    """CLI主入口"""
    if len(sys.argv) < 2:
        print("用法: python -m app.cli.database <command>")
        print("可用命令:")
        print("  init   - 初始化数据库连接")
        print("  check  - 检查数据库健康状态")
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        exit_code = asyncio.run(init_db())
    elif command == "check":
        exit_code = asyncio.run(check_db())
    else:
        print(f"未知命令: {command}")
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
