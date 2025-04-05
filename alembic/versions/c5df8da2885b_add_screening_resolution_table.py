"""add_screening_resolution_table

Revision ID: c5df8da2885b
Revises: 2c7373437db5
Create Date: 2025-04-04 18:50:39.420222+00:00

"""
from typing import Union
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c5df8da2885b'
down_revision: str | None = '2c7373437db5'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('screening_resolutions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("TIMEZONE('UTC', CURRENT_TIMESTAMP)"), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("TIMEZONE('UTC', CURRENT_TIMESTAMP)"), nullable=True),
    sa.Column('pubmed_result_id', sa.Uuid(), nullable=False),
    sa.Column('review_id', sa.Uuid(), nullable=False),
    sa.Column('conservative_result_id', sa.Uuid(), nullable=False),
    sa.Column('comprehensive_result_id', sa.Uuid(), nullable=False),
    sa.Column('resolver_decision', postgresql.ENUM('INCLUDE', 'EXCLUDE', 'UNCERTAIN', name='screeningdecisiontype', create_type=False), nullable=False),
    sa.Column('resolver_reasoning', sa.Text(), nullable=False),
    sa.Column('resolver_confidence_score', sa.Float(), nullable=False),
    sa.Column('resolver_model_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('resolver_include', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('response_metadata', postgresql.JSONB(none_as_null=True, astext_type=sa.Text()), nullable=False),
    sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('trace_id', sa.Uuid(), nullable=True),
    sa.ForeignKeyConstraint(['comprehensive_result_id'], ['screen_abstract_results.id'], ),
    sa.ForeignKeyConstraint(['conservative_result_id'], ['screen_abstract_results.id'], ),
    sa.ForeignKeyConstraint(['pubmed_result_id'], ['pubmed_results.id'], ),
    sa.ForeignKeyConstraint(['review_id'], ['systematic_reviews.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_screening_resolutions_comprehensive_result_id'), 'screening_resolutions', ['comprehensive_result_id'], unique=False)
    op.create_index(op.f('ix_screening_resolutions_conservative_result_id'), 'screening_resolutions', ['conservative_result_id'], unique=False)
    op.create_index('ix_screening_resolutions_on_resolver_include_gin', 'screening_resolutions', [sa.text('resolver_include')], unique=False, postgresql_using='gin')
    op.create_index('ix_screening_resolutions_on_response_metadata_gin', 'screening_resolutions', [sa.text('response_metadata')], unique=False, postgresql_using='gin')
    op.create_index(op.f('ix_screening_resolutions_pubmed_result_id'), 'screening_resolutions', ['pubmed_result_id'], unique=False)
    op.create_index(op.f('ix_screening_resolutions_resolver_decision'), 'screening_resolutions', ['resolver_decision'], unique=False)
    op.create_index(op.f('ix_screening_resolutions_review_id'), 'screening_resolutions', ['review_id'], unique=False)
    op.create_index(op.f('ix_screening_resolutions_trace_id'), 'screening_resolutions', ['trace_id'], unique=False)
    op.add_column('pubmed_results', sa.Column('resolution_id', sa.Uuid(), nullable=True))
    op.create_index(op.f('ix_pubmed_results_resolution_id'), 'pubmed_results', ['resolution_id'], unique=False)
    op.create_foreign_key(None, 'pubmed_results', 'screening_resolutions', ['resolution_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'pubmed_results', type_='foreignkey')
    op.drop_index(op.f('ix_pubmed_results_resolution_id'), table_name='pubmed_results')
    op.drop_column('pubmed_results', 'resolution_id')
    op.drop_index(op.f('ix_screening_resolutions_trace_id'), table_name='screening_resolutions')
    op.drop_index(op.f('ix_screening_resolutions_review_id'), table_name='screening_resolutions')
    op.drop_index(op.f('ix_screening_resolutions_resolver_decision'), table_name='screening_resolutions')
    op.drop_index(op.f('ix_screening_resolutions_pubmed_result_id'), table_name='screening_resolutions')
    op.drop_index('ix_screening_resolutions_on_response_metadata_gin', table_name='screening_resolutions', postgresql_using='gin')
    op.drop_index('ix_screening_resolutions_on_resolver_include_gin', table_name='screening_resolutions', postgresql_using='gin')
    op.drop_index(op.f('ix_screening_resolutions_conservative_result_id'), table_name='screening_resolutions')
    op.drop_index(op.f('ix_screening_resolutions_comprehensive_result_id'), table_name='screening_resolutions')
    op.drop_table('screening_resolutions')
    # ### end Alembic commands ###
