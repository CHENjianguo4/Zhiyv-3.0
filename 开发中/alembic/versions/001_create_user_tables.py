"""create user tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建用户相关表"""
    # 创建users表
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="用户ID"),
        sa.Column("wechat_openid", sa.String(length=64), nullable=False, comment="微信OpenID"),
        sa.Column("wechat_unionid", sa.String(length=64), nullable=True, comment="微信UnionID"),
        sa.Column("nickname", sa.String(length=50), nullable=True, comment="昵称"),
        sa.Column("avatar", sa.String(length=255), nullable=True, comment="头像URL"),
        sa.Column("school_id", sa.BigInteger(), nullable=False, comment="学校ID"),
        sa.Column("student_id", sa.String(length=50), nullable=True, comment="学号"),
        sa.Column("real_name", sa.String(length=50), nullable=True, comment="真实姓名"),
        sa.Column("email", sa.String(length=100), nullable=True, comment="邮箱"),
        sa.Column("phone", sa.String(length=20), nullable=True, comment="手机号"),
        sa.Column(
            "role",
            sa.Enum("student", "teacher", "merchant", "admin", name="userrole"),
            nullable=False,
            comment="用户角色",
        ),
        sa.Column("verified", sa.Boolean(), nullable=False, comment="是否已认证"),
        sa.Column("credit_score", sa.Integer(), nullable=False, comment="信用分（默认80）"),
        sa.Column("points", sa.Integer(), nullable=False, comment="积分（默认0）"),
        sa.Column(
            "status",
            sa.Enum("active", "banned", "deleted", name="userstatus"),
            nullable=False,
            comment="账号状态",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("wechat_openid"),
    )
    op.create_index("idx_school_id", "users", ["school_id"], unique=False)
    op.create_index("idx_student_id", "users", ["student_id"], unique=False)
    op.create_index("idx_credit_score", "users", ["credit_score"], unique=False)
    op.create_index(op.f("ix_users_wechat_openid"), "users", ["wechat_openid"], unique=True)
    op.create_index(op.f("ix_users_wechat_unionid"), "users", ["wechat_unionid"], unique=False)

    # 创建user_profiles表
    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="用户ID"),
        sa.Column("grade", sa.String(length=20), nullable=True, comment="年级"),
        sa.Column("major", sa.String(length=100), nullable=True, comment="专业"),
        sa.Column("campus", sa.String(length=50), nullable=True, comment="校区"),
        sa.Column("tags", sa.JSON(), nullable=True, comment="兴趣标签（JSON数组）"),
        sa.Column("bio", sa.Text(), nullable=True, comment="个人简介"),
        sa.Column("privacy_settings", sa.JSON(), nullable=True, comment="隐私设置（JSON对象）"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )

    # 创建credit_logs表
    op.create_table(
        "credit_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="记录ID"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="用户ID"),
        sa.Column("change_amount", sa.Integer(), nullable=False, comment="变更金额（正数为增加，负数为减少）"),
        sa.Column("reason", sa.String(length=255), nullable=True, comment="变更原因"),
        sa.Column("related_type", sa.String(length=50), nullable=True, comment="关联对象类型（post/order/rating/violation）"),
        sa.Column("related_id", sa.BigInteger(), nullable=True, comment="关联对象ID"),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_user_id", "credit_logs", ["user_id"], unique=False)
    op.create_index("idx_created_at", "credit_logs", ["created_at"], unique=False)

    # 创建point_logs表
    op.create_table(
        "point_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="记录ID"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="用户ID"),
        sa.Column("change_amount", sa.Integer(), nullable=False, comment="变更金额（正数为增加，负数为减少）"),
        sa.Column("action_type", sa.String(length=50), nullable=True, comment="动作类型（post/order/rating/material等）"),
        sa.Column("description", sa.String(length=255), nullable=True, comment="描述"),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_point_logs_user_id"), "point_logs", ["user_id"], unique=False)


def downgrade() -> None:
    """删除用户相关表"""
    op.drop_index(op.f("ix_point_logs_user_id"), table_name="point_logs")
    op.drop_table("point_logs")
    op.drop_index("idx_created_at", table_name="credit_logs")
    op.drop_index("idx_user_id", table_name="credit_logs")
    op.drop_table("credit_logs")
    op.drop_table("user_profiles")
    op.drop_index(op.f("ix_users_wechat_unionid"), table_name="users")
    op.drop_index(op.f("ix_users_wechat_openid"), table_name="users")
    op.drop_index("idx_credit_score", table_name="users")
    op.drop_index("idx_student_id", table_name="users")
    op.drop_index("idx_school_id", table_name="users")
    op.drop_table("users")
