"""add password column to employees

Revision ID: add_employee_password_column
Revises: add_work_time_tables
Create Date: 2025-07-09 18:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_employee_password_column'
down_revision = 'add_work_time_tables'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('employees', sa.Column('password', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('employees', 'password') 