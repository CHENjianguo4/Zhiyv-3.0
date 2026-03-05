# 🚀 快速启动指南

## 第一次使用？按照以下步骤操作

### 步骤 1：安装 Docker Desktop

1. 访问 https://www.docker.com/products/docker-desktop/
2. 下载 Windows 版本
3. 安装并启动 Docker Desktop
4. 等待 Docker 引擎启动（系统托盘图标变为绿色）

### 步骤 2：安装 Python 依赖

打开 PowerShell 或 CMD，在项目目录下运行：

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境（PowerShell）
.\venv\Scripts\Activate.ps1

# 或者（CMD）
.\venv\Scripts\activate.bat

# 安装依赖
pip install -r requirements.txt
```

### 步骤 3：配置环境变量

```bash
# 复制环境变量模板
copy .env.example .env
```

### 步骤 4：一键启动

#### 使用 PowerShell（推荐）：
```powershell
.\start-dev.ps1
```

#### 使用 CMD：
```cmd
start-dev.bat
```

### 步骤 5：访问 API 文档

在浏览器中打开：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🎯 现在可以做什么？

### 1. 浏览 API 文档
访问 http://localhost:8000/docs 查看所有可用的接口

### 2. 测试用户注册和登录

在 Swagger UI 中：
1. 找到 `POST /api/v1/auth/wechat-login`
2. 点击 "Try it out"
3. 输入：
   ```json
   {
     "code": "test_code_123"
   }
   ```
4. 点击 "Execute"
5. 复制返回的 `access_token`

### 3. 测试用户信息查询

1. 找到 `GET /api/v1/users/{user_id}`
2. 点击 "Try it out"
3. 输入 user_id: `1`
4. 点击右上角的 🔒 图标，输入 token：`Bearer YOUR_ACCESS_TOKEN`
5. 点击 "Execute"

### 4. 测试信用分查询

1. 找到 `GET /api/v1/users/{user_id}/credit`
2. 使用相同的方式测试

---

## 📊 已实现的功能

### ✅ 用户认证模块
- 微信授权登录
- 校园身份认证
- 验证码发送

### ✅ 用户管理模块
- 获取用户信息
- 更新用户档案
- 隐私信息脱敏

### ✅ 信用分管理
- 查询信用分
- 调整信用分
- 信用分历史记录

### ✅ 权限管理
- 基于角色的权限控制
- 基于信用分的权限限制
- JWT Token 认证

---

## 🛠️ 常用命令

### 查看数据库
```bash
# 进入 MySQL
docker compose exec mysql mysql -uzhiyu -pzhiyu_password zhiyu

# 查看所有表
SHOW TABLES;

# 查看用户数据
SELECT * FROM users;
```

### 查看日志
```bash
# 查看容器日志
docker compose logs -f mysql

# 查看应用日志
# 在运行 python run.py 的终端查看
```

### 停止服务
```bash
# 停止开发服务器：按 Ctrl+C

# 停止数据库容器
docker compose stop

# 停止并删除容器
docker compose down
```

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/services/test_auth.py -v

# 查看测试覆盖率
pytest --cov=app --cov-report=html
```

---

## ❓ 遇到问题？

### Docker 启动失败
- 确保 Docker Desktop 正在运行
- 检查系统托盘图标是否为绿色
- 尝试重启 Docker Desktop

### 端口被占用
如果 8000 端口被占用，修改 `.env` 文件：
```env
PORT=8001
```

### 数据库连接失败
```bash
# 检查容器状态
docker compose ps

# 重启容器
docker compose restart mysql
```

### 更多帮助
查看详细文档：`docs/getting-started.md`

---

## 📚 下一步

1. ✅ 熟悉 API 文档和接口
2. ✅ 查看数据库表结构
3. ✅ 运行测试套件
4. ✅ 继续开发新功能（任务 3.1：敏感词管理）

---

## 🎉 开始探索吧！

现在你已经准备好了！打开浏览器访问：
👉 http://localhost:8000/docs

祝你开发愉快！🚀
