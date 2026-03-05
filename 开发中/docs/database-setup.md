# 数据库配置指南

本文档介绍如何配置和使用知域平台的数据库系统。

## 数据库架构

知域平台使用三种数据库：

1. **MySQL 8.0** - 关系型数据库
   - 存储结构化业务数据（用户、订单、课程等）
   - 使用SQLAlchemy 2.0异步ORM
   - 支持事务和复杂查询

2. **MongoDB** - 文档数据库
   - 存储非结构化数据（帖子、评论、消息等）
   - 使用Motor异步驱动
   - 灵活的schema设计

3. **Redis** - 内存数据库
   - 缓存热点数据
   - 会话管理
   - 分布式锁
   - 消息队列

## 快速启动（使用Docker Compose）

### 1. 启动数据库服务

```bash
# 启动所有数据库服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 2. 验证数据库连接

```bash
# 检查MySQL
docker exec -it zhiyu-mysql mysql -uzhiyu -pzhiyu_password -e "SHOW DATABASES;"

# 检查MongoDB
docker exec -it zhiyu-mongodb mongosh --eval "db.adminCommand('ping')"

# 检查Redis
docker exec -it zhiyu-redis redis-cli ping
```

### 3. 配置环境变量

使用Docker Compose时，默认配置已经可以工作：

```bash
cp .env.example .env
# .env文件中的默认配置已经匹配Docker Compose
```

### 4. 运行数据库迁移

```bash
# 创建初始迁移
poetry run alembic revision --autogenerate -m "初始化数据库"

# 执行迁移
poetry run alembic upgrade head
```

### 5. 检查应用连接

```bash
# 使用CLI工具检查数据库健康状态
poetry run python -m app.cli.database check

# 启动应用
poetry run python run.py

# 访问健康检查端点
curl http://localhost:8000/health
```

## 手动安装数据库

如果不使用Docker Compose，可以手动安装数据库服务。

### MySQL 8.0

#### macOS
```bash
brew install mysql@8.0
brew services start mysql@8.0

# 创建数据库和用户
mysql -uroot -p
CREATE DATABASE zhiyu CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'zhiyu'@'localhost' IDENTIFIED BY 'zhiyu_password';
GRANT ALL PRIVILEGES ON zhiyu.* TO 'zhiyu'@'localhost';
FLUSH PRIVILEGES;
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install mysql-server-8.0
sudo systemctl start mysql

# 创建数据库和用户（同上）
```

#### Windows
1. 下载MySQL 8.0安装包：https://dev.mysql.com/downloads/mysql/
2. 运行安装程序
3. 使用MySQL Workbench或命令行创建数据库和用户

### MongoDB

#### macOS
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

#### Ubuntu/Debian
```bash
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl start mongod
```

#### Windows
1. 下载MongoDB安装包：https://www.mongodb.com/try/download/community
2. 运行安装程序
3. 启动MongoDB服务

### Redis

#### macOS
```bash
brew install redis
brew services start redis
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
```

#### Windows
1. 下载Redis for Windows：https://github.com/microsoftarchive/redis/releases
2. 解压并运行redis-server.exe

## 数据库配置

### 环境变量

在`.env`文件中配置数据库连接：

```bash
# MySQL配置
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

### 连接池配置

#### MySQL连接池
- `MYSQL_POOL_SIZE`: 连接池大小（默认10）
- `MYSQL_MAX_OVERFLOW`: 最大溢出连接数（默认20）
- `MYSQL_POOL_RECYCLE`: 连接回收时间，秒（默认3600）

#### MongoDB连接池
- `MONGODB_MAX_POOL_SIZE`: 最大连接池大小（默认100）
- `MONGODB_MIN_POOL_SIZE`: 最小连接池大小（默认10）

#### Redis连接池
- `REDIS_MAX_CONNECTIONS`: 最大连接数（默认50）
- `REDIS_SOCKET_TIMEOUT`: Socket超时时间，秒（默认5）
- `REDIS_SOCKET_CONNECT_TIMEOUT`: 连接超时时间，秒（默认5）

## 数据库迁移

### Alembic使用

Alembic是SQLAlchemy的数据库迁移工具，用于管理MySQL schema变更。

#### 创建迁移脚本

```bash
# 自动生成迁移脚本（推荐）
poetry run alembic revision --autogenerate -m "描述信息"

# 手动创建空白迁移脚本
poetry run alembic revision -m "描述信息"
```

#### 执行迁移

```bash
# 升级到最新版本
poetry run alembic upgrade head

# 升级到特定版本
poetry run alembic upgrade <revision>

# 升级一个版本
poetry run alembic upgrade +1
```

#### 回滚迁移

```bash
# 降级一个版本
poetry run alembic downgrade -1

# 降级到特定版本
poetry run alembic downgrade <revision>

# 降级到初始状态
poetry run alembic downgrade base
```

#### 查看迁移状态

```bash
# 查看当前版本
poetry run alembic current

# 查看迁移历史
poetry run alembic history

# 查看详细历史
poetry run alembic history --verbose
```

### 迁移最佳实践

1. **在创建迁移前确保模型已定义**
   - 所有SQLAlchemy模型都应该继承自`app.core.database.Base`
   - 模型应该在`alembic/env.py`中导入

2. **检查自动生成的迁移脚本**
   - 自动生成的脚本可能不完整
   - 手动检查并修改迁移脚本
   - 特别注意索引、外键、默认值

3. **测试迁移**
   - 在测试环境先执行迁移
   - 测试升级和降级
   - 确保数据不会丢失

4. **版本控制**
   - 迁移脚本应该纳入Git版本控制
   - 不要修改已经部署的迁移脚本
   - 如需修改，创建新的迁移脚本

## 在代码中使用数据库

### MySQL (SQLAlchemy)

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
    await db.commit()
    await db.refresh(user)
    return user
```

### MongoDB (Motor)

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

### Redis

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

## 数据库健康检查

### 使用CLI工具

```bash
# 检查所有数据库健康状态
poetry run python -m app.cli.database check
```

### 使用HTTP端点

```bash
# 访问健康检查端点
curl http://localhost:8000/health

# 响应示例
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

### 在代码中检查

```python
from app.core.database import check_databases_health

async def check_health():
    health = await check_databases_health()
    print(f"MySQL: {'✓' if health['mysql'] else '✗'}")
    print(f"MongoDB: {'✓' if health['mongodb'] else '✗'}")
    print(f"Redis: {'✓' if health['redis'] else '✗'}")
```

## 故障排查

### MySQL连接失败

1. **检查MySQL服务是否运行**
   ```bash
   # Docker
   docker-compose ps mysql
   
   # macOS
   brew services list | grep mysql
   
   # Linux
   sudo systemctl status mysql
   ```

2. **检查连接配置**
   - 确认主机、端口、用户名、密码正确
   - 确认数据库已创建
   - 确认用户有访问权限

3. **检查防火墙**
   - 确保3306端口未被阻止

### MongoDB连接失败

1. **检查MongoDB服务是否运行**
   ```bash
   # Docker
   docker-compose ps mongodb
   
   # macOS
   brew services list | grep mongodb
   
   # Linux
   sudo systemctl status mongod
   ```

2. **检查连接配置**
   - 确认主机和端口正确
   - 如果设置了认证，确认用户名和密码正确

### Redis连接失败

1. **检查Redis服务是否运行**
   ```bash
   # Docker
   docker-compose ps redis
   
   # macOS
   brew services list | grep redis
   
   # Linux
   sudo systemctl status redis-server
   ```

2. **检查连接配置**
   - 确认主机和端口正确
   - 如果设置了密码，确认密码正确

### 连接池耗尽

如果遇到连接池耗尽错误：

1. **增加连接池大小**
   ```bash
   MYSQL_POOL_SIZE=20
   MYSQL_MAX_OVERFLOW=40
   ```

2. **检查连接泄漏**
   - 确保使用`Depends(get_db_session)`自动管理会话
   - 不要手动创建会话而不关闭

3. **优化查询**
   - 减少长时间运行的查询
   - 使用索引优化查询性能

## 性能优化

### MySQL优化

1. **使用索引**
   ```python
   from sqlalchemy import Index
   
   Index('idx_user_email', User.email)
   Index('idx_post_created', Post.created_at.desc())
   ```

2. **批量操作**
   ```python
   # 批量插入
   db.add_all([user1, user2, user3])
   await db.commit()
   ```

3. **预加载关联**
   ```python
   from sqlalchemy.orm import selectinload
   
   result = await db.execute(
       select(User).options(selectinload(User.posts))
   )
   ```

### MongoDB优化

1. **创建索引**
   ```python
   await db.posts.create_index("author_id")
   await db.posts.create_index([("created_at", -1)])
   ```

2. **使用投影**
   ```python
   # 只返回需要的字段
   posts = await db.posts.find(
       {},
       {"title": 1, "author_id": 1, "_id": 0}
   ).to_list(length=100)
   ```

### Redis优化

1. **设置过期时间**
   ```python
   await redis.set("key", "value", ex=3600)
   ```

2. **使用管道**
   ```python
   pipe = redis.pipeline()
   pipe.set("key1", "value1")
   pipe.set("key2", "value2")
   await pipe.execute()
   ```

3. **使用哈希存储对象**
   ```python
   await redis.hset("user:1", mapping={
       "name": "张三",
       "email": "zhangsan@example.com"
   })
   ```

## 备份和恢复

### MySQL备份

```bash
# 备份数据库
docker exec zhiyu-mysql mysqldump -uzhiyu -pzhiyu_password zhiyu > backup.sql

# 恢复数据库
docker exec -i zhiyu-mysql mysql -uzhiyu -pzhiyu_password zhiyu < backup.sql
```

### MongoDB备份

```bash
# 备份数据库
docker exec zhiyu-mongodb mongodump --db=zhiyu --out=/backup

# 恢复数据库
docker exec zhiyu-mongodb mongorestore --db=zhiyu /backup/zhiyu
```

### Redis备份

```bash
# Redis会自动保存RDB文件到/data目录
# 手动触发保存
docker exec zhiyu-redis redis-cli SAVE

# 复制RDB文件
docker cp zhiyu-redis:/data/dump.rdb ./backup/
```

## 参考资料

- [SQLAlchemy 2.0文档](https://docs.sqlalchemy.org/en/20/)
- [Motor文档](https://motor.readthedocs.io/)
- [redis-py文档](https://redis-py.readthedocs.io/)
- [Alembic文档](https://alembic.sqlalchemy.org/)
- [MySQL 8.0文档](https://dev.mysql.com/doc/refman/8.0/en/)
- [MongoDB文档](https://www.mongodb.com/docs/)
- [Redis文档](https://redis.io/documentation)
