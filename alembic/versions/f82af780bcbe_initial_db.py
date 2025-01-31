"""Initial DB

Revision ID: f82af780bcbe
Revises: 
Create Date: 2025-01-31 15:32:04.797584

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f82af780bcbe'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


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
        sa.Column('hrc_id', sa.String(), nullable=False, unique=True),
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

    op.create_table(
        'video_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('duration', sa.String(50), nullable=False),
        sa.Column('email', sa.String(200), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('video_tags')
    op.drop_table('video_presenters')
    op.drop_table('tag')
    op.drop_table('tag_category')
    op.drop_table('presenters')
    op.drop_table('videos')
    op.drop_table('video_submissions')
