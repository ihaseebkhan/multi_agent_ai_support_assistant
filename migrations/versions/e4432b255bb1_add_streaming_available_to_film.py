"""add streaming_available to film

Revision ID: e4432b255bb1
Revises: a0ad47384753
Create Date: 2026-08-30 00:08:22.837556

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4432b255bb1'
down_revision: Union[str, Sequence[str], None] = 'a0ad47384753'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "film",
        sa.Column(
            "streaming_available",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("film", "streaming_available")
