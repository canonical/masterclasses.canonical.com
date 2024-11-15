"""initial schema

Revision ID: xxxx
Revises: 
Create Date: 2024-xx-xx
"""
from alembic import op
import sqlalchemy as sa

revision = 'xxxx'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create videos table
    op.create_table(
        'videos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('unixstart', sa.Integer(), nullable=False),
        sa.Column('unixend', sa.Integer(), nullable=False),
        sa.Column('stream', sa.String(), nullable=True),
        sa.Column('slides', sa.String(), nullable=True),
        sa.Column('recording', sa.String(), nullable=True),
        sa.Column('chat_log', sa.String(), nullable=True),
        sa.Column('thumbnails', sa.String(), nullable=True),
        sa.Column('calendar_event', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create presenters table
    op.create_table(
        'presenters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('hrc_id', sa.Integer(), nullable=True),
        sa.Column('headshot', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create tag_category table
    op.create_table(
        'tag_category',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create tag table
    op.create_table(
        'tag',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('tag_type_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['tag_type_id'], ['tag_category.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create video_presenters association table
    op.create_table(
        'video_presenters',
        sa.Column('video_id', sa.Integer(), nullable=False),
        sa.Column('presenter_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['presenter_id'], ['presenters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('video_id', 'presenter_id')
    )

    # Create video_tags association table
    op.create_table(
        'video_tags',
        sa.Column('video_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('video_id', 'tag_id')
    )

def downgrade() -> None:
    op.drop_table('video_tags')
    op.drop_table('video_presenters')
    op.drop_table('tag')
    op.drop_table('tag_category')
    op.drop_table('presenters')
    op.drop_table('videos') 