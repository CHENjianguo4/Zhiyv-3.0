"""create secondhand tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建二手商品相关表"""
    # 创建secondhand_items表
    op.create_table(
        "secondhand_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="商品ID"),
        sa.Column("seller_id", sa.BigInteger(), nullable=False, comment="卖家ID"),
        sa.Column("school_id", sa.BigInteger(), nullable=False, comment="学校ID"),
        sa.Column("title", sa.String(length=200), nullable=False, comment="商品标题"),
        sa.Column("description", sa.Text(), nullable=True, comment="商品描述"),
        sa.Column(
            "category",
            sa.Enum(
                "electronics",
                "textbook",
                "daily",
                "sports",
                "other",
                name="itemcategory",
            ),
            nullable=False,
            comment="商品分类",
        ),
        sa.Column(
            "condition",
            sa.Enum(
                "brand_new",
                "like_new",
                "lightly_used",
                "well_used",
                "heavily_used",
                name="itemcondition",
            ),
            nullable=False,
            comment="成色",
        ),
        sa.Column("original_price", sa.Numeric(precision=10, scale=2), nullable=True, comment="原价"),
        sa.Column("selling_price", sa.Numeric(precision=10, scale=2), nullable=False, comment="售价"),
        sa.Column("images", sa.JSON(), nullable=True, comment="图片URLs（JSON数组）"),
        sa.Column("videos", sa.JSON(), nullable=True, comment="视频URLs（JSON数组）"),
        sa.Column("location", sa.String(length=255), nullable=True, comment="交易地点"),
        sa.Column("is_negotiable", sa.Boolean(), nullable=False, comment="是否可议价"),
        sa.Column(
            "delivery_method",
            sa.Enum(
                "face_to_face",
                "express",
                "both",
                name="deliverymethod",
            ),
            nullable=False,
            comment="交易方式",
        ),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "on_sale",
                "sold",
                "removed",
                "banned",
                name="itemstatus",
            ),
            nullable=False,
            comment="状态",
        ),
        sa.Column("view_count", sa.BigInteger(), nullable=False, comment="浏览次数"),
        sa.Column("favorite_count", sa.BigInteger(), nullable=False, comment="收藏次数"),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, comment="更新时间"),
        sa.Column("deleted_at", sa.DateTime(), nullable=True, comment="删除时间（软删除）"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_school_id", "secondhand_items", ["school_id"], unique=False)
    op.create_index("idx_seller_id", "secondhand_items", ["seller_id"], unique=False)
    op.create_index("idx_category", "secondhand_items", ["category"], unique=False)
    op.create_index("idx_status", "secondhand_items", ["status"], unique=False)
    op.create_index(
        "idx_school_category_status",
        "secondhand_items",
        ["school_id", "category", "status"],
        unique=False,
    )

    # 创建secondhand_orders表
    op.create_table(
        "secondhand_orders",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="订单ID"),
        sa.Column("item_id", sa.BigInteger(), nullable=False, comment="商品ID"),
        sa.Column("buyer_id", sa.BigInteger(), nullable=False, comment="买家ID"),
        sa.Column("seller_id", sa.BigInteger(), nullable=False, comment="卖家ID"),
        sa.Column("school_id", sa.BigInteger(), nullable=False, comment="学校ID"),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False, comment="成交价格"),
        sa.Column(
            "delivery_method",
            sa.Enum(
                "face_to_face",
                "express",
                "both",
                name="deliverymethod",
            ),
            nullable=False,
            comment="交易方式",
        ),
        sa.Column("delivery_address", sa.String(length=500), nullable=True, comment="收货地址"),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "confirmed",
                "delivering",
                "completed",
                "cancelled",
                "disputed",
                name="orderstatus",
            ),
            nullable=False,
            comment="订单状态",
        ),
        sa.Column(
            "payment_status",
            sa.Enum(
                "unpaid",
                "paid",
                "refunded",
                name="paymentstatus",
            ),
            nullable=False,
            comment="支付状态",
        ),
        sa.Column("escrow_amount", sa.Numeric(precision=10, scale=2), nullable=True, comment="担保金额"),
        sa.Column("buyer_note", sa.Text(), nullable=True, comment="买家备注"),
        sa.Column("seller_note", sa.Text(), nullable=True, comment="卖家备注"),
        sa.Column("completed_at", sa.DateTime(), nullable=True, comment="完成时间"),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_item_id", "secondhand_orders", ["item_id"], unique=False)
    op.create_index("idx_buyer_id", "secondhand_orders", ["buyer_id"], unique=False)
    op.create_index("idx_seller_id", "secondhand_orders", ["seller_id"], unique=False)
    op.create_index("idx_school_id", "secondhand_orders", ["school_id"], unique=False)
    op.create_index("idx_status", "secondhand_orders", ["status"], unique=False)


def downgrade() -> None:
    """删除二手商品相关表"""
    op.drop_index("idx_status", table_name="secondhand_orders")
    op.drop_index("idx_school_id", table_name="secondhand_orders")
    op.drop_index("idx_seller_id", table_name="secondhand_orders")
    op.drop_index("idx_buyer_id", table_name="secondhand_orders")
    op.drop_index("idx_item_id", table_name="secondhand_orders")
    op.drop_table("secondhand_orders")
    op.drop_index("idx_school_category_status", table_name="secondhand_items")
    op.drop_index("idx_status", table_name="secondhand_items")
    op.drop_index("idx_category", table_name="secondhand_items")
    op.drop_index("idx_seller_id", table_name="secondhand_items")
    op.drop_index("idx_school_id", table_name="secondhand_items")
    op.drop_table("secondhand_items")
