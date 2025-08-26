"""Add fortune_jobs table

Revision ID: add_fortune_jobs_table
Revises: 7d71d4f4f4fb
Create Date: 2024-01-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_fortune_jobs_table'
down_revision = '7d71d4f4f4fb'
branch_labels = None
depends_on = None


def upgrade():
    # Create job status enum
    job_status_enum = postgresql.ENUM(
        'pending', 'processing', 'running', 'completed', 'failed',
        name='jobstatus',
        create_type=False
    )
    job_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create job type enum
    job_type_enum = postgresql.ENUM(
        'fortune_draw', 'fortune_interpret', 'general',
        name='jobtype',
        create_type=False
    )
    job_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create fortune_jobs table
    op.create_table('fortune_jobs',
        sa.Column('id', sa.String(length=36), nullable=False, comment='UUID job identifier'),
        sa.Column('user_id', sa.String(length=36), nullable=False, comment='User who created the job'),
        sa.Column('job_type', job_type_enum, nullable=False, comment='Type of fortune job'),
        sa.Column('status', job_status_enum, nullable=False, comment='Current job status'),
        sa.Column('payload', sa.JSON(), nullable=True, comment='Job input data'),
        sa.Column('result_data', sa.JSON(), nullable=True, comment='Job result data'),
        sa.Column('error_message', sa.String(length=1000), nullable=True, comment='Error message if failed'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True, comment='When processing started'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='When job completed'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True, comment='When job expires'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='Simplified job model for fortune processing tasks'
    )
    
    # Create indexes
    op.create_index('idx_fortune_jobs_user_id', 'fortune_jobs', ['user_id'])
    op.create_index('idx_fortune_jobs_status', 'fortune_jobs', ['status'])
    op.create_index('idx_fortune_jobs_type', 'fortune_jobs', ['job_type'])
    op.create_index('idx_fortune_jobs_created_at', 'fortune_jobs', ['created_at'])
    op.create_index('idx_fortune_jobs_user_status', 'fortune_jobs', ['user_id', 'status'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_fortune_jobs_user_status', table_name='fortune_jobs')
    op.drop_index('idx_fortune_jobs_created_at', table_name='fortune_jobs')
    op.drop_index('idx_fortune_jobs_type', table_name='fortune_jobs')
    op.drop_index('idx_fortune_jobs_status', table_name='fortune_jobs')
    op.drop_index('idx_fortune_jobs_user_id', table_name='fortune_jobs')
    
    # Drop table
    op.drop_table('fortune_jobs')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS jobtype')
    op.execute('DROP TYPE IF EXISTS jobstatus')