"""create previous sessions table

Revision ID: 67bdd768be96
Revises: 
Create Date: 2024-01-27 02:31:24.087602

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67bdd768be96'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "previous_sessions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("topic", sa.String(255), nullable=False),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("duration", sa.String(255), nullable=False),
        sa.Column("date", sa.DateTime, nullable=False),
        sa.Column("slides", sa.String(255), nullable=False),
        sa.Column("recording", sa.String(255), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("chat log", sa.String(255), nullable=False),
        sa.Column("tags", sa.String(255), nullable=False),
        sa.Column("thumbnails", sa.String(255), nullable=False),
    )



def downgrade() -> None:
    op.drop_table("previous_sessions")

