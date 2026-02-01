import asyncio
from sqlalchemy import text

from .database import engine, Base
from .models import Metric, Alert


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        await conn.execute(text("""
            SELECT create_hypertable('metrics', 'timestamp', if_not_exists => TRUE);
        """))

    print("Database initialized successfully")


if __name__ == "__main__":
    asyncio.run(init_db())
