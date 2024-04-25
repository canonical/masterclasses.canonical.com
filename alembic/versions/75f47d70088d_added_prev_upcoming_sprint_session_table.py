"""Added prev,upcoming,sprint session table

Revision ID: 75f47d70088d
Revises: 
Create Date: 2024-03-06 21:23:01.910134

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75f47d70088d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('previous_sessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('topic', sa.String(), nullable=False),
    sa.Column('owner', sa.String(), nullable=False),
    sa.Column('duration', sa.String(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False, index=True),
    sa.Column('slides', sa.String(), nullable=True),
    sa.Column('recording', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('chat_log', sa.String(), nullable=True),
    sa.Column('tags', sa.String(), nullable=True),
    sa.Column('thumbnails', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_table('sprint_sessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('topic', sa.String(), nullable=False),
    sa.Column('owner', sa.String(), nullable=False),
    sa.Column('duration', sa.String(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False, index=True),
    sa.Column('slides', sa.String(), nullable=True),
    sa.Column('recording', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('chat_log', sa.String(), nullable=True),
    sa.Column('tags', sa.String(), nullable=True),
    sa.Column('thumbnails', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('upcoming_sessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('topic', sa.String(), nullable=False),
    sa.Column('owner', sa.String(), nullable=False),
    sa.Column('duration', sa.String(), nullable=False),
    sa.Column('date', sa.Date(), nullable=True, index=True),
    sa.Column('notes', sa.String(), nullable=True),
    sa.Column('event', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('upcoming_sessions')
    op.drop_table('sprint_sessions')
    op.drop_table('previous_sessions')
