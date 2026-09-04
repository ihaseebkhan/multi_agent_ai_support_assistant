"""create streaming_subscription

Revision ID: 96fadc45df62
Revises: e4432b255bb1
Create Date: 2026-08-30 00:08:53.704032

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96fadc45df62'
down_revision: Union[str, Sequence[str], None] = 'e4432b255bb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "streaming_subscription",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "customer_id",
            sa.Integer(),
            sa.ForeignKey("customer.customer_id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("plan_name", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "start_date",
            sa.Date(),
            nullable=False,
            server_default=sa.text("CURRENT_DATE"),
        ),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column(
            "auto_renew",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )

    op.execute(
        """
        INSERT INTO streaming_subscription (customer_id, plan_name, status, start_date, end_date, auto_renew)
        VALUES (1, 'basic', 'active', CURRENT_DATE, CURRENT_DATE + INTERVAL '1 month', TRUE)
        """
    )


def downgrade() -> None:
    op.drop_table("streaming_subscription")
