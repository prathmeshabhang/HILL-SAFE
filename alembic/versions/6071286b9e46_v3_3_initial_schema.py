"""v3_3_initial_schema

Revision ID: 6071286b9e46
Revises: 
Create Date: 2026-09-21 17:23:09.251034

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6071286b9e46'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Creates complete v3.3 initial schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    if 'users' not in existing_tables:
        op.create_table(
            'users',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('username', sa.String(64), nullable=False, unique=True),
            sa.Column('email', sa.String(128), nullable=False, unique=True),
            sa.Column('hashed_password', sa.String(255), nullable=False),
            sa.Column('role', sa.String(32), nullable=False, server_default='OBSERVER'),
            sa.Column('full_name', sa.String(128), nullable=True),
            sa.Column('agency', sa.String(128), nullable=False, server_default='HPSDMA / Kullu Civil Defense'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )

    if 'incidents' not in existing_tables:
        op.create_table(
            'incidents',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('incident_type', sa.String(64), nullable=False),
            sa.Column('severity_level', sa.String(32), nullable=False, server_default='CRITICAL'),
            sa.Column('trigger_source', sa.String(64), nullable=False, server_default='SATELLITE_SYNTHESIS'),
            sa.Column('trigger_location', sa.String(128), nullable=False),
            sa.Column('latitude', sa.Float(), nullable=True),
            sa.Column('longitude', sa.Float(), nullable=True),
            sa.Column('dam_height_m', sa.Float(), nullable=True),
            sa.Column('impounded_volume_m3', sa.Float(), nullable=True),
            sa.Column('rainfall_rate_mmh', sa.Float(), nullable=True),
            sa.Column('status', sa.String(32), nullable=False, server_default='ACTIVE'),
            sa.Column('summary', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
        )

    if 'sensor_stations' not in existing_tables:
        op.create_table(
            'sensor_stations',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('name', sa.String(128), nullable=False),
            sa.Column('station_type', sa.String(64), nullable=False),
            sa.Column('latitude', sa.Float(), nullable=False),
            sa.Column('longitude', sa.Float(), nullable=False),
            sa.Column('elevation_m', sa.Float(), nullable=True),
            sa.Column('river_basin', sa.String(128), server_default='Upper Beas Basin'),
            sa.Column('is_active', sa.Boolean(), server_default=sa.true()),
            sa.Column('last_heartbeat', sa.DateTime(), nullable=True),
        )

    if 'sensor_observations' not in existing_tables:
        op.create_table(
            'sensor_observations',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('station_id', sa.String(64), sa.ForeignKey('sensor_stations.id'), nullable=False),
            sa.Column('data_source_id', sa.String(64), nullable=True, server_default='UPPER_BEAS_IOT'),
            sa.Column('idempotency_hash', sa.String(64), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.Column('rainfall_rate_mmh', sa.Float(), nullable=True),
            sa.Column('water_level_m', sa.Float(), nullable=True),
            sa.Column('pore_pressure_kpa', sa.Float(), nullable=True),
            sa.Column('displacement_mm', sa.Float(), nullable=True),
            sa.Column('acoustic_emission_db', sa.Float(), nullable=True),
            sa.Column('is_anomalous', sa.Boolean(), server_default=sa.false()),
            sa.Column('anomaly_score', sa.Float(), server_default='0.0'),
            sa.Column('anomaly_reason', sa.String(255), nullable=True),
            sa.Column('quality_state', sa.String(32), nullable=False, server_default='FRESH'),
            sa.Column('provenance_json', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )

    if 'model_runs' not in existing_tables:
        op.create_table(
            'model_runs',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('model_id', sa.String(32), nullable=False),
            sa.Column('model_name', sa.String(128), nullable=False),
            sa.Column('model_version', sa.String(32), nullable=False, server_default='3.3.0'),
            sa.Column('artifact_hash', sa.String(64), nullable=True),
            sa.Column('evidence_status', sa.String(64), nullable=False, server_default='PROTOTYPE'),
            sa.Column('run_timestamp', sa.DateTime(), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('execution_time_ms', sa.Float(), nullable=False),
            sa.Column('input_hash', sa.String(64), nullable=False),
            sa.Column('output_hash', sa.String(64), nullable=True),
            sa.Column('input_reference', sa.Text(), nullable=True),
            sa.Column('output_reference', sa.Text(), nullable=True),
            sa.Column('output_summary', sa.Text(), nullable=True),
            sa.Column('confidence_score', sa.Float(), nullable=True),
            sa.Column('status', sa.String(32), nullable=False, server_default='SUCCESS'),
            sa.Column('quality_state', sa.String(32), nullable=False, server_default='FRESH'),
            sa.Column('error_message', sa.Text(), nullable=True),
        )

    if 'alert_dispatches' not in existing_tables:
        op.create_table(
            'alert_dispatches',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('incident_id', sa.String(64), sa.ForeignKey('incidents.id'), nullable=True),
            sa.Column('cap_identifier', sa.String(128), nullable=False, unique=True),
            sa.Column('alert_type', sa.String(32), nullable=False, server_default='Alert'),
            sa.Column('urgency', sa.String(32), nullable=False, server_default='Immediate'),
            sa.Column('severity', sa.String(32), nullable=False, server_default='Extreme'),
            sa.Column('certainty', sa.String(32), nullable=False, server_default='Observed'),
            sa.Column('headline', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('instruction', sa.Text(), nullable=True),
            sa.Column('area_desc', sa.String(255), nullable=False),
            sa.Column('polygon_geojson', sa.Text(), nullable=True),
            sa.Column('cap_xml', sa.Text(), nullable=True),
            sa.Column('authorized_by', sa.String(128), nullable=False),
            sa.Column('status', sa.String(32), nullable=False, server_default='PENDING_APPROVAL'),
            sa.Column('dispatched_at', sa.DateTime(), nullable=True),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )

    if 'alert_acknowledgements' not in existing_tables:
        op.create_table(
            'alert_acknowledgements',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('alert_id', sa.String(64), sa.ForeignKey('alert_dispatches.id'), nullable=False),
            sa.Column('recipient_id', sa.String(128), nullable=False),
            sa.Column('channel', sa.String(32), nullable=False, server_default='EOC_DASHBOARD'),
            sa.Column('status', sa.String(32), nullable=False, server_default='RECEIVED'),
            sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
        )

    if 'evacuation_routes' not in existing_tables:
        op.create_table(
            'evacuation_routes',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('incident_id', sa.String(64), sa.ForeignKey('incidents.id'), nullable=True),
            sa.Column('origin_name', sa.String(128), nullable=False),
            sa.Column('destination_safe_zone', sa.String(128), nullable=False),
            sa.Column('distance_km', sa.Float(), nullable=False),
            sa.Column('estimated_duration_min', sa.Float(), nullable=False),
            sa.Column('clearance_status', sa.String(32), nullable=False, server_default='CLEAR'),
            sa.Column('route_geojson', sa.Text(), nullable=True),
            sa.Column('computed_at', sa.DateTime(), nullable=True),
        )

    if 'audit_logs' not in existing_tables:
        op.create_table(
            'audit_logs',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.Column('action', sa.String(64), nullable=False),
            sa.Column('actor_id', sa.String(128), nullable=False),
            sa.Column('actor_role', sa.String(64), nullable=False),
            sa.Column('target_entity_type', sa.String(64), nullable=False),
            sa.Column('target_entity_id', sa.String(64), nullable=False),
            sa.Column('changes', sa.Text(), nullable=True),
            sa.Column('ip_address', sa.String(64), nullable=True),
            sa.Column('previous_hash', sa.String(64), nullable=True),
            sa.Column('entry_hash', sa.String(64), nullable=True),
        )

    if 'risk_states' not in existing_tables:
        op.create_table(
            'risk_states',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('incident_id', sa.String(64), sa.ForeignKey('incidents.id'), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.Column('location_name', sa.String(128), nullable=False),
            sa.Column('latitude', sa.Float(), nullable=True),
            sa.Column('longitude', sa.Float(), nullable=True),
            sa.Column('flood_hazard_json', sa.Text(), nullable=True),
            sa.Column('landslide_hazard_json', sa.Text(), nullable=True),
            sa.Column('cascade_hazard_json', sa.Text(), nullable=True),
            sa.Column('population_impact_json', sa.Text(), nullable=True),
            sa.Column('infrastructure_impact_json', sa.Text(), nullable=True),
            sa.Column('overall_risk_level', sa.String(32), nullable=False, server_default='MODERATE'),
            sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.85'),
            sa.Column('quality_state', sa.String(32), nullable=False, server_default='FRESH'),
            sa.Column('provenance_json', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )

    if 'risk_zones' not in existing_tables:
        op.create_table(
            'risk_zones',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('name', sa.String(128), nullable=False),
            sa.Column('zone_type', sa.String(64), nullable=False),
            sa.Column('risk_level', sa.String(32), nullable=False, server_default='HIGH'),
            sa.Column('geometry_geojson', sa.Text(), nullable=False),
            sa.Column('is_active', sa.String(16), nullable=False, server_default='ACTIVE'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )

    if 'data_ingestion_runs' not in existing_tables:
        op.create_table(
            'data_ingestion_runs',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('source_id', sa.String(64), nullable=False),
            sa.Column('start_time', sa.DateTime(), nullable=True),
            sa.Column('end_time', sa.DateTime(), nullable=True),
            sa.Column('records_fetched', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('records_accepted', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('records_rejected', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('status', sa.String(32), nullable=False, server_default='COMPLETED'),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )

    if 'data_quality_records' not in existing_tables:
        op.create_table(
            'data_quality_records',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('ingestion_run_id', sa.String(64), nullable=True),
            sa.Column('source_id', sa.String(64), nullable=False),
            sa.Column('station_or_scene_id', sa.String(128), nullable=False),
            sa.Column('observation_timestamp', sa.DateTime(), nullable=False),
            sa.Column('quality_state', sa.String(32), nullable=False, server_default='FRESH'),
            sa.Column('rule_evaluated', sa.String(64), nullable=False),
            sa.Column('passed', sa.String(8), nullable=False, server_default='PASS'),
            sa.Column('rejection_reason', sa.String(255), nullable=True),
            sa.Column('details_json', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )

    if 'infrastructure_assets' not in existing_tables:
        op.create_table(
            'infrastructure_assets',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('name', sa.String(128), nullable=False),
            sa.Column('asset_type', sa.String(64), nullable=False),
            sa.Column('sector', sa.String(64), nullable=False, server_default='AUT_LARJI_CORRIDOR'),
            sa.Column('latitude', sa.Float(), nullable=True),
            sa.Column('longitude', sa.Float(), nullable=True),
            sa.Column('geometry_geojson', sa.Text(), nullable=True),
            sa.Column('replacement_cost_inr', sa.Float(), nullable=False, server_default='10000000.0'),
            sa.Column('criticality_tier', sa.String(16), nullable=False, server_default='TIER_1'),
            sa.Column('is_operational', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )

    if 'population_zones' not in existing_tables:
        op.create_table(
            'population_zones',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('ward_name', sa.String(128), nullable=False),
            sa.Column('settlement_name', sa.String(128), nullable=False),
            sa.Column('resident_population', sa.Integer(), nullable=False, server_default='1000'),
            sa.Column('peak_tourist_population', sa.Integer(), nullable=False, server_default='500'),
            sa.Column('vulnerability_index', sa.Float(), nullable=False, server_default='0.5'),
            sa.Column('geometry_geojson', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )

    if 'safe_zones' not in existing_tables:
        op.create_table(
            'safe_zones',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('name', sa.String(128), nullable=False),
            sa.Column('safe_zone_type', sa.String(64), nullable=False, server_default='COMMUNITY_CENTER'),
            sa.Column('latitude', sa.Float(), nullable=False),
            sa.Column('longitude', sa.Float(), nullable=False),
            sa.Column('elevation_m', sa.Float(), nullable=False),
            sa.Column('capacity_headcount', sa.Integer(), nullable=False, server_default='500'),
            sa.Column('suitability_score', sa.Float(), nullable=False, server_default='0.9'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )


def downgrade() -> None:
    """Drops tables in reverse order."""
    tables = [
        'safe_zones', 'population_zones', 'infrastructure_assets',
        'data_quality_records', 'data_ingestion_runs', 'risk_zones',
        'risk_states', 'audit_logs', 'evacuation_routes',
        'alert_acknowledgements', 'alert_dispatches', 'model_runs',
        'sensor_observations', 'sensor_stations', 'incidents', 'users'
    ]
    for table in tables:
        try:
            op.drop_table(table)
        except Exception:
            pass
