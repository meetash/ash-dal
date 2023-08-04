from unittest import IsolatedAsyncioTestCase

from ash_dal import AsyncBaseDAO, AsyncDatabase
from faker import Faker

from tests.constants import ASYNC_DB_URL
from tests.dao.infrastructure import ExampleEntity, ExampleORMModel


class ExampleAsyncDAO(AsyncBaseDAO[ExampleEntity]):
    __entity__ = ExampleEntity
    __model__ = ExampleORMModel

    def __init__(self, database: AsyncDatabase):
        self._db = database


class AsyncDAOTestCase(IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.faker = Faker()
        self.db = AsyncDatabase(db_url=ASYNC_DB_URL)
        await self.db.connect()
        async with self.db.engine.begin() as conn:
            await conn.run_sync(ExampleORMModel.metadata.drop_all)
            await conn.run_sync(ExampleORMModel.metadata.create_all)
        self.dao = ExampleAsyncDAO(database=self.db)

    async def asyncTearDown(self) -> None:
        await self.db.disconnect()

    async def _create_record(self, id_: int, first_name: str, last_name: str, age: int):
        obj = ExampleORMModel(
            id=id_,
            first_name=first_name,
            last_name=last_name,
            age=age,
        )
        async with self.db.session as session:
            session.add(obj)
            await session.commit()

    async def test_get_by_pk(self):
        expected_entity = ExampleEntity(
            id=self.faker.pyint(min_value=1, max_value=10000),
            first_name=self.faker.first_name(),
            last_name=self.faker.last_name(),
            age=self.faker.pyint(min_value=16, max_value=100),
        )
        await self._create_record(
            id_=expected_entity.id,
            first_name=expected_entity.first_name,
            last_name=expected_entity.last_name,
            age=expected_entity.age,
        )
        result = await self.dao.get_by_pk(expected_entity.id)
        assert result
        assert isinstance(result, ExampleEntity)
        assert result.id == expected_entity.id
        assert result.first_name == expected_entity.first_name
        assert result.last_name == expected_entity.last_name
        assert result.age == expected_entity.age

    async def test_get_by_pk__not_found(self):
        result = await self.dao.get_by_pk(123)
        assert not result
