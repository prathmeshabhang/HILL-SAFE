"""v3_7_provenance_and_commissioning

Revision ID: 26e91b61bac6
Revises: 374d59487ca7
Create Date: 2026-09-21 20:17:00.605812

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26e91b61bac6'
down_revision: Union[str, Sequence[str], None] = '374d59487ca7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to include provenance, environment, qc_flags, and station commissioning data."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. Update sensor_stations
    st_cols = [c['name'] for c in inspector.get_columns('sensor_stations')]
    if 'commissioning_data' not in st_cols:
        op.add_column('sensor_stations', sa.Column('commissioning_data', sa.Text(), nullable=True))
    if 'commissioned_at' not in st_cols:
        op.add_column('sensor_stations', sa.Column('commissioned_at', sa.DateTime(), nullable=True))
    if 'commissioned_by' not in st_cols:
        op.add_column('sensor_stations', sa.Column('commissioned_by', sa.String(128), nullable=True))

    # 2. Update sensor_observations
    obs_cols = [c['name'] for c in inspector.get_columns('sensor_observations')]
    if 'provenance' not in obs_cols:
        op.add_column('sensor_observations', sa.Column('provenance', sa.String(32), nullable=False, server_default='SIMULATED'))
    if 'environment' not in obs_cols:
        op.add_column('sensor_observations', sa.Column('environment', sa.String(32), nullable=False, server_default='TEST'))
    if 'qc_flags' not in obs_cols:
        op.add_column('sensor_observations', sa.Column('qc_flags', sa.String(255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    obs_cols = [c['name'] for c in inspector.get_columns('sensor_observations')]
    if 'qc_flags' in obs_cols:
        op.drop_column('sensor_observations', 'qc_flags')
    if 'environment' in obs_cols:
        op.drop_column('sensor_observations', 'environment')
    if 'provenance' in obs_cols:
        op.drop_column('sensor_observations', 'provenance')

    st_cols = [c['name'] for c in inspector.get_columns('sensor_stations')]
    if 'commissioned_by' in st_cols:
        op.drop_column('sensor_stations', 'commissioned_by')
    if 'commissioned_at' in st_cols:
        op.drop_column('sensor_stations', 'commissioned_at')
    if 'commissioning_data' in st_cols:
        op.drop_column('sensor_stations', 'commissioning_data')
