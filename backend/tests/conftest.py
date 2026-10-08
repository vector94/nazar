import os

# Must be set before `shared` is imported; otherwise it loads backend/.env,
# which points at the dev database and the real Slack webhook.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["SLACK_WEBHOOK_URL"] = ""

from pathlib import Path
from typing import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared import Base


@pytest.fixture
async def session(tmp_path: Path) -> AsyncIterator[AsyncSession]:
    db_path = os.path.join(tmp_path, "test.db")
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as db:
        yield db

    await engine.dispose()
