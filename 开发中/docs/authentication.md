# 认证系统使用文档

## 概述

知域平台使用微信小程序OAuth + JWT Token的认证方案，提供安全可靠的用户身份验证。

## 认证流程

### 1. 微信授权登录

**端点:** `POST /api/v1/auth/wechat-login`

**请求示例:**
```json
{
  "code": "微信登录凭证code",
  "nickname": "用户昵称（可选）",
  "avatar": "用户头像URL（可选）"
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "nickname": "用户昵称",
      "avatar": "https://example.com/avatar.jpg",
      "role": "student",
      "verified": false,
      "credit_score": 80,
      "status": "active"
    }
  }
}
```

**说明:**
- 首次登录会自动创建用户账号
- 返回的`access_token`用于后续API调用
- 返回的`refresh_token`用于刷新访问令牌
- 访问令牌默认有效期24小时
- 刷新令牌默认有效期7天

### 2. 使用访问令牌

在后续的API请求中，需要在请求头中携带访问令牌：

```
Authorization: Bearer {access_token}
```

**示例:**
```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 3. 刷新访问令牌

当访问令牌过期时，使用刷新令牌获取新的访问令牌。

**端点:** `POST /api/v1/auth/refresh-token`

**请求示例:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "令牌刷新成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

## 权限控制

### 获取当前用户

在路由处理器中使用依赖注入获取当前登录用户：

```python
from fastapi import Depends
from app.core.dependencies import get_current_user
from app.models.user import User

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "nickname": current_user.nickname,
    }
```

### 要求已认证用户

某些操作需要用户完成校园身份认证：

```python
from fastapi import Depends
from app.core.dependencies import get_current_verified_user
from app.models.user import User

@router.post("/posts")
async def create_post(
    current_user: User = Depends(get_current_verified_user)
):
    # 只有已认证用户才能发布帖子
    pass
```

## 配置

在`.env`文件中配置以下参数：

```env
# JWT配置
JWT_SECRET_KEY=your-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
JWT_REFRESH_EXPIRE_MINUTES=10080

# 微信配置
WECHAT_APP_ID=your-wechat-app-id
WECHAT_APP_SECRET=your-wechat-app-secret
```

**重要提示:**
- `JWT_SECRET_KEY`必须使用强随机字符串，生产环境中务必修改
- 妥善保管微信`APP_SECRET`，不要泄露

## 错误处理

### 常见错误码

| 错误码 | 说明 | HTTP状态码 |
|--------|------|-----------|
| WECHAT_AUTH_FAILED | 微信授权失败 | 400 |
| WECHAT_SERVICE_UNAVAILABLE | 微信服务不可用 | 400 |
| INVALID_TOKEN | 无效的认证令牌 | 401 |
| INVALID_TOKEN_TYPE | 令牌类型不匹配 | 401 |
| USER_NOT_FOUND | 用户不存在 | 400 |
| USER_ACCOUNT_DISABLED | 用户账号已被禁用 | 400 |
| VERIFICATION_REQUIRED | 需要完成校园身份认证 | 401 |

### 错误响应示例

```json
{
  "code": 401,
  "message": "无效的认证令牌",
  "error": {
    "type": "AuthenticationException",
    "error_code": "INVALID_TOKEN"
  },
  "timestamp": 1234567890,
  "requestId": "uuid"
}
```

## 安全建议

1. **HTTPS传输**: 生产环境必须使用HTTPS加密传输
2. **Token存储**: 小程序端应将token存储在安全的storage中
3. **Token刷新**: 访问令牌过期前主动刷新，避免用户体验中断
4. **密钥管理**: JWT密钥定期轮换，使用强随机字符串
5. **日志记录**: 记录所有认证相关的操作日志，便于审计

## 测试

运行认证服务测试：

```bash
pytest tests/services/test_auth.py -v
```

## 下一步

- 实现校园身份认证功能（Task 2.4）
- 实现基于角色的权限控制（Task 2.10）
- 实现信用分体系（Task 2.8）
