"""用户档案管理API测试

测试用户档案查询、更新和兴趣标签管理功能
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserProfile


@pytest.mark.asyncio
class TestProfileManagement:
    """用户档案管理测试类"""

    async def test_get_user_profile_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_user_profile: UserProfile,
    ):
        """测试获取用户档案成功"""
        response = await async_client.get(f"/api/v1/users/{test_user.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["code"] == 200
        assert data["data"]["id"] == test_user.id
        assert data["data"]["nickname"] == test_user.nickname
        assert data["data"]["grade"] == test_user_profile.grade
        assert data["data"]["major"] == test_user_profile.major
        assert data["data"]["campus"] == test_user_profile.campus
        
        # 验证脱敏
        assert "****" in data["data"]["student_id_masked"]
        assert data["data"]["student_id_masked"] != test_user.student_id

    async def test_get_user_profile_not_found(
        self,
        async_client: AsyncClient,
    ):
        """测试获取不存在的用户档案"""
        response = await async_client.get("/api/v1/users/999999")
        
        assert response.status_code == 404

    async def test_update_user_profile_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_user_profile: UserProfile,
    ):
        """测试更新用户档案成功"""
        update_data = {
            "nickname": "新昵称",
            "grade": "2024级",
            "major": "软件工程",
            "campus": "新校区",
            "bio": "这是我的新简介",
        }
        
        response = await async_client.put(
            f"/api/v1/users/{test_user.id}/profile",
            json=update_data,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["code"] == 200
        assert data["data"]["nickname"] == "新昵称"
        assert data["data"]["grade"] == "2024级"
        assert data["data"]["major"] == "软件工程"
        assert data["data"]["campus"] == "新校区"
        assert data["data"]["bio"] == "这是我的新简介"

    async def test_update_user_profile_partial(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_user_profile: UserProfile,
    ):
        """测试部分更新用户档案"""
        # 只更新昵称
        update_data = {
            "nickname": "只改昵称",
        }
        
        response = await async_client.put(
            f"/api/v1/users/{test_user.id}/profile",
            json=update_data,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["code"] == 200
        assert data["data"]["nickname"] == "只改昵称"
        # 其他字段保持不变
        assert data["data"]["grade"] == test_user_profile.grade
        assert data["data"]["major"] == test_user_profile.major

    async def test_update_user_profile_not_found(
        self,
        async_client: AsyncClient,
    ):
        """测试更新不存在的用户档案"""
        update_data = {
            "nickname": "新昵称",
        }
        
        response = await async_client.put(
            "/api/v1/users/999999/profile",
            json=update_data,
        )
        
        assert response.status_code == 404

    async def test_add_interest_tags_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_user_profile: UserProfile,
    ):
        """测试添加兴趣标签成功"""
        tags_data = {
            "tags": ["编程", "音乐", "运动"],
        }
        
        response = await async_client.post(
            f"/api/v1/users/{test_user.id}/profile/tags",
            json=tags_data,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["code"] == 200
        assert "编程" in data["data"]["tags"]
        assert "音乐" in data["data"]["tags"]
        assert "运动" in data["data"]["tags"]

    async def test_add_interest_tags_duplicate(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_user_profile: UserProfile,
    ):
        """测试添加重复标签（应该去重）"""
        # 先添加一些标签
        tags_data = {
            "tags": ["编程", "音乐"],
        }
        
        response1 = await async_client.post(
            f"/api/v1/users/{test_user.id}/profile/tags",
            json=tags_data,
        )
        
        assert response1.status_code == 200
        
        # 再次添加相同标签
        tags_data2 = {
            "tags": ["编程", "运动"],
        }
        
        response2 = await async_client.post(
            f"/api/v1/users/{test_user.id}/profile/tags",
            json=tags_data2,
        )
        
        assert response2.status_code == 200
        data = response2.json()
        
        # 验证去重
        tags = data["data"]["tags"]
        assert tags.count("编程") == 1
        assert "音乐" in tags
        assert "运动" in tags

    async def test_add_interest_tags_empty(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        """测试添加空标签列表"""
        tags_data = {
            "tags": [],
        }
        
        response = await async_client.post(
            f"/api/v1/users/{test_user.id}/profile/tags",
            json=tags_data,
        )
        
        assert response.status_code == 422  # Validation error

    async def test_add_interest_tags_user_not_found(
        self,
        async_client: AsyncClient,
    ):
        """测试为不存在的用户添加标签"""
        tags_data = {
            "tags": ["编程"],
        }
        
        response = await async_client.post(
            "/api/v1/users/999999/profile/tags",
            json=tags_data,
        )
        
        assert response.status_code == 404

    async def test_remove_interest_tags_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_user_profile: UserProfile,
    ):
        """测试删除兴趣标签成功"""
        # 先添加一些标签
        tags_data = {
            "tags": ["编程", "音乐", "运动"],
        }
        
        response1 = await async_client.post(
            f"/api/v1/users/{test_user.id}/profile/tags",
            json=tags_data,
        )
        
        assert response1.status_code == 200
        
        # 删除部分标签
        remove_data = {
            "tags": ["音乐"],
        }
        
        response2 = await async_client.delete(
            f"/api/v1/users/{test_user.id}/profile/tags",
            json=remove_data,
        )
        
        assert response2.status_code == 200
        data = response2.json()
        
        assert data["code"] == 200
        assert "编程" in data["data"]["tags"]
        assert "音乐" not in data["data"]["tags"]
        assert "运动" in data["data"]["tags"]

    async def test_remove_interest_tags_nonexistent(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_user_profile: UserProfile,
    ):
        """测试删除不存在的标签（不应报错）"""
        # 先添加一些标签
        tags_data = {
            "tags": ["编程"],
        }
        
        response1 = await async_client.post(
            f"/api/v1/users/{test_user.id}/profile/tags",
            json=tags_data,
        )
        
        assert response1.status_code == 200
        
        # 删除不存在的标签
        remove_data = {
            "tags": ["不存在的标签"],
        }
        
        response2 = await async_client.delete(
            f"/api/v1/users/{test_user.id}/profile/tags",
            json=remove_data,
        )
        
        assert response2.status_code == 200
        data = response2.json()
        
        # 原有标签应该保留
        assert "编程" in data["data"]["tags"]

    async def test_remove_interest_tags_user_not_found(
        self,
        async_client: AsyncClient,
    ):
        """测试为不存在的用户删除标签"""
        remove_data = {
            "tags": ["编程"],
        }
        
        response = await async_client.delete(
            "/api/v1/users/999999/profile/tags",
            json=remove_data,
        )
        
        assert response.status_code == 404

    async def test_remove_interest_tags_no_profile(
        self,
        async_client: AsyncClient,
        mysql_session: AsyncSession,
    ):
        """测试删除没有档案的用户的标签"""
        # 创建一个没有档案的用户
        user = User(
            wechat_openid="test_no_profile",
            school_id=1,
            verified=True,
        )
        mysql_session.add(user)
        await mysql_session.commit()
        await mysql_session.refresh(user)
        
        remove_data = {
            "tags": ["编程"],
        }
        
        response = await async_client.delete(
            f"/api/v1/users/{user.id}/profile/tags",
            json=remove_data,
        )
        
        assert response.status_code == 404

    async def test_profile_data_sync_across_modules(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_user_profile: UserProfile,
    ):
        """测试档案数据跨模块同步
        
        验证需求2.5：档案修改后，数据在所有相关模块中保持一致
        """
        # 更新档案
        update_data = {
            "nickname": "同步测试昵称",
            "grade": "2024级",
            "major": "计算机科学",
        }
        
        response1 = await async_client.put(
            f"/api/v1/users/{test_user.id}/profile",
            json=update_data,
        )
        
        assert response1.status_code == 200
        
        # 再次查询档案，验证数据一致性
        response2 = await async_client.get(f"/api/v1/users/{test_user.id}")
        
        assert response2.status_code == 200
        data = response2.json()
        
        assert data["data"]["nickname"] == "同步测试昵称"
        assert data["data"]["grade"] == "2024级"
        assert data["data"]["major"] == "计算机科学"
        
        # TODO: 当实现帖子、订单等模块后，验证这些模块中的用户信息也已更新
        # 例如：查询用户发布的帖子，验证作者昵称已更新

    async def test_tag_management_workflow(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_user_profile: UserProfile,
    ):
        """测试完整的标签管理工作流"""
        # 1. 添加初始标签
        response1 = await async_client.post(
            f"/api/v1/users/{test_user.id}/profile/tags",
            json={"tags": ["编程", "音乐"]},
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["data"]["tags"]) == 2
        
        # 2. 添加更多标签
        response2 = await async_client.post(
            f"/api/v1/users/{test_user.id}/profile/tags",
            json={"tags": ["运动", "阅读"]},
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["data"]["tags"]) == 4
        
        # 3. 删除部分标签
        response3 = await async_client.delete(
            f"/api/v1/users/{test_user.id}/profile/tags",
            json={"tags": ["音乐", "阅读"]},
        )
        assert response3.status_code == 200
        data3 = response3.json()
        assert len(data3["data"]["tags"]) == 2
        assert "编程" in data3["data"]["tags"]
        assert "运动" in data3["data"]["tags"]
        
        # 4. 查询档案验证最终状态
        response4 = await async_client.get(f"/api/v1/users/{test_user.id}")
        assert response4.status_code == 200
        data4 = response4.json()
        assert len(data4["data"]["tags"]) == 2
        assert "编程" in data4["data"]["tags"]
        assert "运动" in data4["data"]["tags"]
