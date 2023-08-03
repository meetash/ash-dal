from unittest import TestCase

import pytest
from ash_dal.database.sync_database import Database
from ash_dal.exceptions.database import DBConnectionError
from sqlalchemy import select, text

from tests.constants import SYNC_DB_URL, SYNC_DB_URL__SLAVE


class CreateSyncDatabaseTestCase(TestCase):
    def setUp(self) -> None:
        self.main_db_url = SYNC_DB_URL
        self.replica_db_url = SYNC_DB_URL__SLAVE

    def test_create_sync_database(self):
        db = Database(
            db_url=self.main_db_url,
            read_replica_url=self.replica_db_url,
        )
        db.connect()
        assert db.engine
        assert db.read_only_engine
        assert db.session_maker
        db.disconnect()

    def test_create_sync_database__db_exception(self):
        url = self.main_db_url.set(drivername="incorrect")
        db = Database(
            db_url=url,
            read_replica_url=self.replica_db_url,
        )
        with pytest.raises(DBConnectionError):
            db.connect()

    def test_create_sync_database__session(self):
        db = Database(
            db_url=self.main_db_url,
            read_replica_url=self.replica_db_url,
        )
        db.connect()
        with db.session as session:
            r = session.execute(select(text("1")))
            assert r.scalar() == 1
