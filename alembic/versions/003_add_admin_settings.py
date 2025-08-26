"""Add admin settings table

Revision ID: 003_add_admin_settings
Revises: 002_add_indexes
Create Date: 2024-01-20 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_add_admin_settings'
down_revision: Union[str, None] = '002_add_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Создать таблицу настроек администраторов"""
    op.create_table(
        'admin_settings',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('chat_id', sa.BigInteger, nullable=False),
        sa.Column('user_id', sa.BigInteger, nullable=False),
        sa.Column('role', sa.String(50), nullable=False),  # 'admin', 'moderator'
        sa.Column('permissions', sa.JSON, nullable=True),  # JSON со списком разрешений
        sa.Column('granted_by', sa.BigInteger, nullable=False),  # Кто назначил
        sa.Column('granted_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime, nullable=True),  # Временные права
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Индексы для быстрого поиска
    op.create_index(
        'idx_admin_settings_chat_user', 
        'admin_settings', 
        ['chat_id', 'user_id'], 
        unique=True
    )
    op.create_index(
        'idx_admin_settings_user_active', 
        'admin_settings', 
        ['user_id', 'is_active']
    )
    op.create_index(
        'idx_admin_settings_role', 
        'admin_settings', 
        ['role']
    )
    op.create_index(
        'idx_admin_settings_expires', 
        'admin_settings', 
        ['expires_at']
    )
    
    # Таблица для глобальных настроек бота
    op.create_table(
        'bot_settings',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('key', sa.String(100), nullable=False, unique=True),
        sa.Column('value', sa.Text, nullable=True),
        sa.Column('value_type', sa.String(20), nullable=False, default='string'),  # string, int, bool, json
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_sensitive', sa.Boolean, nullable=False, default=False),  # Скрывать в логах
        sa.Column('updated_by', sa.BigInteger, nullable=True),  # Кто обновил
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Индекс для быстрого поиска настроек
    op.create_index(
        'idx_bot_settings_key', 
        'bot_settings', 
        ['key']
    )


def downgrade() -> None:
    """Удалить таблицы настроек администраторов"""
    op.drop_index('idx_bot_settings_key', table_name='bot_settings')
    op.drop_table('bot_settings')
    
    op.drop_index('idx_admin_settings_expires', table_name='admin_settings')
    op.drop_index('idx_admin_settings_role', table_name='admin_settings')
    op.drop_index('idx_admin_settings_user_active', table_name='admin_settings')
    op.drop_index('idx_admin_settings_chat_user', table_name='admin_settings')
    op.drop_table('admin_settings')
