# 知域校园互动社交平台

专属单校/多校大学生的全场景闭环校园互动社交服务平台

## 技术栈

- **后端框架**: Python 3.11 + FastAPI
- **依赖管理**: Poetry
- **日志系统**: structlog
- **数据库**: 
  - MySQL 8.0 (关系型数据库，使用SQLAlchemy 2.0异步ORM)
  - MongoDB (文档数据库，使用Motor异步驱动)
  - Redis (缓存和会话，使用redis-py异步客户端)
- **数据库迁移**: Alembic
- **消息队列**: RabbitMQ (后续任务添加)
- **搜索引擎**: Elasticsearch (后续任务添加)

## 项目结构

```
zhiyu-campus-platform/
├── app/                      # 应用主目录
│   ├── __init__.py
│   ├── main.py              # FastAPI应用入口
│   ├── core/                # 核心配置模块
│   │   ├── __init__.py
│   │   ├── config.py        # 环境配置管理
│   │   ├── logging.py       # 日志系统配置
│   │   ├── database.py      # 数据库连接管理
│   │   └── dependencies.py  # FastAPI依赖注入
│   ├── cli/                 # 命令行工具
│   │   ├── __init__.py
│   │   └── database.py      # 数据库管理CLI
│   └── api/                 # API路由模块
│       ├── __init__.py
│       └── v1/              # API v1版本
│           ├── __init__.py
│           ├── router.py    # v1主路由
│           └── endpoints/   # API端点
│               └── __init__.py
├── alembic/                 # 数据库迁移脚本
│   ├── env.py              # Alembic环境配置
│   ├── script.py.mako      # 迁移脚本模板
│   └── versions/           # 迁移版本目录
├── tests/                   # 测试目录
├── alembic.ini             # Alembic配置文件
├── pyproject.toml          # Poetry依赖配置
├── .env.example            # 环境变量示例
├── .gitignore
├── run.py                  # 本地启动脚本
└── README.md
```

## 快速开始

### 1. 安装依赖

确保已安装 Python 3.11+ 和 Poetry:

```bash
# 安装Poetry (如果未安装)
curl -sSL https://install.python-poetry.org | python3 -

# 安装项目依赖
poetry install
```

### 2. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑.env文件，配置必要的环境变量
# 特别注意配置数据库连接信息：
# - MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
# - MONGODB_HOST, MONGODB_PORT, MONGODB_DATABASE
# - REDIS_HOST, REDIS_PORT, REDIS_DB
```

### 3. 准备数据库

确保已安装并启动以下数据库服务：

```bash
# MySQL 8.0
# 创建数据库
mysql -u root -p
CREATE DATABASE zhiyu CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# MongoDB
# 启动MongoDB服务
mongod --dbpath /path/to/data

# Redis
# 启动Redis服务
redis-server
```

### 4. 检查数据库连接

```bash
# 检查数据库连接健康状态
poetry run python -m app.cli.database check
```

### 5. 运行数据库迁移

```bash
# 创建初始迁移脚本
poetry run alembic revision --autogenerate -m "初始化数据库"

# 执行迁移
poetry run alembic upgrade head
```

### 6. 启动应用

```bash
# 使用Poetry运行
poetry run python run.py

# 或者激活虚拟环境后运行
poetry shell
python run.py
```

应用将在 http://localhost:8000 启动

### 4. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health (包含数据库健康状态)

## 数据库管理

### 数据库连接

项目使用以下数据库：

1. **MySQL**: 存储结构化业务数据（用户、订单、课程等）
   - 使用SQLAlchemy 2.0异步ORM
   - 支持连接池管理
   - 自动重连和健康检查

2. **MongoDB**: 存储非结构化数据（帖子、评论、消息等）
   - 使用Motor异步驱动
   - 支持连接池管理

3. **Redis**: 缓存和会话管理
   - 使用redis-py异步客户端
   - 支持连接池管理

### 数据库迁移

使用Alembic管理MySQL数据库schema变更：

```bash
# 创建新的迁移脚本
poetry run alembic revision --autogenerate -m "描述信息"

# 升级到最新版本
poetry run alembic upgrade head

# 降级一个版本
poetry run alembic downgrade -1

# 查看当前版本
poetry run alembic current

# 查看迁移历史
poetry run alembic history
```

### 数据库CLI工具

```bash
# 初始化数据库连接
poetry run python -m app.cli.database init

# 检查数据库健康状态
poetry run python -m app.cli.database check
```

### 在代码中使用数据库

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorDatabase
from redis.asyncio import Redis

from app.core.dependencies import get_db_session, get_mongo_db, get_redis_client

# MySQL示例
@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(User))
    return result.scalars().all()

# MongoDB示例
@router.get("/posts")
async def get_posts(db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    posts = await db.posts.find().to_list(length=100)
    return posts

# Redis示例
@router.get("/cache/{key}")
async def get_cache(key: str, redis: Redis = Depends(get_redis_client)):
    value = await redis.get(key)
    return {"value": value}
```

## 环境配置

支持三种运行环境：

- **development**: 开发环境（默认）
  - 启用调试模式
  - 启用API文档
  - 彩色控制台日志
  - 热重载

- **testing**: 测试环境
  - 用于自动化测试
  - JSON格式日志

- **production**: 生产环境
  - 禁用调试模式
  - 禁用API文档
  - JSON格式日志
  - 严格的CORS配置

通过设置 `ENVIRONMENT` 环境变量切换环境：

```bash
ENVIRONMENT=production python run.py
```

## 日志系统

使用 structlog 提供结构化日志：

- **开发环境**: 彩色控制台输出，便于阅读
- **生产环境**: JSON格式输出，便于日志收集和分析

日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL

配置日志级别：

```bash
LOG_LEVEL=DEBUG python run.py
```

## 开发指南

### 代码规范

项目使用以下工具保证代码质量：

- **black**: 代码格式化
- **ruff**: 代码检查

运行代码检查：

```bash
# 格式化代码
poetry run black app/

# 运行linter
poetry run ruff check app/
```

### 运行测试

```bash
# 运行所有测试
poetry run pytest

# 运行测试并显示覆盖率
poetry run pytest --cov=app --cov-report=html
```

## 后续任务

当前已完成任务：
- ✅ 1.1: 搭建项目基础架构
- ✅ 1.2: 配置数据库连接

后续任务包括：
- 1.3: 实现统一响应格式和错误处理
- 2.x: 用户体系与认证模块
- 3.x: 内容安全与审核模块
- ...

详见 `.kiro/specs/zhiyu-campus-social-platform/tasks.md`

## 许可证

Copyright © 2024 Zhiyu Team
