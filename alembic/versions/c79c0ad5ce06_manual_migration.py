"""manual migration

Revision ID: c79c0ad5ce06
Revises: 
Create Date: 2025-07-09 16:05:02.150786

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c79c0ad5ce06'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Проверяем, существует ли колонка taken_at
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('applications')]
    
    if 'taken_at' not in columns:
        op.add_column('applications', sa.Column('taken_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Проверяем, существует ли колонка taken_at перед удалением
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('applications')]
    
    if 'taken_at' in columns:
        op.drop_column('applications', 'taken_at')
