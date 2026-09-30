"""v3_4_device_sensor_schema

Revision ID: c4b1829e5a10
Revises: 6071286b9e46
Create Date: 2026-09-21 17:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4b1829e5a10'
down_revision: Union[str, Sequence[str], None] = '6071286b9e46'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    if 'devices' not in existing_tables:
        op.create_table(
            'devices',
            sa.Column('device_id', sa.String(64), primary_key=True),
            sa.Column('station_id', sa.String(64), sa.ForeignKey('sensor_stations.id'), nullable=False),
            sa.Column('serial_number', sa.String(64), unique=True, nullable=False),
            sa.Column('device_type', sa.String(64), nullable=False),
            sa.Column('manufacturer', sa.String(128), nullable=False, server_default='FloodyShield-Hardware'),
            sa.Column('firmware_version', sa.String(64), nullable=False, server_default='1.0.0'),
            sa.Column('protocol', sa.String(32), nullable=False, server_default='LORAWAN'),
            sa.Column('status', sa.String(32), nullable=False, server_default='PLANNED'),
            sa.Column('installed_at', sa.DateTime(), nullable=True),
            sa.Column('last_seen_at', sa.DateTime(), nullable=True),
            sa.Column('battery_level', sa.Float(), nullable=True),
            sa.Column('signal_strength', sa.Float(), nullable=True),
            sa.Column('latitude', sa.Float(), nullable=True),
            sa.Column('longitude', sa.Float(), nullable=True),
            sa.Column('elevation', sa.Float(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
        )
        op.create_index('ix_devices_station_id', 'devices', ['station_id'])
        op.create_index('ix_devices_serial_number', 'devices', ['serial_number'])

    if 'sensors' not in existing_tables:
        op.create_table(
            'sensors',
            sa.Column('sensor_id', sa.String(64), primary_key=True),
            sa.Column('device_id', sa.String(64), sa.ForeignKey('devices.device_id'), nullable=False),
            sa.Column('sensor_type', sa.String(64), nullable=False),
            sa.Column('unit', sa.String(32), nullable=False),
            sa.Column('measurement_range_min', sa.Float(), nullable=True),
            sa.Column('measurement_range_max', sa.Float(), nullable=True),
            sa.Column('sampling_interval_sec', sa.Integer(), nullable=False, server_default='60'),
            sa.Column('calibration_status', sa.String(32), nullable=False, server_default='VALID'),
            sa.Column('last_calibration_at', sa.DateTime(), nullable=True),
            sa.Column('next_calibration_at', sa.DateTime(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )
        op.create_index('ix_sensors_device_id', 'sensors', ['device_id'])
        op.create_index('ix_sensors_sensor_type', 'sensors', ['sensor_type'])

    if 'calibration_records' not in existing_tables:
        op.create_table(
            'calibration_records',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('sensor_id', sa.String(64), sa.ForeignKey('sensors.sensor_id'), nullable=False),
            sa.Column('calibrated_at', sa.DateTime(), nullable=False),
            sa.Column('calibrated_by', sa.String(128), nullable=False),
            sa.Column('standard_reference', sa.String(128), nullable=True),
            sa.Column('zero_offset', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('scale_factor', sa.Float(), nullable=False, server_default='1.0'),
            sa.Column('notes', sa.Text(), nullable=True),
        )
        op.create_index('ix_calibration_records_sensor_id', 'calibration_records', ['sensor_id'])

    if 'device_heartbeats' not in existing_tables:
        op.create_table(
            'device_heartbeats',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('device_id', sa.String(64), sa.ForeignKey('devices.device_id'), nullable=False),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.Column('battery_voltage', sa.Float(), nullable=True),
            sa.Column('battery_percentage', sa.Float(), nullable=True),
            sa.Column('rssi_dbm', sa.Float(), nullable=True),
            sa.Column('snr_db', sa.Float(), nullable=True),
            sa.Column('firmware_version', sa.String(64), nullable=True),
            sa.Column('error_flags', sa.Integer(), nullable=False, server_default='0'),
        )
        op.create_index('ix_device_heartbeats_device_id', 'device_heartbeats', ['device_id'])
        op.create_index('ix_device_heartbeats_timestamp', 'device_heartbeats', ['timestamp'])

    # Add columns to sensor_observations if they do not exist
    obs_cols = {c['name'] for c in inspector.get_columns('sensor_observations')}
    with op.batch_alter_table('sensor_observations') as batch_op:
        if 'device_id' not in obs_cols:
            batch_op.add_column(sa.Column('device_id', sa.String(64), nullable=True))
        if 'sensor_id' not in obs_cols:
            batch_op.add_column(sa.Column('sensor_id', sa.String(64), nullable=True))
        if 'source_event_id' not in obs_cols:
            batch_op.add_column(sa.Column('source_event_id', sa.String(128), nullable=True))
            batch_op.create_unique_constraint('uq_sensor_obs_source_event_id', ['source_event_id'])
        if 'observed_at' not in obs_cols:
            batch_op.add_column(sa.Column('observed_at', sa.DateTime(), nullable=True))
        if 'received_at' not in obs_cols:
            batch_op.add_column(sa.Column('received_at', sa.DateTime(), nullable=True))
        if 'processed_at' not in obs_cols:
            batch_op.add_column(sa.Column('processed_at', sa.DateTime(), nullable=True))
        if 'measurement_type' not in obs_cols:
            batch_op.add_column(sa.Column('measurement_type', sa.String(64), nullable=True))
        if 'value' not in obs_cols:
            batch_op.add_column(sa.Column('value', sa.Float(), nullable=True))
        if 'unit' not in obs_cols:
            batch_op.add_column(sa.Column('unit', sa.String(32), nullable=True))
        if 'sequence_number' not in obs_cols:
            batch_op.add_column(sa.Column('sequence_number', sa.Integer(), nullable=True))
        if 'temporal_state' not in obs_cols:
            batch_op.add_column(sa.Column('temporal_state', sa.String(32), nullable=False, server_default='VALID'))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    if 'device_heartbeats' in existing_tables:
        op.drop_table('device_heartbeats')
    if 'calibration_records' in existing_tables:
        op.drop_table('calibration_records')
    if 'sensors' in existing_tables:
        op.drop_table('sensors')
    if 'devices' in existing_tables:
        op.drop_table('devices')
