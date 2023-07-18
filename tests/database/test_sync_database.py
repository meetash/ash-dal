from unittest import TestCase

import pytest
from ash_dal.database.sync_database import Database
from ash_dal.exceptions.database import DBConnectionError
from sqlalchemy import URL, text


class CreateSyncDatabaseTestCase(TestCase):
    def setUp(self) -> None:
        self.main_db_url = URL.create(
            drivername="mysql+pymysql",
            username="my_db_user",
            password="S3cret",
            host="127.0.0.1",
            port=3306,
            database="my_db",
        )
        self.replica_db_url = URL.create(
            drivername="mysql+pymysql",
            username="my_db_user",
            password="S3cret",
            host="127.0.0.1",
            port=3307,
            database="my_db",
        )

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
        print(self.main_db_url)
        with db.session as session:
            r = session.execute(text("SELECT 1;"))
            assert r.scalar() == 1
