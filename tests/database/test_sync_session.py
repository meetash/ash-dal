from unittest import TestCase
from unittest.mock import MagicMock

import pytest
from ash_dal.database.sync_database import Database
from sqlalchemy import Column, Integer, MetaData, String, Table, delete, insert, select, text
from sqlalchemy.exc import UnboundExecutionError

from tests.constants import SYNC_DB_URL, SYNC_DB_URL__SLAVE


class CreateSyncSessionTestCase(TestCase):
    def setUp(self) -> None:
        self.db = Database(
            db_url=SYNC_DB_URL,
            read_replica_url=SYNC_DB_URL__SLAVE,
        )
        self.metadata = MetaData()
        self.db.connect()
        self.test_table = Table(
            "users",
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column("name", String(30)),
            Column("fullname", String(64)),
        )
        self.metadata.create_all(self.db.engine)

    def tearDown(self) -> None:
        with self.db.engine.connect() as connection:
            for tbl in reversed(self.metadata.sorted_tables):
                connection.execute(delete(tbl))
                connection.commit()

    def test_sync_session__select(self):
        with self.db.session as session:
            r = session.execute(select(text("1")))
            assert r.scalar() == 1

    def test_sync_session__insert_and_select(self):
        id_, name, fullname = 1, "John", "John Doe"
        with self.db.session as session:
            session.execute(insert(self.test_table).values(id=id_, name=name, fullname=fullname))
            session.commit()
            r = session.execute(select(self.test_table).where(self.test_table.c.id == 1)).first()
            assert r
            assert r.id == id_
            assert r.name == name

    def test_sync_session__insert_and_select_mocked(self):
        slave_engine = MagicMock()
        master_engine = MagicMock()
        id_, name, fullname = 1, "John", "John Doe"
        with self.db.session as session:
            session.info["master"] = master_engine
            session.info["slave"] = slave_engine
            insert_response = session.execute(insert(self.test_table).values(id=id_, name=name, fullname=fullname))
            session.commit()
            assert insert_response == master_engine.connect.return_value.execute.return_value
            select_response = session.execute(select(self.test_table).where(self.test_table.c.id == 1)).first()
            assert select_response == slave_engine.connect.return_value.execute.return_value.first.return_value

    def test_sync_session__insert_and_select_no_engines(self):
        with self.db.session as session:
            session.info["master"] = None
            session.info["slave"] = None
            with pytest.raises(UnboundExecutionError):
                session.execute(select(text("1"))).scalar()
