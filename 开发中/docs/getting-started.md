# 知域平台 - 快速开始指南

## 前置要求

在开始之前，请确保你的系统已安装以下软件：

### 1. Python 3.11+
检查 Python 版本：
```bash
python --version
```

如果未安装，请从 [Python 官网](https://www.python.org/downloads/) 下载安装。

### 2. Docker Desktop（用于运行数据库）

#### Windows 安装步骤：

1. 访问 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. 下载并安装 Docker Desktop
3. 安装完成后，启动 Docker Desktop
4. 等待 Docker 引擎启动完成（系统托盘图标变为绿色）

验证安装：
```bash
docker --version
docker compose version
```

### 3. Git（可选，用于版本控制）
```bash
git --version
```

---

## 安装步骤

### 步骤 1：安装 Python 依赖

在项目根目录下运行：

```bash
# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
.\venv\Scripts\activate.bat

# 安装依赖
pip install -r requirements.txt
```

### 步骤 2：配置环境变量

复制环境变量模板：
```bash
copy .env.example .env
```

编辑 `.env` 文件，确保以下配置正确：
```env
# 应用配置
APP_NAME=知域校园互动社交平台
ENVIRONMENT=development
DEBUG=True
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=mysql+aiomysql://zhiyu:zhiyu_password@localhost:3306/zhiyu
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=zhiyu

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# JWT 配置
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 微信配置（开发环境可以使用测试值）
WECHAT_APP_ID=your_wechat_app_id
WECHAT_APP_SECRET=your_wechat_app_secret

# 日志配置
LOG_LEVEL=INFO
```

### 步骤 3：启动数据库服务

确保 Docker Desktop 正在运行，然后执行：

```bash
# 启动 MySQL 和 Redis
docker compose up -d mysql redis

# 查看容器状态
docker compose ps

# 查看日志（可选）
docker compose logs -f mysql
```

等待数据库启动完成（大约 30 秒）。

### 步骤 4：初始化数据库

运行数据库迁移：

```bash
# 升级到最新版本
alembic upgrade head

# 查看迁移历史
alembic history
```

### 步骤 5：启动开发服务器

```bash
python run.py
```

你应该看到类似以下的输出：
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## 访问 API 文档

服务器启动后，在浏览器中访问：

### 🎯 Swagger UI（推荐）
**地址：** http://localhost:8000/docs

功能：
- 查看所有 API 接口
- 在线测试接口
- 查看请求/响应格式
- 自动生成代码示例

### 📚 ReDoc
**地址：** http://localhost:8000/redoc

功能：
- 更美观的文档展示
- 适合阅读和分享

### 🔍 健康检查
**地址：** http://localhost:8000/health

返回：
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## 测试 API

### 方法 1：使用 Swagger UI（最简单）

1. 访问 http://localhost:8000/docs
2. 找到 `/api/v1/auth/wechat-login` 接口
3. 点击 "Try it out"
4. 输入测试数据：
   ```json
   {
     "code": "test_code_123"
   }
   ```
5. 点击 "Execute"
6. 查看响应结果

### 方法 2：使用 curl

```bash
# 测试微信登录
curl -X POST http://localhost:8000/api/v1/auth/wechat-login \
  -H "Content-Type: application/json" \
  -d "{\"code\": \"test_code_123\"}"

# 获取用户信息（需要先登录获取 token）
curl -X GET http://localhost:8000/api/v1/users/1 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 方法 3：使用 Postman

1. 下载 [Postman](https://www.postman.com/downloads/)
2. 导入 API 集合（可以从 Swagger UI 导出）
3. 创建请求并测试

---

## 常见问题

### Q1: Docker 容器启动失败

**检查 Docker Desktop 是否运行：**
```bash
docker ps
```

**查看容器日志：**
```bash
docker compose logs mysql
docker compose logs redis
```

**重启容器：**
```bash
docker compose down
docker compose up -d mysql redis
```

### Q2: 数据库连接失败

**检查数据库是否就绪：**
```bash
docker compose exec mysql mysql -uzhiyu -pzhiyu_password -e "SELECT 1"
```

**检查端口是否被占用：**
```bash
netstat -ano | findstr :3306
netstat -ano | findstr :6379
```

### Q3: 端口 8000 被占用

修改 `.env` 文件中的 `PORT` 配置：
```env
PORT=8001
```

或者在启动时指定：
```bash
uvicorn app.main:app --port 8001
```

### Q4: 虚拟环境激活失败（PowerShell）

如果遇到执行策略错误，以管理员身份运行 PowerShell：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Q5: 依赖安装失败

尝试使用国内镜像源：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 停止服务

### 停止开发服务器
在运行 `python run.py` 的终端按 `Ctrl+C`

### 停止数据库容器
```bash
# 停止但保留数据
docker compose stop

# 停止并删除容器（数据会保留在 volume 中）
docker compose down

# 停止并删除所有数据（慎用！）
docker compose down -v
```

---

## 开发工作流

### 日常开发流程

1. **启动数据库**
   ```bash
   docker compose up -d mysql redis
   ```

2. **激活虚拟环境**
   ```bash
   .\venv\Scripts\Activate.ps1
   ```

3. **启动开发服务器**
   ```bash
   python run.py
   ```

4. **开始开发**
   - 修改代码
   - 服务器会自动重载（热重载）
   - 在浏览器中测试 API

5. **运行测试**
   ```bash
   pytest
   ```

6. **提交代码**
   ```bash
   git add .
   git commit -m "feat: 添加新功能"
   ```

### 数据库迁移流程

当修改数据模型后：

```bash
# 1. 生成迁移文件
alembic revision --autogenerate -m "描述变更内容"

# 2. 查看生成的迁移文件
# 文件位置：alembic/versions/xxx_描述变更内容.py

# 3. 应用迁移
alembic upgrade head

# 4. 回滚迁移（如果需要）
alembic downgrade -1
```

---

## 下一步

现在你已经成功启动了开发环境！接下来可以：

1. ✅ 浏览 API 文档：http://localhost:8000/docs
2. ✅ 测试已实现的接口
3. ✅ 查看数据库中的数据
4. ✅ 继续开发新功能（任务 3.1：敏感词管理）

---

## 有用的命令

```bash
# 查看所有容器
docker compose ps

# 查看容器日志
docker compose logs -f

# 进入 MySQL 容器
docker compose exec mysql mysql -uzhiyu -pzhiyu_password zhiyu

# 进入 Redis 容器
docker compose exec redis redis-cli

# 查看数据库表
docker compose exec mysql mysql -uzhiyu -pzhiyu_password zhiyu -e "SHOW TABLES"

# 重启服务
docker compose restart mysql

# 查看 Python 依赖
pip list

# 更新依赖
pip install --upgrade -r requirements.txt
```

---

## 需要帮助？

- 查看项目文档：`docs/` 目录
- 查看 API 文档：http://localhost:8000/docs
- 查看数据库设计：`docs/database-setup.md`
- 查看实现进度：`.kiro/specs/zhiyu-campus-social-platform/tasks.md`
