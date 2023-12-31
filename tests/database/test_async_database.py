from unittest import IsolatedAsyncioTestCase

import pytest
from ash_dal.database.async_database import AsyncDatabase
from ash_dal.exceptions.database import DBConnectionError
from sqlalchemy import select, text

from tests.constants import ASYNC_DB_URL, ASYNC_DB_URL__SLAVE


class CreateSyncDatabaseTestCase(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.main_db_url = ASYNC_DB_URL
        self.replica_db_url = ASYNC_DB_URL__SLAVE

    async def test_create_async_database(self):
        db = AsyncDatabase(
            db_url=self.main_db_url,
            read_replica_url=self.replica_db_url,
        )
        await db.connect()
        assert db.engine
        assert db.read_only_engine
        assert db.session_maker
        await db.disconnect()

    async def test_create_async_database__db_exception(self):
        url = self.main_db_url.set(drivername="incorrect")
        db = AsyncDatabase(
            db_url=url,
            read_replica_url=self.replica_db_url,
        )
        with pytest.raises(DBConnectionError):
            await db.connect()

    async def test_create_async_database__session(self):
        db = AsyncDatabase(
            db_url=self.main_db_url,
            read_replica_url=self.replica_db_url,
        )
        await db.connect()
        async with db.session as session:
            r = await session.execute(select(text("1")))
            assert r.scalar() == 1
        await db.disconnect()
