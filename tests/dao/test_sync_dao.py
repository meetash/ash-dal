from unittest import TestCase

from ash_dal import BaseDAO, Database
from faker import Faker

from tests.constants import SYNC_DB_URL
from tests.dao.infrastructure import ExampleEntity, ExampleORMModel


class ExampleDAO(BaseDAO[ExampleEntity]):
    __entity__ = ExampleEntity
    __model__ = ExampleORMModel

    def __init__(self, database: Database):
        self._db = database


class SyncDAOTestCase(TestCase):
    def setUp(self) -> None:
        self.faker = Faker()
        self.db = Database(db_url=SYNC_DB_URL)
        self.db.connect()
        ExampleORMModel.metadata.drop_all(self.db.engine)
        ExampleORMModel.metadata.create_all(self.db.engine)
        self.dao = ExampleDAO(database=self.db)

    def tearDown(self) -> None:
        self.db.disconnect()

    def _create_record(self, id_: int, first_name: str, last_name: str, age: int):
        obj = ExampleORMModel(
            id=id_,
            first_name=first_name,
            last_name=last_name,
            age=age,
        )
        with self.db.session as session:
            session.add(obj)
            session.commit()

    def test_get_by_pk(self):
        expected_entity = ExampleEntity(
            id=self.faker.pyint(min_value=1, max_value=10000),
            first_name=self.faker.first_name(),
            last_name=self.faker.last_name(),
            age=self.faker.pyint(min_value=16, max_value=100),
        )
        self._create_record(
            id_=expected_entity.id,
            first_name=expected_entity.first_name,
            last_name=expected_entity.last_name,
            age=expected_entity.age,
        )
        result = self.dao.get_by_pk(expected_entity.id)
        assert result
        assert isinstance(result, ExampleEntity)
        assert result.id == expected_entity.id
        assert result.first_name == expected_entity.first_name
        assert result.last_name == expected_entity.last_name
        assert result.age == expected_entity.age

    def test_get_by_pk__not_found(self):
        result = self.dao.get_by_pk(123)
        assert not result
