"""Add work time tracking tables

Revision ID: add_work_time_tables
Revises: c79c0ad5ce06
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_work_time_tables'
down_revision = 'c79c0ad5ce06'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Проверяем, существуют ли таблицы
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()
    
    if 'work_days' not in existing_tables:
        op.create_table('work_days',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('total_work_time', sa.Integer(), nullable=True),
        sa.Column('total_break_time', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'PAUSED', 'FINISHED', name='workdaystatusenum'), nullable=True),
        sa.Column('applications_processed', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
    
    if 'work_breaks' not in existing_tables:
        op.create_table('work_breaks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('work_day_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['work_day_id'], ['work_days.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    # Явно создаем ENUM для problem_status
    problem_status_enum = sa.Enum('NEW', 'IN_PROGRESS', 'SOLVED', 'SOLVED_RETURN', name='problemstatusenum')
    problem_status_enum.create(op.get_bind(), checkfirst=True)
    with op.batch_alter_table('applications') as batch_op:
        batch_op.add_column(sa.Column('problem_status', problem_status_enum, nullable=True))
        batch_op.add_column(sa.Column('problem_comment', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('problem_responsible', sa.String(), nullable=True))


def downgrade() -> None:
    # Удаляем таблицы в обратном порядке
    op.drop_table('work_breaks')
    op.drop_table('work_days') 