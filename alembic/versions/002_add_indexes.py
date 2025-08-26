"""Add database indexes for performance

Revision ID: 002_add_indexes
Revises: 001_initial
Create Date: 2025-08-26 12:01:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_indexes'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создание индексов для оптимизации запросов
    
    # Индекс для поиска пользователей по user_id и chat_id
    op.create_index('idx_users_user_chat', 'users', ['user_id', 'chat_id'], unique=False)
    
    # Индекс для поиска забаненных пользователей
    op.create_index('idx_users_banned', 'users', ['is_banned'], unique=False)
    
    # Индекс для поиска сообщений по чату
    op.create_index('idx_messages_chat', 'messages', ['chat_id'], unique=False)
    
    # Индекс для поиска сообщений с нарушениями
    op.create_index('idx_messages_violations', 'messages', ['chat_id', 'contains_violations'], unique=False)
    
    # Индекс для поиска сообщений по времени
    op.create_index('idx_messages_timestamp', 'messages', ['timestamp'], unique=False)
    
    # Индекс для поиска сообщений пользователя
    op.create_index('idx_messages_user_chat', 'messages', ['user_id', 'chat_id'], unique=False)


def downgrade() -> None:
    # Удаление индексов
    op.drop_index('idx_messages_user_chat', table_name='messages')
    op.drop_index('idx_messages_timestamp', table_name='messages')
    op.drop_index('idx_messages_violations', table_name='messages')
    op.drop_index('idx_messages_chat', table_name='messages')
    op.drop_index('idx_users_banned', table_name='users')
    op.drop_index('idx_users_user_chat', table_name='users')
