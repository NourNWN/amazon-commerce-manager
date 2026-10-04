import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

from app.config import settings
from app.database import Base
from app.models.supplier import Supplier  # noqa: F401  ← كل نموذج جديد يُضاف هنا لاحقًا
from app.models.product import Product    # noqa: F401
from app.models.shipping_route import ShippingRoute  # noqa: F401
from app.models.listing import Listing  # noqa: F401
from app.models.order import Order  # noqa: F401
from app.models.risk_check import RiskCheck  # noqa: F401
from app.models.wallet_transaction import WalletTransaction  # noqa: F401
from app.models.account_health_snapshot import AccountHealthSnapshot  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(settings.database_url, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())