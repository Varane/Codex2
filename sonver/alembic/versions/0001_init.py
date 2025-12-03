"""initial tables and seed data

Revision ID: 0001
Revises: 
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'vehicle_make',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_vehicle_make_id'), 'vehicle_make', ['id'], unique=False)

    op.create_table(
        'vehicle_model',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('make_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['make_id'], ['vehicle_make.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_model_id'), 'vehicle_model', ['id'], unique=False)

    op.create_table(
        'vehicle_submodel',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['model_id'], ['vehicle_model.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_submodel_id'), 'vehicle_submodel', ['id'], unique=False)

    op.create_table(
        'vehicle_engine',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('submodel_id', sa.Integer(), nullable=False),
        sa.Column('engine_name', sa.String(), nullable=False),
        sa.Column('year_start', sa.Integer(), nullable=False),
        sa.Column('year_end', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['submodel_id'], ['vehicle_submodel.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_engine_id'), 'vehicle_engine', ['id'], unique=False)

    op.create_table(
        'part_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('make_id', sa.Integer(), nullable=True),
        sa.Column('model_id', sa.Integer(), nullable=True),
        sa.Column('submodel_id', sa.Integer(), nullable=True),
        sa.Column('engine_id', sa.Integer(), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('vin', sa.String(), nullable=True),
        sa.Column('oem', sa.String(), nullable=True),
        sa.Column('part_name', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('message_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('user_ip', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['engine_id'], ['vehicle_engine.id']),
        sa.ForeignKeyConstraint(['make_id'], ['vehicle_make.id']),
        sa.ForeignKeyConstraint(['model_id'], ['vehicle_model.id']),
        sa.ForeignKeyConstraint(['submodel_id'], ['vehicle_submodel.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_part_requests_id'), 'part_requests', ['id'], unique=False)

    # Seed data
    connection = op.get_bind()
    make_table = sa.table('vehicle_make', sa.column('id', sa.Integer), sa.column('name', sa.String))
    model_table = sa.table('vehicle_model', sa.column('id', sa.Integer), sa.column('make_id', sa.Integer), sa.column('name', sa.String))
    submodel_table = sa.table('vehicle_submodel', sa.column('id', sa.Integer), sa.column('model_id', sa.Integer), sa.column('name', sa.String))
    engine_table = sa.table(
        'vehicle_engine',
        sa.column('id', sa.Integer),
        sa.column('submodel_id', sa.Integer),
        sa.column('engine_name', sa.String),
        sa.column('year_start', sa.Integer),
        sa.column('year_end', sa.Integer),
    )

    connection.execute(make_table.insert(), [
        {'id': 1, 'name': 'BMW'},
        {'id': 2, 'name': 'Peugeot'},
    ])

    connection.execute(model_table.insert(), [
        {'id': 1, 'make_id': 1, 'name': '3 Series'},
        {'id': 2, 'make_id': 2, 'name': '308'},
    ])

    connection.execute(submodel_table.insert(), [
        {'id': 1, 'model_id': 1, 'name': 'F30'},
        {'id': 2, 'model_id': 2, 'name': 'T9'},
    ])

    connection.execute(engine_table.insert(), [
        {'id': 1, 'submodel_id': 1, 'engine_name': 'N20', 'year_start': 2012, 'year_end': 2016},
        {'id': 2, 'submodel_id': 1, 'engine_name': 'B48', 'year_start': 2016, 'year_end': 2019},
        {'id': 3, 'submodel_id': 2, 'engine_name': '1.2 PureTech', 'year_start': 2014, 'year_end': 2021},
        {'id': 4, 'submodel_id': 2, 'engine_name': '1.6 THP', 'year_start': 2014, 'year_end': 2018},
    ])


def downgrade():
    op.drop_index(op.f('ix_part_requests_id'), table_name='part_requests')
    op.drop_table('part_requests')
    op.drop_index(op.f('ix_vehicle_engine_id'), table_name='vehicle_engine')
    op.drop_table('vehicle_engine')
    op.drop_index(op.f('ix_vehicle_submodel_id'), table_name='vehicle_submodel')
    op.drop_table('vehicle_submodel')
    op.drop_index(op.f('ix_vehicle_model_id'), table_name='vehicle_model')
    op.drop_table('vehicle_model')
    op.drop_index(op.f('ix_vehicle_make_id'), table_name='vehicle_make')
    op.drop_table('vehicle_make')
