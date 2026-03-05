"""create reports table

Revision ID: 003
Revises: 002
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create reports table"""
    op.create_table(
        'reports',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('reporter_id', sa.BigInteger(), nullable=False),
        sa.Column(
            'target_type',
            sa.Enum('post', 'comment', 'user', 'item', 'order', name='reporttargettype'),
            nullable=False
        ),
        sa.Column('target_id', sa.BigInteger(), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('evidence', sa.JSON(), nullable=True),
        sa.Column(
            'status',
            sa.Enum('pending', 'processing', 'resolved', 'rejected', name='reportstatus'),
            nullable=False
        ),
        sa.Column('handler_id', sa.BigInteger(), nullable=True),
        sa.Column('handle_result', sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(['reporter_id'], ['users.id']),
        sa.ForeignKeyConstraint(['handler_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_status', 'reports', ['status'])
    op.create_index('idx_target', 'reports', ['target_type', 'target_id'])
    op.create_index('idx_reporter_id', 'reports', ['reporter_id'])
    op.create_index('idx_created_at', 'reports', ['created_at'])


def downgrade() -> None:
    """Drop reports table"""
    op.drop_index('idx_created_at', table_name='reports')
    op.drop_index('idx_reporter_id', table_name='reports')
    op.drop_index('idx_target', table_name='reports')
    op.drop_index('idx_status', table_name='reports')
    op.drop_table('reports')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS reporttargettype')
    op.execute('DROP TYPE IF EXISTS reportstatus')
