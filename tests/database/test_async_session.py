from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock

import pytest
from ash_dal.database import AsyncDatabase
from sqlalchemy import URL, Column, Integer, MetaData, String, Table, insert, select, text
from sqlalchemy.exc import UnboundExecutionError


class CreateAsyncSessionTestCase(IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        main_db_url = URL.create(
            drivername="mysql+aiomysql",
            username="my_db_user",
            password="S3cret",
            host="127.0.0.1",
            port=3306,
            database="my_db",
        )
        replica_db_url = URL.create(
            drivername="mysql+aiomysql",
            username="my_db_user",
            password="S3cret",
            host="127.0.0.1",
            port=3307,
            database="my_db",
        )
        self.db = AsyncDatabase(
            db_url=main_db_url,
            read_replica_url=replica_db_url,
        )
        self.metadata = MetaData()
        await self.db.connect()
        self.test_table = Table(
            "users",
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column("name", String(30)),
            Column("fullname", String(64)),
        )
        async with self.db.engine.begin() as conn:
            await conn.run_sync(self.metadata.drop_all)
            await conn.run_sync(self.metadata.create_all)

    async def test_async_session__select(self):
        async with self.db.session as session:
            r = await session.execute(select(text("1")))
            assert r.scalar() == 1

    async def test_async_session__insert_and_select(self):
        id_, name, fullname = 1, "John", "John Doe"
        async with self.db.session as session:
            await session.execute(insert(self.test_table).values(id=id_, name=name, fullname=fullname))
            await session.commit()
            r = await session.execute(select(self.test_table).where(self.test_table.c.id == 1))
            data = r.first()
            assert data
            assert data.id == id_
            assert data.name == name

    async def test_async_session__insert_and_select_mocked(self):
        slave_engine = MagicMock()
        slave_engine.connect.return_value.execute.return_value.context._is_server_side = None
        master_engine = MagicMock()
        master_engine.connect.return_value.execute.return_value.context._is_server_side = None
        id_, name, fullname = 1, "John", "John Doe"
        async with self.db.session as session:
            session.info["master"] = master_engine
            session.info["slave"] = slave_engine
            insert_response = await session.execute(
                insert(self.test_table).values(id=id_, name=name, fullname=fullname)
            )
            await session.commit()
            assert insert_response == master_engine.connect.return_value.execute.return_value
            select_response = await session.execute(select(self.test_table).where(self.test_table.c.id == 1))
            result = select_response.first()
            assert result == slave_engine.connect.return_value.execute.return_value.first.return_value

    async def test_async_session__insert_and_select_no_engines(self):
        async with self.db.session as session:
            session.info["master"] = None
            session.info["slave"] = None
            with pytest.raises(UnboundExecutionError):
                await session.execute(select(text("1")))
