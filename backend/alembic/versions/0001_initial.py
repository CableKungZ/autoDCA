"""initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dca_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("exchange", sa.Enum("binance", "bitkub", name="exchange"), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("quote_amount", sa.Numeric(18, 8), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("schedule_cron", sa.String(50), nullable=False),
        sa.Column("status", sa.Enum("active", "paused", "deleted", name="planstatus"), nullable=False, server_default="active"),
        sa.Column("max_retries", sa.Integer, nullable=False, server_default="3"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("dca_plans.id"), nullable=False),
        sa.Column("exchange", sa.String(20), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("side", sa.String(10), nullable=False, server_default="buy"),
        sa.Column("quote_amount", sa.Numeric(18, 8), nullable=False),
        sa.Column("base_amount", sa.Numeric(18, 8), nullable=True),
        sa.Column("price", sa.Numeric(18, 8), nullable=True),
        sa.Column("cost_per_token", sa.Numeric(18, 8), nullable=True),
        sa.Column("thb_usd_rate", sa.Numeric(18, 8), nullable=True),
        sa.Column("exchange_order_id", sa.String(100), nullable=True),
        sa.Column("status", sa.Enum("pending", "filled", "failed", "cancelled", name="orderstatus"), nullable=False, server_default="pending"),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("executed_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_orders_plan_id", "orders", ["plan_id"])
    op.create_index("ix_orders_executed_at", "orders", ["executed_at"])

    op.create_table(
        "rate_snapshots",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("rate", sa.Numeric(18, 8), nullable=False),
        sa.Column("source", sa.String(50), nullable=False, server_default="bitkub"),
        sa.Column("recorded_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_rate_snapshots_recorded_at", "rate_snapshots", ["recorded_at"])

    op.create_table(
        "log_entries",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("service", sa.String(50), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("context", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_log_entries_created_at", "log_entries", ["created_at"])


def downgrade() -> None:
    op.drop_table("log_entries")
    op.drop_table("rate_snapshots")
    op.drop_table("orders")
    op.drop_table("dca_plans")
    op.execute("DROP TYPE IF EXISTS exchange")
    op.execute("DROP TYPE IF EXISTS planstatus")
    op.execute("DROP TYPE IF EXISTS orderstatus")
