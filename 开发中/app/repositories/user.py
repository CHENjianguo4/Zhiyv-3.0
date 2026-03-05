"""用户仓储层

提供用户相关的数据访问操作
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import CreditLog, PointLog, User, UserProfile


class UserRepository:
    """用户仓储类

    提供用户、用户档案、信用分记录、积分记录的CRUD操作
    """

    def __init__(self, session: AsyncSession):
        """初始化仓储

        Args:
            session: 数据库会话
        """
        self.session = session

    # ==================== User CRUD ====================

    async def create_user(self, user: User) -> User:
        """创建用户

        Args:
            user: 用户对象

        Returns:
            User: 创建后的用户对象（包含ID）
        """
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get_user_by_id(
        self,
        user_id: int,
        load_profile: bool = False,
    ) -> Optional[User]:
        """根据ID获取用户

        Args:
            user_id: 用户ID
            load_profile: 是否加载用户档案

        Returns:
            Optional[User]: 用户对象，不存在则返回None
        """
        query = select(User).where(User.id == user_id)

        if load_profile:
            query = query.options(selectinload(User.profile))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_openid(
        self,
        openid: str,
        load_profile: bool = False,
    ) -> Optional[User]:
        """根据微信OpenID获取用户

        Args:
            openid: 微信OpenID
            load_profile: 是否加载用户档案

        Returns:
            Optional[User]: 用户对象，不存在则返回None
        """
        query = select(User).where(User.wechat_openid == openid)

        if load_profile:
            query = query.options(selectinload(User.profile))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_student_id(
        self,
        school_id: int,
        student_id: str,
    ) -> Optional[User]:
        """根据学校ID和学号获取用户

        Args:
            school_id: 学校ID
            student_id: 学号

        Returns:
            Optional[User]: 用户对象，不存在则返回None
        """
        query = select(User).where(
            User.school_id == school_id,
            User.student_id == student_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_user(self, user: User) -> User:
        """更新用户

        Args:
            user: 用户对象

        Returns:
            User: 更新后的用户对象
        """
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def delete_user(self, user: User) -> None:
        """删除用户（软删除）

        Args:
            user: 用户对象
        """
        from app.models.user import UserStatus

        user.status = UserStatus.DELETED
        await self.session.flush()

    async def list_users_by_school(
        self,
        school_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> list[User]:
        """根据学校ID获取用户列表

        Args:
            school_id: 学校ID
            offset: 偏移量
            limit: 限制数量

        Returns:
            list[User]: 用户列表
        """
        query = (
            select(User)
            .where(User.school_id == school_id)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ==================== UserProfile CRUD ====================

    async def create_profile(self, profile: UserProfile) -> UserProfile:
        """创建用户档案

        Args:
            profile: 用户档案对象

        Returns:
            UserProfile: 创建后的用户档案对象
        """
        self.session.add(profile)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def get_profile_by_user_id(
        self,
        user_id: int,
    ) -> Optional[UserProfile]:
        """根据用户ID获取用户档案

        Args:
            user_id: 用户ID

        Returns:
            Optional[UserProfile]: 用户档案对象，不存在则返回None
        """
        query = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_profile(self, profile: UserProfile) -> UserProfile:
        """更新用户档案

        Args:
            profile: 用户档案对象

        Returns:
            UserProfile: 更新后的用户档案对象
        """
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def delete_profile(self, profile: UserProfile) -> None:
        """删除用户档案

        Args:
            profile: 用户档案对象
        """
        await self.session.delete(profile)
        await self.session.flush()

    # ==================== CreditLog CRUD ====================

    async def create_credit_log(self, log: CreditLog) -> CreditLog:
        """创建信用分记录

        Args:
            log: 信用分记录对象

        Returns:
            CreditLog: 创建后的信用分记录对象
        """
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def get_credit_logs_by_user_id(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> list[CreditLog]:
        """根据用户ID获取信用分记录列表

        Args:
            user_id: 用户ID
            offset: 偏移量
            limit: 限制数量

        Returns:
            list[CreditLog]: 信用分记录列表
        """
        query = (
            select(CreditLog)
            .where(CreditLog.user_id == user_id)
            .order_by(CreditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ==================== PointLog CRUD ====================

    async def create_point_log(self, log: PointLog) -> PointLog:
        """创建积分记录

        Args:
            log: 积分记录对象

        Returns:
            PointLog: 创建后的积分记录对象
        """
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def get_point_logs_by_user_id(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> list[PointLog]:
        """根据用户ID获取积分记录列表

        Args:
            user_id: 用户ID
            offset: 偏移量
            limit: 限制数量

        Returns:
            list[PointLog]: 积分记录列表
        """
        query = (
            select(PointLog)
            .where(PointLog.user_id == user_id)
            .order_by(PointLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ==================== 业务方法 ====================

    async def update_credit_score(
        self,
        user_id: int,
        change_amount: int,
        reason: str,
        related_type: Optional[str] = None,
        related_id: Optional[int] = None,
    ) -> tuple[User, CreditLog]:
        """更新用户信用分并记录日志

        Args:
            user_id: 用户ID
            change_amount: 变更金额（正数为增加，负数为减少）
            reason: 变更原因
            related_type: 关联对象类型
            related_id: 关联对象ID

        Returns:
            tuple[User, CreditLog]: 更新后的用户对象和信用分记录

        Raises:
            ValueError: 用户不存在
        """
        # 获取用户
        user = await self.get_user_by_id(user_id)
        if user is None:
            raise ValueError(f"用户不存在: {user_id}")

        # 更新信用分
        user.credit_score += change_amount

        # 确保信用分在0-100之间
        user.credit_score = max(0, min(100, user.credit_score))

        # 创建信用分记录
        log = CreditLog(
            user_id=user_id,
            change_amount=change_amount,
            reason=reason,
            related_type=related_type,
            related_id=related_id,
        )
        await self.create_credit_log(log)

        # 更新用户
        await self.update_user(user)

        return user, log

    async def update_points(
        self,
        user_id: int,
        change_amount: int,
        action_type: str,
        description: Optional[str] = None,
    ) -> tuple[User, PointLog]:
        """更新用户积分并记录日志

        Args:
            user_id: 用户ID
            change_amount: 变更金额（正数为增加，负数为减少）
            action_type: 动作类型
            description: 描述

        Returns:
            tuple[User, PointLog]: 更新后的用户对象和积分记录

        Raises:
            ValueError: 用户不存在或积分不足
        """
        # 获取用户
        user = await self.get_user_by_id(user_id)
        if user is None:
            raise ValueError(f"用户不存在: {user_id}")

        # 检查积分是否足够
        if user.points + change_amount < 0:
            raise ValueError(f"积分不足: 当前积分={user.points}, 需要={-change_amount}")

        # 更新积分
        user.points += change_amount

        # 创建积分记录
        log = PointLog(
            user_id=user_id,
            change_amount=change_amount,
            action_type=action_type,
            description=description,
        )
        await self.create_point_log(log)

        # 更新用户
        await self.update_user(user)

        return user, log
