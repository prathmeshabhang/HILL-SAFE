"""v3_6_station_status

Revision ID: 374d59487ca7
Revises: c4b1829e5a10
Create Date: 2026-09-21 19:40:23.587506

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '374d59487ca7'
down_revision: Union[str, Sequence[str], None] = 'c4b1829e5a10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to include station lifecycle status."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c['name'] for c in inspector.get_columns('sensor_stations')]
    if 'status' not in cols:
        op.add_column(
            'sensor_stations',
            sa.Column('status', sa.String(32), nullable=False, server_default='PLANNED')
        )


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c['name'] for c in inspector.get_columns('sensor_stations')]
    if 'status' in cols:
        op.drop_column('sensor_stations', 'status')
