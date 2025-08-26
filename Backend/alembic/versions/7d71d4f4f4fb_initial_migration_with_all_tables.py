"""Initial migration with all tables

Revision ID: 7d71d4f4f4fb
Revises: 
Create Date: 2025-08-24 08:51:01.649433

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7d71d4f4f4fb'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply database schema changes (forward migration)."""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('user_id', sa.BigInteger(), autoincrement=True, nullable=False, comment='使用者唯一 ID'),
        sa.Column('email', sa.String(length=255), nullable=False, comment='登入帳號'),
        sa.Column('password_hash', sa.String(length=255), nullable=False, comment='加鹽後 hash 密碼'),
        sa.Column('role', sa.Enum('USER', 'ADMIN', name='userrole'), nullable=False, comment='使用者角色'),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'SUSPENDED', 'DELETED', name='userstatus'), nullable=False, comment='帳號狀態'),
        sa.Column('display_name', sa.String(length=100), nullable=True, comment='顯示名稱'),
        sa.Column('profile_image', sa.String(length=500), nullable=True, comment='頭像路徑'),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True, comment='最後登入時間'),
        sa.Column('email_verified', sa.Boolean(), nullable=False, comment='是否已驗證電子郵件'),
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True, comment='電子郵件驗證時間'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('email')
    )
    
    # Create index on email for faster lookups
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_status', 'users', ['status'])
    
    # Create wallets table
    op.create_table(
        'wallets',
        sa.Column('wallet_id', sa.BigInteger(), autoincrement=True, nullable=False, comment='錢包唯一 ID'),
        sa.Column('user_id', sa.BigInteger(), nullable=False, comment='所屬使用者'),
        sa.Column('balance', sa.Integer(), default=0, nullable=False, comment='當前點數餘額'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='最後更新時間'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('wallet_id')
    )
    
    # Create indexes for wallets
    op.create_index('idx_wallets_user_id', 'wallets', ['user_id'])
    op.create_index('idx_wallets_updated_at', 'wallets', ['updated_at'])
    
    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('txn_id', sa.BigInteger(), autoincrement=True, nullable=False, comment='交易唯一 ID'),
        sa.Column('wallet_id', sa.BigInteger(), nullable=False, comment='所屬錢包'),
        sa.Column('type', sa.Enum('deposit', 'spend', 'refund', name='transactiontype'), nullable=False, comment='交易類型'),
        sa.Column('amount', sa.Integer(), nullable=False, comment='金額（正數 = 加點，負數 = 扣點）'),
        sa.Column('reference_id', sa.String(length=255), nullable=True, comment='金流平台或任務 ID'),
        sa.Column('status', sa.Enum('pending', 'success', 'failed', name='transactionstatus'), nullable=False, comment='狀態'),
        sa.Column('description', sa.String(length=500), nullable=True, comment='交易描述'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.ForeignKeyConstraint(['wallet_id'], ['wallets.wallet_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('txn_id')
    )
    
    # Create indexes for transactions
    op.create_index('idx_transactions_wallet_id', 'transactions', ['wallet_id'])
    op.create_index('idx_transactions_type', 'transactions', ['type'])
    op.create_index('idx_transactions_status', 'transactions', ['status'])
    op.create_index('idx_transactions_reference_id', 'transactions', ['reference_id'])
    op.create_index('idx_transactions_created_at', 'transactions', ['created_at'])
    op.create_index('idx_transactions_wallet_status', 'transactions', ['wallet_id', 'status'])
    
    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('job_id', sa.BigInteger(), autoincrement=True, nullable=False, comment='任務唯一 ID'),
        sa.Column('user_id', sa.BigInteger(), nullable=False, comment='建立任務的使用者'),
        sa.Column('txn_id', sa.BigInteger(), nullable=False, comment='扣點交易'),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', name='jobstatus'), nullable=False, comment='任務狀態'),
        sa.Column('input_path', sa.String(length=500), nullable=True, comment='任務輸入資料（檔案路徑 / URL）'),
        sa.Column('points_used', sa.Integer(), nullable=False, comment='扣除點數數量'),
        sa.Column('job_type', sa.String(length=100), nullable=True, comment='任務類型（fortune, tarot, etc.）'),
        sa.Column('priority', sa.Integer(), default=0, nullable=False, comment='任務優先級（數字越大優先級越高）'),
        sa.Column('expire_at', sa.DateTime(timezone=True), nullable=True, comment='任務結果保存期限'),
        sa.Column('error_message', sa.String(length=1000), nullable=True, comment='錯誤訊息'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True, comment='任務開始處理時間'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='任務完成時間'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['txn_id'], ['transactions.txn_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('job_id')
    )
    
    # Create indexes for jobs
    op.create_index('idx_jobs_user_id', 'jobs', ['user_id'])
    op.create_index('idx_jobs_status', 'jobs', ['status'])
    op.create_index('idx_jobs_txn_id', 'jobs', ['txn_id'])
    op.create_index('idx_jobs_created_at', 'jobs', ['created_at'])
    op.create_index('idx_jobs_expire_at', 'jobs', ['expire_at'])
    op.create_index('idx_jobs_user_status', 'jobs', ['user_id', 'status'])
    op.create_index('idx_jobs_priority_created', 'jobs', ['priority', 'created_at'])
    
    # Create job_results table
    op.create_table(
        'job_results',
        sa.Column('result_id', sa.BigInteger(), autoincrement=True, nullable=False, comment='結果唯一 ID'),
        sa.Column('job_id', sa.BigInteger(), nullable=False, comment='工作 ID'),
        sa.Column('user_id', sa.BigInteger(), nullable=False, comment='用戶 ID'),
        sa.Column('result_type', sa.String(length=50), nullable=False, comment='結果類型'),
        sa.Column('result_data', sa.JSON(), nullable=True, comment='結果資料'),
        sa.Column('file_path', sa.String(length=500), nullable=True, comment='結果檔案路徑'),
        sa.Column('file_size', sa.Integer(), nullable=True, comment='檔案大小'),
        sa.Column('mime_type', sa.String(length=100), nullable=True, comment='檔案類型'),
        sa.Column('download_count', sa.Integer(), nullable=False, comment='下載次數'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True, comment='過期時間'),
        sa.Column('is_public', sa.Boolean(), nullable=False, comment='是否公開'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.job_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('result_id')
    )
    
    # Create indexes for job_results
    op.create_index('ix_job_results_job_id', 'job_results', ['job_id'])
    op.create_index('ix_job_results_user_id', 'job_results', ['user_id'])
    op.create_index('ix_job_results_result_type', 'job_results', ['result_type'])
    op.create_index('ix_job_results_expires_at', 'job_results', ['expires_at'])
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('log_id', sa.BigInteger(), autoincrement=True, nullable=False, comment='Log 唯一 ID'),
        sa.Column('user_id', sa.BigInteger(), nullable=True, comment='用戶 ID'),
        sa.Column('action', sa.String(length=100), nullable=False, comment='操作類型'),
        sa.Column('resource_type', sa.String(length=50), nullable=True, comment='資源類型'),
        sa.Column('resource_id', sa.String(length=100), nullable=True, comment='資源 ID'),
        sa.Column('old_values', sa.JSON(), nullable=True, comment='舊值'),
        sa.Column('new_values', sa.JSON(), nullable=True, comment='新值'),
        sa.Column('ip_address', sa.String(length=45), nullable=True, comment='IP 地址'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='用戶代理'),
        sa.Column('session_id', sa.String(length=100), nullable=True, comment='會話 ID'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='操作狀態'),
        sa.Column('detail', sa.Text(), nullable=True, comment='詳細描述'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='錯誤訊息（如果操作失敗）'),
        sa.Column('extra_data', sa.JSON(), nullable=True, comment='結構化的額外信息'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('log_id')
    )
    
    # Create indexes for audit_logs
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('ix_audit_logs_status', 'audit_logs', ['status'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])


def downgrade() -> None:
    """Revert database schema changes (backward migration)."""
    
    # Drop tables in reverse order due to foreign key constraints
    op.drop_table('audit_logs')
    op.drop_table('job_results')
    op.drop_table('jobs')
    op.drop_table('transactions')
    op.drop_table('wallets')
    op.drop_table('users')
    
    # Drop custom enum types
    op.execute('DROP TYPE IF EXISTS userstatus')
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS transactiontype')
    op.execute('DROP TYPE IF EXISTS transactionstatus')  
    op.execute('DROP TYPE IF EXISTS jobstatus')