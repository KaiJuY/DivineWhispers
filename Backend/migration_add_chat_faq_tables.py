"""Add chat and FAQ tables

Revision ID: add_chat_faq_tables
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_chat_faq_tables'
down_revision = None  # Update this to your latest revision ID
branch_labels = None
depends_on = None


def upgrade():
    """Create chat and FAQ tables"""
    
    # Create chat_sessions table
    op.create_table('chat_sessions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=False, index=True),
        sa.Column('session_name', sa.String(200), nullable=True),
        sa.Column('context_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('is_active', sa.Boolean(), default=True),
    )
    
    # Create chat_messages table
    op.create_table('chat_messages',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('chat_sessions.id'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=False, index=True),
        sa.Column('message_type', sa.String(20), nullable=False, default='user'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('is_deleted', sa.Boolean(), default=False),
    )
    
    # Create faqs table
    op.create_table('faqs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('category', sa.String(50), nullable=False, default='general'),
        sa.Column('question', sa.String(500), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('slug', sa.String(200), unique=True, nullable=False, index=True),
        sa.Column('tags', sa.String(500), nullable=True),
        sa.Column('is_published', sa.Boolean(), default=True),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('view_count', sa.Integer(), default=0),
        sa.Column('helpful_votes', sa.Integer(), default=0),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('updated_by', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create faq_feedback table
    op.create_table('faq_feedback',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('faq_id', sa.Integer(), sa.ForeignKey('faqs.id'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('is_helpful', sa.Boolean(), nullable=False),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Create indexes for better performance
    op.create_index('idx_chat_sessions_user_id', 'chat_sessions', ['user_id'])
    op.create_index('idx_chat_sessions_active', 'chat_sessions', ['is_active'])
    op.create_index('idx_chat_sessions_updated_at', 'chat_sessions', ['updated_at'])
    
    op.create_index('idx_chat_messages_session_id', 'chat_messages', ['session_id'])
    op.create_index('idx_chat_messages_user_id', 'chat_messages', ['user_id'])
    op.create_index('idx_chat_messages_created_at', 'chat_messages', ['created_at'])
    op.create_index('idx_chat_messages_type', 'chat_messages', ['message_type'])
    
    op.create_index('idx_faqs_category', 'faqs', ['category'])
    op.create_index('idx_faqs_published', 'faqs', ['is_published'])
    op.create_index('idx_faqs_display_order', 'faqs', ['display_order'])
    op.create_index('idx_faqs_created_by', 'faqs', ['created_by'])
    
    op.create_index('idx_faq_feedback_faq_id', 'faq_feedback', ['faq_id'])
    op.create_index('idx_faq_feedback_helpful', 'faq_feedback', ['is_helpful'])
    op.create_index('idx_faq_feedback_created_at', 'faq_feedback', ['created_at'])


def downgrade():
    """Drop chat and FAQ tables"""
    
    # Drop indexes first
    op.drop_index('idx_faq_feedback_created_at', 'faq_feedback')
    op.drop_index('idx_faq_feedback_helpful', 'faq_feedback')
    op.drop_index('idx_faq_feedback_faq_id', 'faq_feedback')
    
    op.drop_index('idx_faqs_created_by', 'faqs')
    op.drop_index('idx_faqs_display_order', 'faqs')
    op.drop_index('idx_faqs_published', 'faqs')
    op.drop_index('idx_faqs_category', 'faqs')
    
    op.drop_index('idx_chat_messages_type', 'chat_messages')
    op.drop_index('idx_chat_messages_created_at', 'chat_messages')
    op.drop_index('idx_chat_messages_user_id', 'chat_messages')
    op.drop_index('idx_chat_messages_session_id', 'chat_messages')
    
    op.drop_index('idx_chat_sessions_updated_at', 'chat_sessions')
    op.drop_index('idx_chat_sessions_active', 'chat_sessions')
    op.drop_index('idx_chat_sessions_user_id', 'chat_sessions')
    
    # Drop tables
    op.drop_table('faq_feedback')
    op.drop_table('faqs')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')