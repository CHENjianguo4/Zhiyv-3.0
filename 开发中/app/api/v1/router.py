"""API v1主路由

整合所有v1版本的子路由
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, demo, users, verification, sensitive_words, audit, reports, posts, secondhand

# 创建v1版本的主路由
api_router = APIRouter(prefix="/api/v1")

# 注册演示端点（用于测试统一响应格式和错误处理）
api_router.include_router(demo.router, prefix="/demo", tags=["演示"])

# 注册认证端点
api_router.include_router(auth.router)

# 注册校园身份认证端点
api_router.include_router(verification.router)

# 注册用户端点
api_router.include_router(users.router)

# 注册敏感词管理端点
api_router.include_router(sensitive_words.router)

# 注册内容审核端点
api_router.include_router(audit.router)

# 注册举报管理端点
api_router.include_router(reports.router)

# 注册帖子管理端点
api_router.include_router(posts.router)

# 注册二手商品端点
api_router.include_router(secondhand.router)

# 后续任务将在此处添加子路由
# 例如：
# from app.api.v1.endpoints import circles
# api_router.include_router(circles.router, prefix="/circles", tags=["圈子"])
