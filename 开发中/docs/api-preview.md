# 知域平台 API 文档预览

## 已实现的模块

### 1. 用户认证模块

#### 1.1 微信授权登录
```
POST /api/v1/auth/wechat-login
```

**请求体：**
```json
{
  "code": "string"  // 微信授权码
}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "nickname": "用户昵称",
      "avatar": "https://...",
      "verified": false,
      "credit_score": 80,
      "role": "student"
    }
  }
}
```

#### 1.2 校园身份认证
```
POST /api/v1/auth/verify
```

**请求头：**
```
Authorization: Bearer {access_token}
```

**请求体：**
```json
{
  "student_id": "2021001234",
  "real_name": "张三",
  "email": "zhangsan@university.edu.cn"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "认证成功",
  "data": {
    "verified": true,
    "user_id": 1
  }
}
```

#### 1.3 发送验证码
```
POST /api/v1/verification/send
```

**请求体：**
```json
{
  "email": "zhangsan@university.edu.cn",
  "purpose": "identity_verification"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "验证码已发送",
  "data": {
    "expires_in": 300
  }
}
```

---

### 2. 用户管理模块

#### 2.1 获取用户信息
```
GET /api/v1/users/{user_id}
```

**请求头：**
```
Authorization: Bearer {access_token}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "nickname": "用户昵称",
    "avatar": "https://...",
    "verified": true,
    "credit_score": 80,
    "points": 100,
    "role": "student",
    "profile": {
      "grade": "2021级",
      "major": "计算机科学与技术",
      "campus": "本部",
      "tags": ["编程", "运动", "音乐"],
      "bio": "个人简介"
    }
  }
}
```

#### 2.2 更新用户档案
```
PUT /api/v1/users/{user_id}/profile
```

**请求头：**
```
Authorization: Bearer {access_token}
```

**请求体：**
```json
{
  "nickname": "新昵称",
  "avatar": "https://...",
  "grade": "2021级",
  "major": "计算机科学与技术",
  "campus": "本部",
  "tags": ["编程", "运动"],
  "bio": "这是我的个人简介"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "档案更新成功",
  "data": {
    "id": 1,
    "nickname": "新昵称",
    "profile": { ... }
  }
}
```

#### 2.3 获取当前用户信息
```
GET /api/v1/users/me
```

**请求头：**
```
Authorization: Bearer {access_token}
```

**响应：** 同 2.1

---

### 3. 信用分管理模块

#### 3.1 查询用户信用分
```
GET /api/v1/users/{user_id}/credit
```

**请求头：**
```
Authorization: Bearer {access_token}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_id": 1,
    "credit_score": 80,
    "history": [
      {
        "id": 1,
        "change_amount": -5,
        "reason": "订单超时未完成",
        "related_type": "order",
        "related_id": 123,
        "created_at": "2024-01-15T10:30:00"
      },
      {
        "id": 2,
        "change_amount": 3,
        "reason": "完成交易获得好评",
        "related_type": "order",
        "related_id": 124,
        "created_at": "2024-01-16T14:20:00"
      }
    ]
  }
}
```

#### 3.2 调整用户信用分（管理员）
```
POST /api/v1/users/{user_id}/credit
```

**请求头：**
```
Authorization: Bearer {admin_access_token}
```

**请求体：**
```json
{
  "change_amount": -10,
  "reason": "发布违规内容",
  "related_type": "post",
  "related_id": 456
}
```

**响应：**
```json
{
  "code": 200,
  "message": "信用分调整成功",
  "data": {
    "user_id": 1,
    "credit_score": 70,
    "change_amount": -10
  }
}
```

---

### 4. 权限验证

所有需要认证的接口都需要在请求头中携带 JWT Token：

```
Authorization: Bearer {access_token}
```

#### 权限级别：
- **未认证用户**：只能浏览内容，不能发布、交易、评分
- **认证用户**：可以使用所有基础功能
- **信用分 < 60**：限制接单、发布和交易权限
- **信用分 < 30**：禁止所有交易和发布功能
- **管理员**：拥有后台管理权限

---

## 错误响应格式

所有错误响应遵循统一格式：

```json
{
  "code": 400,
  "message": "错误描述",
  "error": "详细错误信息",
  "timestamp": 1705305600,
  "request_id": "uuid"
}
```

### 常见错误码：
- `400` - 请求参数错误
- `401` - 未授权（Token 无效或过期）
- `403` - 权限不足
- `404` - 资源不存在
- `409` - 资源冲突（如重复注册）
- `422` - 验证失败
- `500` - 服务器内部错误

---

## 如何测试

### 方式 1：启动开发服务器（推荐）

如果你已安装 Docker：

```bash
# 1. 启动数据库
docker compose up -d mysql redis

# 2. 运行数据库迁移
alembic upgrade head

# 3. 启动开发服务器
python run.py
```

然后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 方式 2：运行测试套件

```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/services/test_auth.py -v
pytest tests/services/test_credit.py -v
pytest tests/api/test_users.py -v

# 查看测试覆盖率
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### 方式 3：使用 curl 测试

```bash
# 测试微信登录
curl -X POST http://localhost:8000/api/v1/auth/wechat-login \
  -H "Content-Type: application/json" \
  -d '{"code": "test_code"}'

# 获取用户信息
curl -X GET http://localhost:8000/api/v1/users/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 数据库表结构

### users 表
```sql
CREATE TABLE users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  wechat_openid VARCHAR(64) UNIQUE NOT NULL,
  nickname VARCHAR(50),
  avatar VARCHAR(255),
  school_id BIGINT NOT NULL,
  student_id VARCHAR(50),
  real_name VARCHAR(50),
  email VARCHAR(100),
  verified BOOLEAN DEFAULT FALSE,
  credit_score INT DEFAULT 80,
  points INT DEFAULT 0,
  role ENUM('student', 'teacher', 'merchant', 'admin'),
  status ENUM('active', 'banned', 'deleted'),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### user_profiles 表
```sql
CREATE TABLE user_profiles (
  user_id BIGINT PRIMARY KEY,
  grade VARCHAR(20),
  major VARCHAR(100),
  campus VARCHAR(50),
  tags JSON,
  bio TEXT,
  privacy_settings JSON
);
```

### credit_logs 表
```sql
CREATE TABLE credit_logs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  change_amount INT NOT NULL,
  reason VARCHAR(255),
  related_type ENUM('post', 'order', 'rating', 'violation'),
  related_id BIGINT,
  created_at TIMESTAMP
);
```

---

## 下一步

当前已完成：
- ✅ 用户注册与微信授权
- ✅ 校园身份认证
- ✅ 用户档案管理
- ✅ 信用分体系
- ✅ 权限管理系统

正在进行：
- 🔄 敏感词管理（任务 3.1）

待实现：
- ⏳ 内容审核引擎
- ⏳ 校园圈子与帖子
- ⏳ 二手交易
- ⏳ 更多功能...
