"""create sensitive_words table

Revision ID: 002
Revises: 001
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create sensitive_words table"""
    op.create_table(
        'sensitive_words',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('word', sa.String(length=100), nullable=False),
        sa.Column(
            'level',
            sa.Enum('low', 'medium', 'high', name='sensitivewordlevel'),
            nullable=False
        ),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column(
            'action',
            sa.Enum('replace', 'block', 'review', name='sensitivewordaction'),
            nullable=False
        ),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=True
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('word', name='uk_word')
    )
    
    # Create indexes
    op.create_index('idx_level', 'sensitive_words', ['level'])


def downgrade() -> None:
    """Drop sensitive_words table"""
    op.drop_index('idx_level', table_name='sensitive_words')
    op.drop_table('sensitive_words')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS sensitivewordlevel')
    op.execute('DROP TYPE IF EXISTS sensitivewordaction')
