"""认证服务测试

测试微信登录、Token刷新等功能
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.auth import AuthService
from app.services.wechat import WeChatOAuthService
from app.models.user import User, UserRole, UserStatus


@pytest.fixture
def mock_session():
    """模拟数据库会话"""
    return AsyncMock()


@pytest.fixture
def mock_wechat_service():
    """模拟微信OAuth服务"""
    service = AsyncMock(spec=WeChatOAuthService)
    return service


@pytest.fixture
def auth_service(mock_session, mock_wechat_service):
    """创建认证服务实例"""
    return AuthService(mock_session, mock_wechat_service)


@pytest.mark.asyncio
async def test_wechat_login_new_user(auth_service, mock_wechat_service, mock_session):
    """测试新用户微信登录"""
    # 准备测试数据
    test_code = "test_code_123"
    test_openid = "test_openid_123"
    test_nickname = "测试用户"
    test_avatar = "https://example.com/avatar.jpg"
    
    # 模拟微信API返回
    mock_wechat_service.code2session.return_value = {
        "openid": test_openid,
        "session_key": "test_session_key",
        "unionid": None,
    }
    
    # 模拟用户不存在（首次登录）
    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_openid.return_value = None
    
    # 模拟创建新用户
    new_user = User(
        id=1,
        wechat_openid=test_openid,
        nickname=test_nickname,
        avatar=test_avatar,
        role=UserRole.STUDENT,
        verified=False,
        credit_score=80,
        status=UserStatus.ACTIVE,
    )
    mock_user_repo.create.return_value = new_user
    
    auth_service.user_repo = mock_user_repo
    
    # 执行登录
    result = await auth_service.wechat_login(
        code=test_code,
        nickname=test_nickname,
        avatar=test_avatar,
    )
    
    # 验证结果
    assert "access_token" in result
    assert "refresh_token" in result
    assert result["token_type"] == "bearer"
    assert result["user"]["id"] == 1
    assert result["user"]["nickname"] == test_nickname
    assert result["user"]["verified"] is False
    assert result["user"]["credit_score"] == 80
    
    # 验证调用
    mock_wechat_service.code2session.assert_called_once_with(test_code)
    mock_user_repo.get_by_openid.assert_called_once_with(test_openid)
    mock_user_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_wechat_login_existing_user(auth_service, mock_wechat_service, mock_session):
    """测试已存在用户微信登录"""
    # 准备测试数据
    test_code = "test_code_123"
    test_openid = "test_openid_123"
    
    # 模拟微信API返回
    mock_wechat_service.code2session.return_value = {
        "openid": test_openid,
        "session_key": "test_session_key",
        "unionid": None,
    }
    
    # 模拟用户已存在
    existing_user = User(
        id=1,
        wechat_openid=test_openid,
        nickname="已存在用户",
        avatar="https://example.com/old_avatar.jpg",
        role=UserRole.STUDENT,
        verified=True,
        credit_score=85,
        status=UserStatus.ACTIVE,
    )
    
    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_openid.return_value = existing_user
    mock_user_repo.update.return_value = existing_user
    
    auth_service.user_repo = mock_user_repo
    
    # 执行登录
    result = await auth_service.wechat_login(
        code=test_code,
        nickname="新昵称",
        avatar="https://example.com/new_avatar.jpg",
    )
    
    # 验证结果
    assert "access_token" in result
    assert "refresh_token" in result
    assert result["user"]["id"] == 1
    assert result["user"]["verified"] is True
    
    # 验证调用
    mock_wechat_service.code2session.assert_called_once_with(test_code)
    mock_user_repo.get_by_openid.assert_called_once_with(test_openid)
    mock_user_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_access_token(auth_service, mock_session):
    """测试刷新访问令牌"""
    # 准备测试数据
    user = User(
        id=1,
        wechat_openid="test_openid",
        nickname="测试用户",
        role=UserRole.STUDENT,
        verified=True,
        credit_score=80,
        status=UserStatus.ACTIVE,
    )
    
    mock_user_repo = AsyncMock()
    mock_user_repo.get_by_id.return_value = user
    
    auth_service.user_repo = mock_user_repo
    
    # 创建一个有效的refresh token
    from app.core.security import create_refresh_token
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    # 执行刷新
    result = await auth_service.refresh_access_token(refresh_token)
    
    # 验证结果
    assert "access_token" in result
    assert result["token_type"] == "bearer"
    
    # 验证调用
    mock_user_repo.get_by_id.assert_called_once_with(1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
