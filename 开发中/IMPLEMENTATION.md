# 任务 1.1 实施文档

## 任务概述

**任务**: 1.1 搭建项目基础架构

**需求**: 32.1, 32.2

**目标**:
- 创建Python项目结构（使用Poetry管理依赖）
- 配置FastAPI应用和路由框架
- 设置环境配置管理（开发/测试/生产环境）
- 配置日志系统（structlog）

## 已完成的工作

### 1. 项目结构

创建了标准的Python项目目录结构：

```
zhiyu-campus-platform/
├── app/                      # 应用主目录
│   ├── __init__.py
│   ├── main.py              # FastAPI应用入口
│   ├── core/                # 核心配置模块
│   │   ├── __init__.py
│   │   ├── config.py        # 环境配置管理
│   │   └── logging.py       # 日志系统配置
│   └── api/                 # API路由模块
│       ├── __init__.py
│       └── v1/              # API v1版本
│           ├── __init__.py
│           ├── router.py    # v1主路由
│           └── endpoints/   # API端点目录
│               └── __init__.py
├── tests/                   # 测试目录
│   ├── __init__.py
│   ├── conftest.py         # pytest配置
│   ├── test_main.py        # 主应用测试
│   └── core/
│       ├── __init__.py
│       └── test_config.py  # 配置测试
├── pyproject.toml          # Poetry依赖配置
├── requirements.txt        # pip依赖配置（备用）
├── pytest.ini              # pytest配置
├── .env                    # 环境变量（本地）
├── .env.example            # 环境变量示例
├── .gitignore
├── run.py                  # 本地启动脚本
└── README.md               # 项目文档
```

### 2. 依赖管理（Poetry）

**文件**: `pyproject.toml`

配置了以下依赖：

**生产依赖**:
- `fastapi ^0.109.0` - Web框架
- `uvicorn[standard] ^0.27.0` - ASGI服务器
- `pydantic ^2.5.0` - 数据验证
- `pydantic-settings ^2.1.0` - 配置管理
- `structlog ^24.1.0` - 结构化日志
- `python-dotenv ^1.0.0` - 环境变量加载

**开发依赖**:
- `pytest ^7.4.0` - 测试框架
- `pytest-asyncio ^0.23.0` - 异步测试支持
- `httpx ^0.26.0` - HTTP客户端（用于测试）
- `black ^24.1.0` - 代码格式化
- `ruff ^0.1.0` - 代码检查

**代码质量配置**:
- Black: 行长度100，目标Python 3.11
- Ruff: 启用E, F, I, N, W规则

### 3. FastAPI应用配置

**文件**: `app/main.py`

实现了以下功能：

1. **应用生命周期管理**
   - 使用`@asynccontextmanager`管理启动和关闭
   - 启动时记录应用信息
   - 为后续数据库连接等初始化预留位置

2. **FastAPI应用创建**
   - 根据环境配置标题、版本、调试模式
   - 开发环境启用API文档（/docs, /redoc）
   - 生产环境禁用API文档

3. **CORS配置**
   - 开发环境允许所有来源
   - 生产环境需要配置白名单

4. **路由注册**
   - 注册API v1路由（/api/v1）
   - 健康检查端点（/health）

5. **健康检查端点**
   ```json
   GET /health
   {
     "status": "healthy",
     "app": "知域校园互动社交平台",
     "version": "0.1.0",
     "environment": "development"
   }
   ```

### 4. 路由框架

**文件**: `app/api/v1/router.py`

- 创建了API v1版本的主路由
- 使用`/api/v1`前缀
- 预留了子路由注册位置
- 后续任务将添加具体的端点（auth, users, posts等）

**目录结构**:
- `app/api/v1/endpoints/` - 存放具体的API端点实现
- 每个功能模块一个文件（如auth.py, users.py）

### 5. 环境配置管理

**文件**: `app/core/config.py`

实现了三种环境的配置管理：

1. **Environment枚举**
   - DEVELOPMENT: 开发环境
   - TESTING: 测试环境
   - PRODUCTION: 生产环境

2. **Settings类**
   - 使用`pydantic-settings`从环境变量加载配置
   - 支持`.env`文件
   - 类型安全的配置项

3. **配置项**
   - `environment`: 运行环境
   - `app_name`: 应用名称
   - `app_version`: 应用版本
   - `debug`: 调试模式
   - `host`: 服务监听地址
   - `port`: 服务监听端口
   - `log_level`: 日志级别
   - `log_format`: 日志格式

4. **环境判断属性**
   - `is_development`: 是否为开发环境
   - `is_testing`: 是否为测试环境
   - `is_production`: 是否为生产环境

5. **配置单例**
   - `get_settings()`: 使用`@lru_cache`确保配置只加载一次

### 6. 日志系统（structlog）

**文件**: `app/core/logging.py`

实现了结构化日志系统：

1. **日志处理器链**
   - 合并上下文变量
   - 添加logger名称和日志级别
   - 格式化位置参数
   - 添加时间戳（ISO格式）
   - 渲染堆栈信息
   - 添加应用上下文（app, version, environment）

2. **环境适配**
   - **开发环境**: 彩色控制台输出，便于阅读
   - **生产环境**: JSON格式输出，便于日志收集和分析

3. **日志级别**
   - DEBUG, INFO, WARNING, ERROR, CRITICAL
   - 通过`LOG_LEVEL`环境变量配置

4. **使用方式**
   ```python
   from app.core.logging import get_logger
   
   logger = get_logger(__name__)
   logger.info("用户登录", user_id=123, action="login")
   ```

5. **日志格式示例**
   
   **开发环境（控制台）**:
   ```
   2024-01-01T12:00:00Z [info     ] 用户登录 app=知域校园互动社交平台 version=0.1.0 environment=development user_id=123 action=login
   ```
   
   **生产环境（JSON）**:
   ```json
   {
     "event": "用户登录",
     "level": "info",
     "timestamp": "2024-01-01T12:00:00Z",
     "app": "知域校园互动社交平台",
     "version": "0.1.0",
     "environment": "production",
     "user_id": 123,
     "action": "login"
   }
   ```

### 7. 环境变量配置

**文件**: `.env.example` 和 `.env`

提供了环境变量模板和本地开发配置：

```bash
# 应用环境
ENVIRONMENT=development

# 应用配置
APP_NAME=知域校园互动社交平台
APP_VERSION=0.1.0
DEBUG=true
HOST=0.0.0.0
PORT=8000

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=console
```

预留了后续任务的配置项：
- 数据库连接
- JWT配置
- 微信配置

### 8. 测试框架

**文件**: `tests/conftest.py`, `tests/test_main.py`, `tests/core/test_config.py`

实现了基础测试：

1. **测试配置**
   - pytest配置文件（pytest.ini）
   - 共享fixtures（conftest.py）
   - 测试标记（unit, integration, property）

2. **测试用例**
   - 健康检查端点测试
   - API文档可访问性测试
   - 配置管理测试
   - 环境判断测试
   - 配置单例测试

3. **测试运行**
   ```bash
   pytest                    # 运行所有测试
   pytest -v                 # 详细输出
   pytest --cov=app          # 代码覆盖率
   ```

### 9. 启动脚本

**文件**: `run.py`

提供了本地开发启动脚本：

```python
python run.py
```

功能：
- 从配置加载host和port
- 开发环境启用热重载
- 配置日志级别

### 10. 文档

**文件**: `README.md`

提供了完整的项目文档：
- 技术栈说明
- 项目结构
- 快速开始指南
- 环境配置说明
- 日志系统说明
- 开发指南
- 后续任务说明

## 技术亮点

1. **类型安全**: 使用Pydantic进行配置管理，提供类型检查和验证
2. **结构化日志**: 使用structlog提供结构化日志，便于日志分析
3. **环境隔离**: 支持开发、测试、生产三种环境，配置清晰
4. **代码质量**: 配置了black和ruff保证代码质量
5. **测试覆盖**: 提供了基础测试框架和示例测试
6. **文档完善**: 提供了详细的README和代码注释

## 符合需求

### 需求 32.1: 微服务架构设计

- ✅ 采用模块化设计，按功能划分目录结构
- ✅ 预留了服务拆分的接口（api/v1/endpoints）
- ✅ 使用FastAPI支持异步处理，便于后续扩展

### 需求 32.2: 服务拆分

- ✅ 创建了清晰的目录结构，便于后续拆分服务
- ✅ 使用API版本化（v1），支持后续版本迭代
- ✅ 预留了各个服务模块的目录（endpoints）

## 后续任务

当前任务已完成项目基础架构搭建。后续任务包括：

1. **任务 1.2**: 配置数据库连接
   - MySQL连接池（SQLAlchemy）
   - MongoDB连接（Motor）
   - Redis连接（aioredis）
   - 数据库迁移（Alembic）

2. **任务 1.3**: 实现统一响应格式和错误处理
   - BaseResponse模型
   - 全局异常处理器
   - 业务异常类型
   - 请求ID追踪

3. **任务 2.x**: 用户体系与认证模块
   - 用户数据模型
   - 微信授权登录
   - 校园身份认证
   - 信用分体系
   - 权限管理

## 验证方式

### 1. 代码语法检查

```bash
python -m py_compile app/main.py app/core/config.py app/core/logging.py
```

✅ 所有文件编译成功，无语法错误

### 2. 项目结构检查

```bash
tree app/
```

✅ 目录结构符合设计要求

### 3. 配置加载测试

```python
from app.core.config import get_settings
settings = get_settings()
print(settings.app_name)  # 输出: 知域校园互动社交平台
```

✅ 配置正确加载

### 4. 日志系统测试

```python
from app.core.logging import setup_logging, get_logger
setup_logging()
logger = get_logger(__name__)
logger.info("测试日志")
```

✅ 日志系统正常工作

### 5. 应用启动测试

```bash
python run.py
```

访问 http://localhost:8000/health

预期响应：
```json
{
  "status": "healthy",
  "app": "知域校园互动社交平台",
  "version": "0.1.0",
  "environment": "development"
}
```

## 安装说明

### 使用Poetry（推荐）

```bash
# 安装Poetry
curl -sSL https://install.python-poetry.org | python3 -

# 安装依赖
poetry install

# 运行应用
poetry run python run.py
```

### 使用pip

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
python run.py
```

## 总结

任务 1.1 已成功完成，实现了：

1. ✅ 标准的Python项目结构
2. ✅ Poetry依赖管理配置
3. ✅ FastAPI应用和路由框架
4. ✅ 三种环境的配置管理
5. ✅ structlog结构化日志系统
6. ✅ 基础测试框架
7. ✅ 完善的项目文档

项目基础架构已搭建完成，为后续功能开发提供了坚实的基础。


---

# 任务 1.2 实施文档

## 任务概述

**任务**: 1.2 配置数据库连接

**需求**: 32.1

**目标**:
- 配置MySQL连接池（使用SQLAlchemy 2.0异步API）
- 配置MongoDB连接（使用Motor异步驱动）
- 配置Redis连接（使用redis-py异步客户端）
- 实现数据库迁移工具（Alembic）
- 在应用启动时初始化数据库连接
- 在应用关闭时正确清理连接
- 提供数据库健康检查功能
- 创建数据库会话管理的依赖注入

## 已完成的工作

### 1. 依赖安装

**文件**: `pyproject.toml`, `requirements.txt`

添加了以下数据库驱动依赖：

**生产依赖**:
- `sqlalchemy ^2.0.25` - SQLAlchemy 2.0异步ORM
- `asyncmy ^0.2.9` - MySQL异步驱动（基于aiomysql）
- `motor ^3.3.2` - MongoDB异步驱动
- `redis[hiredis] ^5.0.1` - Redis异步客户端（包含hiredis加速）
- `alembic ^1.13.1` - 数据库迁移工具

### 2. 数据库配置

**文件**: `app/core/config.py`

在Settings类中添加了完整的数据库配置：

#### MySQL配置
- `mysql_host`: MySQL主机地址（默认localhost）
- `mysql_port`: MySQL端口（默认3306）
- `mysql_user`: MySQL用户名
- `mysql_password`: MySQL密码
- `mysql_database`: MySQL数据库名
- `mysql_pool_size`: 连接池大小（默认10）
- `mysql_max_overflow`: 连接池最大溢出（默认20）
- `mysql_pool_recycle`: 连接回收时间（默认3600秒）
- `mysql_echo`: 是否打印SQL语句（默认False）

#### MongoDB配置
- `mongodb_host`: MongoDB主机地址（默认localhost）
- `mongodb_port`: MongoDB端口（默认27017）
- `mongodb_user`: MongoDB用户名
- `mongodb_password`: MongoDB密码
- `mongodb_database`: MongoDB数据库名
- `mongodb_max_pool_size`: 最大连接池大小（默认100）
- `mongodb_min_pool_size`: 最小连接池大小（默认10）

#### Redis配置
- `redis_host`: Redis主机地址（默认localhost）
- `redis_port`: Redis端口（默认6379）
- `redis_password`: Redis密码
- `redis_db`: Redis数据库编号（默认0）
- `redis_max_connections`: 最大连接数（默认50）
- `redis_socket_timeout`: Socket超时时间（默认5秒）
- `redis_socket_connect_timeout`: 连接超时时间（默认5秒）

#### 连接URL属性
- `mysql_url`: 自动构建MySQL连接URL
- `mongodb_url`: 自动构建MongoDB连接URL

### 3. 数据库连接管理

**文件**: `app/core/database.py`

实现了完整的数据库连接管理系统：

#### MySQL连接管理

1. **引擎和会话工厂**
   - 使用`create_async_engine`创建异步引擎
   - 配置连接池参数（pool_size, max_overflow, pool_recycle）
   - 启用`pool_pre_ping`进行连接健康检查
   - 使用`async_sessionmaker`创建会话工厂

2. **会话管理**
   - `get_mysql_session()`: 异步生成器，提供会话依赖注入
   - 自动管理事务（commit/rollback）
   - 自动关闭会话
   - 支持FastAPI的Depends注入

3. **生命周期管理**
   - `init_mysql()`: 初始化MySQL连接池
   - `close_mysql()`: 关闭MySQL连接池
   - `check_mysql_health()`: 健康检查

4. **SQLAlchemy Base**
   - 定义了`Base = declarative_base()`
   - 所有ORM模型应继承此Base类

#### MongoDB连接管理

1. **客户端和数据库**
   - 使用`AsyncIOMotorClient`创建异步客户端
   - 配置连接池参数（maxPoolSize, minPoolSize）
   - 设置服务器选择超时（5秒）

2. **数据库访问**
   - `get_mongodb_database()`: 获取数据库实例
   - 支持FastAPI的Depends注入

3. **生命周期管理**
   - `init_mongodb()`: 初始化MongoDB连接
   - `close_mongodb()`: 关闭MongoDB连接
   - `check_mongodb_health()`: 健康检查（使用ping命令）

#### Redis连接管理

1. **连接池**
   - 使用`ConnectionPool`创建连接池
   - 配置最大连接数和超时参数
   - 启用`decode_responses`自动解码为字符串

2. **连接管理**
   - `get_redis()`: 异步生成器，提供Redis连接依赖注入
   - 自动关闭连接
   - 支持FastAPI的Depends注入

3. **生命周期管理**
   - `init_redis()`: 初始化Redis连接池
   - `close_redis()`: 关闭Redis连接池
   - `check_redis_health()`: 健康检查（使用ping命令）

#### 统一管理接口

1. **初始化和关闭**
   - `init_databases()`: 初始化所有数据库连接
   - `close_databases()`: 关闭所有数据库连接

2. **健康检查**
   - `check_databases_health()`: 检查所有数据库健康状态
   - 返回字典：`{"mysql": bool, "mongodb": bool, "redis": bool}`

### 4. 应用集成

**文件**: `app/main.py`

在FastAPI应用中集成数据库连接：

1. **生命周期管理**
   - 在`lifespan`函数中调用`init_databases()`
   - 应用启动时初始化所有数据库连接
   - 应用关闭时调用`close_databases()`
   - 正确清理所有数据库连接

2. **健康检查端点**
   - 更新`/health`端点，包含数据库健康状态
   - 返回格式：
     ```json
     {
       "status": "healthy",
       "app": "知域校园互动社交平台",
       "version": "0.1.0",
       "environment": "development",
       "databases": {
         "mysql": true,
         "mongodb": true,
         "redis": true
       }
     }
     ```

### 5. 依赖注入

**文件**: `app/core/dependencies.py`

创建了便捷的依赖注入函数：

1. **MySQL会话注入**
   ```python
   async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
       async for session in get_mysql_session():
           yield session
   ```

2. **MongoDB数据库注入**
   ```python
   def get_mongo_db() -> AsyncIOMotorDatabase:
       return get_mongodb_database()
   ```

3. **Redis客户端注入**
   ```python
   async def get_redis_client() -> AsyncGenerator[Redis, None]:
       async for redis in get_redis():
           yield redis
   ```

**使用示例**:
```python
from fastapi import Depends
from app.core.dependencies import get_db_session, get_mongo_db, get_redis_client

@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(User))
    return result.scalars().all()

@router.get("/posts")
async def get_posts(db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    posts = await db.posts.find().to_list(length=100)
    return posts

@router.get("/cache/{key}")
async def get_cache(key: str, redis: Redis = Depends(get_redis_client)):
    value = await redis.get(key)
    return {"value": value}
```

### 6. Alembic数据库迁移

#### 配置文件

**文件**: `alembic.ini`

- 配置迁移脚本目录为`alembic`
- 设置迁移脚本模板格式
- 配置时区为`Asia/Shanghai`
- 配置日志级别和格式

**文件**: `alembic/env.py`

- 配置Alembic使用异步SQLAlchemy引擎
- 从应用配置读取数据库URL
- 支持离线和在线两种迁移模式
- 使用`run_sync`在异步环境中执行迁移

**文件**: `alembic/script.py.mako`

- 迁移脚本模板
- 包含revision ID、依赖关系等元数据
- 定义upgrade和downgrade函数

#### 使用方式

```bash
# 创建迁移脚本
alembic revision --autogenerate -m "描述信息"

# 升级到最新版本
alembic upgrade head

# 降级一个版本
alembic downgrade -1

# 查看当前版本
alembic current

# 查看迁移历史
alembic history
```

### 7. 数据库CLI工具

**文件**: `app/cli/database.py`

创建了命令行工具用于数据库管理：

1. **初始化命令**
   ```bash
   python -m app.cli.database init
   ```
   - 测试数据库连接初始化
   - 验证配置是否正确

2. **健康检查命令**
   ```bash
   python -m app.cli.database check
   ```
   - 检查所有数据库连接健康状态
   - 显示每个数据库的状态（✓ 健康 / ✗ 不健康）
   - 返回退出码（0=全部健康，1=有不健康）

### 8. Docker Compose配置

**文件**: `docker-compose.yml`

提供了本地开发环境的数据库服务：

1. **MySQL 8.0服务**
   - 容器名：zhiyu-mysql
   - 端口：3306
   - 数据库：zhiyu
   - 用户：zhiyu / zhiyu_password
   - 字符集：utf8mb4
   - 健康检查：mysqladmin ping

2. **MongoDB 7.0服务**
   - 容器名：zhiyu-mongodb
   - 端口：27017
   - 健康检查：mongosh ping

3. **Redis 7服务**
   - 容器名：zhiyu-redis
   - 端口：6379
   - 持久化：AOF
   - 健康检查：redis-cli ping

4. **数据卷**
   - mysql_data: MySQL数据持久化
   - mongodb_data: MongoDB数据持久化
   - mongodb_config: MongoDB配置持久化
   - redis_data: Redis数据持久化

5. **网络**
   - zhiyu-network: 桥接网络

**文件**: `docker/mysql/init.sql`

MySQL初始化脚本：
- 设置数据库字符集为utf8mb4
- 创建测试数据库zhiyu_test
- 授予用户权限

### 9. 环境变量配置

**文件**: `.env.example`

更新了环境变量示例，包含完整的数据库配置：

```bash
# MySQL数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=zhiyu
MYSQL_PASSWORD=zhiyu_password
MYSQL_DATABASE=zhiyu
MYSQL_POOL_SIZE=10
MYSQL_MAX_OVERFLOW=20
MYSQL_POOL_RECYCLE=3600
MYSQL_ECHO=false

# MongoDB配置
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USER=
MONGODB_PASSWORD=
MONGODB_DATABASE=zhiyu
MONGODB_MAX_POOL_SIZE=100
MONGODB_MIN_POOL_SIZE=10

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
```

### 10. 测试

**文件**: `tests/test_database.py`

创建了数据库连接测试：

1. **初始化测试**
   - 测试数据库连接初始化
   - 验证引擎、客户端、连接池创建成功

2. **健康检查测试**
   - 测试健康检查功能
   - 验证返回结果包含所有数据库

3. **会话上下文测试**
   - 测试MySQL会话上下文管理
   - 测试Redis连接上下文管理

### 11. 文档

**文件**: `README.md`

更新了项目文档：
- 添加数据库技术栈说明
- 更新项目结构（包含数据库相关文件）
- 添加数据库准备步骤
- 添加数据库连接检查步骤
- 添加数据库迁移步骤
- 添加数据库管理章节
- 添加数据库使用示例

**文件**: `docs/database-setup.md`

创建了详细的数据库配置指南：
- 数据库架构说明
- 快速启动指南（Docker Compose）
- 手动安装指南（macOS/Linux/Windows）
- 数据库配置详解
- Alembic迁移使用指南
- 代码使用示例
- 故障排查指南
- 性能优化建议
- 备份和恢复指南
- 参考资料链接

## 技术亮点

1. **异步优先**: 所有数据库操作都使用异步API，提高并发性能
2. **连接池管理**: 合理配置连接池参数，优化资源使用
3. **健康检查**: 提供完善的健康检查机制，便于监控
4. **依赖注入**: 使用FastAPI的Depends机制，简化数据库使用
5. **自动管理**: 会话和连接自动管理，防止资源泄漏
6. **配置灵活**: 所有配置从环境变量读取，支持不同环境
7. **迁移工具**: 使用Alembic管理数据库schema变更
8. **开发友好**: 提供Docker Compose快速启动开发环境
9. **文档完善**: 提供详细的配置指南和使用示例
10. **CLI工具**: 提供命令行工具便于数据库管理

## 符合需求

### 需求 32.1: 可扩展性与系统架构

- ✅ 使用连接池管理，支持高并发访问
- ✅ 异步API设计，提高系统性能
- ✅ 支持水平扩展（通过增加连接池大小）
- ✅ 预留了数据库分片和读写分离的扩展空间

## 架构设计

### 连接池架构

```
FastAPI应用
    ↓
依赖注入 (Depends)
    ↓
会话/连接管理器
    ↓
连接池
    ↓
数据库服务器
```

### 生命周期管理

```
应用启动
    ↓
init_databases()
    ├─ init_mysql()      → 创建引擎和会话工厂
    ├─ init_mongodb()    → 创建客户端和数据库实例
    └─ init_redis()      → 创建连接池
    ↓
应用运行
    ├─ 请求处理
    │   ├─ 获取会话/连接 (Depends)
    │   ├─ 执行数据库操作
    │   └─ 自动提交/回滚/关闭
    └─ 健康检查
    ↓
应用关闭
    ↓
close_databases()
    ├─ close_mysql()     → 释放所有连接
    ├─ close_mongodb()   → 关闭客户端
    └─ close_redis()     → 断开连接池
```

## 使用示例

### 1. MySQL使用示例

```python
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.models.user import User

router = APIRouter()

@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db_session)):
    """获取用户列表"""
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users

@router.post("/users")
async def create_user(
    user_data: dict,
    db: AsyncSession = Depends(get_db_session)
):
    """创建用户"""
    user = User(**user_data)
    db.add(user)
    # 会话会自动提交
    return user
```

### 2. MongoDB使用示例

```python
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import get_mongo_db

router = APIRouter()

@router.get("/posts")
async def get_posts(db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    """获取帖子列表"""
    posts = await db.posts.find().to_list(length=100)
    return posts

@router.post("/posts")
async def create_post(
    post_data: dict,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """创建帖子"""
    result = await db.posts.insert_one(post_data)
    post_data["_id"] = str(result.inserted_id)
    return post_data
```

### 3. Redis使用示例

```python
from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from app.core.dependencies import get_redis_client

router = APIRouter()

@router.get("/cache/{key}")
async def get_cache(
    key: str,
    redis: Redis = Depends(get_redis_client)
):
    """获取缓存"""
    value = await redis.get(key)
    return {"key": key, "value": value}

@router.post("/cache/{key}")
async def set_cache(
    key: str,
    value: str,
    redis: Redis = Depends(get_redis_client)
):
    """设置缓存"""
    await redis.set(key, value, ex=3600)  # 1小时过期
    return {"key": key, "value": value}
```

## 验证方式

### 1. 启动数据库服务

```bash
# 使用Docker Compose启动
docker-compose up -d

# 检查服务状态
docker-compose ps
```

### 2. 检查数据库连接

```bash
# 使用CLI工具检查
poetry run python -m app.cli.database check

# 预期输出
mysql: ✓ 健康
mongodb: ✓ 健康
redis: ✓ 健康
```

### 3. 启动应用

```bash
poetry run python run.py
```

### 4. 访问健康检查端点

```bash
curl http://localhost:8000/health
```

预期响应：
```json
{
  "status": "healthy",
  "app": "知域校园互动社交平台",
  "version": "0.1.0",
  "environment": "development",
  "databases": {
    "mysql": true,
    "mongodb": true,
    "redis": true
  }
}
```

### 5. 运行测试

```bash
# 运行数据库测试
poetry run pytest tests/test_database.py -v

# 运行所有测试
poetry run pytest
```

## 性能指标

### 连接池配置

- **MySQL连接池**: 10个基础连接 + 20个溢出连接 = 最多30个并发连接
- **MongoDB连接池**: 10-100个连接，根据负载自动调整
- **Redis连接池**: 最多50个连接

### 预期性能

- **MySQL查询**: < 10ms（简单查询）
- **MongoDB查询**: < 5ms（索引查询）
- **Redis操作**: < 1ms（内存操作）

### 并发能力

- 支持1000+并发请求（取决于数据库服务器性能）
- 连接池自动管理，避免连接耗尽
- 异步操作，不阻塞事件循环

## 安全性

1. **密码保护**: 所有数据库密码从环境变量读取，不硬编码
2. **连接加密**: 支持SSL/TLS连接（需配置）
3. **权限控制**: 使用专用数据库用户，限制权限
4. **SQL注入防护**: 使用ORM参数化查询
5. **连接超时**: 配置合理的超时时间，防止连接泄漏

## 监控和日志

1. **连接池监控**: 可通过日志查看连接池状态
2. **健康检查**: 定期检查数据库连接健康状态
3. **错误日志**: 记录所有数据库错误和异常
4. **性能日志**: 可选启用SQL语句日志（MYSQL_ECHO=true）

## 后续优化

1. **读写分离**: 配置MySQL主从复制，实现读写分离
2. **数据库分片**: 根据业务需求实现数据分片
3. **缓存策略**: 实现多级缓存（Redis + 本地缓存）
4. **连接池优化**: 根据实际负载调整连接池参数
5. **监控告警**: 集成Prometheus监控数据库指标

## 总结

任务 1.2 已成功完成，实现了：

1. ✅ MySQL连接池配置（SQLAlchemy 2.0异步API）
2. ✅ MongoDB连接配置（Motor异步驱动）
3. ✅ Redis连接配置（redis-py异步客户端）
4. ✅ Alembic数据库迁移工具
5. ✅ 应用启动时初始化数据库连接
6. ✅ 应用关闭时正确清理连接
7. ✅ 数据库健康检查功能
8. ✅ 数据库会话管理的依赖注入
9. ✅ Docker Compose开发环境
10. ✅ CLI管理工具
11. ✅ 完善的文档和测试

数据库连接系统已完全配置完成，为后续业务功能开发提供了可靠的数据存储基础。
