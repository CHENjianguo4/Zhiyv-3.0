"""create circles and schools tables

Revision ID: 004
Revises: 003
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create schools and circles tables"""
    # Create schools table
    op.create_table(
        'schools',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('short_name', sa.String(length=50), nullable=True),
        sa.Column('province', sa.String(length=50), nullable=True),
        sa.Column('city', sa.String(length=50), nullable=True),
        sa.Column('logo', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='active'),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=True
        ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create circles table
    op.create_table(
        'circles',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('school_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(length=255), nullable=True),
        sa.Column(
            'type',
            sa.Enum('official', 'custom', name='circletype'),
            nullable=False
        ),
        sa.Column('creator_id', sa.BigInteger(), nullable=True),
        sa.Column('admin_ids', sa.JSON(), nullable=True),
        sa.Column('member_count', sa.Integer(), server_default='0'),
        sa.Column('post_count', sa.Integer(), server_default='0'),
        sa.Column(
            'status',
            sa.Enum('active', 'archived', name='circlestatus'),
            nullable=False
        ),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=True
        ),
        sa.Column(
            'updated_at',
            sa.TIMESTAMP(),
            server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
            nullable=True
        ),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id']),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_school_id', 'circles', ['school_id'])
    op.create_index('idx_type', 'circles', ['type'])
    op.create_index('idx_status', 'circles', ['status'])


def downgrade() -> None:
    """Drop circles and schools tables"""
    op.drop_index('idx_status', table_name='circles')
    op.drop_index('idx_type', table_name='circles')
    op.drop_index('idx_school_id', table_name='circles')
    op.drop_table('circles')
    op.drop_table('schools')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS circletype')
    op.execute('DROP TYPE IF EXISTS circlestatus')
