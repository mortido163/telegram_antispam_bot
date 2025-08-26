"""Initial migration: create base tables

Revision ID: 001_initial
Revises: 
Create Date: 2025-08-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import JSON


# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создание таблицы пользователей
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('warnings_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('is_banned', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('can_send_messages', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('last_warning_time', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Создание таблицы сообщений
    op.create_table('messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('contains_violations', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('violation_words', JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Создание таблицы конфигураций чатов
    op.create_table('chat_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('warnings_limit', sa.Integer(), server_default='3', nullable=True),
        sa.Column('forbidden_words', JSON(), server_default='[]', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chat_id')
    )


def downgrade() -> None:
    # Удаление таблиц в обратном порядке
    op.drop_table('chat_configs')
    op.drop_table('messages')
    op.drop_table('users')
