"""create favorites and alerts tables

Revision ID: 003
Revises: 002
Create Date: 2024-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create favorites and price alerts tables"""
    
    # Create item_favorites table
    op.create_table(
        'item_favorites',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='收藏ID'),
        sa.Column('user_id', sa.BigInteger(), nullable=False, comment='用户ID'),
        sa.Column('item_id', sa.BigInteger(), nullable=False, comment='商品ID'),
        sa.Column('school_id', sa.BigInteger(), nullable=False, comment='学校ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_user_id', 'user_id'),
        sa.Index('idx_item_id', 'item_id'),
        sa.Index('idx_school_id', 'school_id'),
        sa.UniqueConstraint('user_id', 'item_id', name='uk_user_item'),
        comment='商品收藏表'
    )
    
    # Create price_alerts table
    op.create_table(
        'price_alerts',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False, comment='提醒ID'),
        sa.Column('user_id', sa.BigInteger(), nullable=False, comment='用户ID'),
        sa.Column('item_id', sa.BigInteger(), nullable=False, comment='商品ID'),
        sa.Column('school_id', sa.BigInteger(), nullable=False, comment='学校ID'),
        sa.Column('target_price', sa.Numeric(10, 2), nullable=False, comment='目标价格'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1', comment='是否激活'),
        sa.Column('notified_at', sa.DateTime(), nullable=True, comment='通知时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_user_id', 'user_id'),
        sa.Index('idx_item_id', 'item_id'),
        sa.Index('idx_school_id', 'school_id'),
        sa.Index('idx_is_active', 'is_active'),
        sa.UniqueConstraint('user_id', 'item_id', name='uk_user_item_alert'),
        comment='降价提醒表'
    )


def downgrade() -> None:
    """Drop favorites and price alerts tables"""
    op.drop_table('price_alerts')
    op.drop_table('item_favorites')
