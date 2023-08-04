import math
from unittest import IsolatedAsyncioTestCase

from ash_dal import AsyncDatabase
from ash_dal.utils import AsyncDeferredJoinPaginator, AsyncPaginator
from faker import Faker
from sqlalchemy import select

from tests.constants import ASYNC_DB_URL
from tests.utils.paginator.infrastructure import ExampleORMModel


class AsyncPaginatorTestCaseBase(IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.faker = Faker()
        self.records_count = 100
        self.page_size = 10
        self.db = AsyncDatabase(db_url=ASYNC_DB_URL)
        await self.db.connect()
        async with self.db.engine.begin() as conn:
            await conn.run_sync(ExampleORMModel.metadata.drop_all)
            await conn.run_sync(ExampleORMModel.metadata.create_all)
        await self._create_mock_records()

    async def asyncTearDown(self) -> None:
        await self.db.disconnect()

    async def _create_mock_records(self):
        records = tuple(
            ExampleORMModel(
                id=i,
                first_name=self.faker.first_name(),
                last_name=self.faker.last_name(),
                age=self.faker.pyint(min_value=10, max_value=100),
            )
            for i in range(1, self.records_count + 1)
        )
        async with self.db.session as session:
            session.add_all(records)
            await session.commit()


class AsyncPaginatorTestCase(AsyncPaginatorTestCaseBase):
    async def test_paginator__paginate(self):
        async with self.db.session as session:
            paginator = AsyncPaginator[ExampleORMModel](
                session=session,
                query=select(ExampleORMModel),
                page_size=self.page_size,
            )
            counter = 0
            async for page in paginator.paginate():
                assert page
                assert len(page) <= self.page_size
                assert isinstance(page[0], ExampleORMModel)
                counter += 1
            assert counter == math.ceil(self.records_count / self.page_size)

    async def test_paginator__paginate_with_condition(self):
        id_offset = 55
        async with self.db.session as session:
            paginator = AsyncPaginator[ExampleORMModel](
                session=session,
                query=select(ExampleORMModel).where(ExampleORMModel.id > id_offset),
                page_size=self.page_size,
            )
            counter = 0
            async for page in paginator.paginate():
                assert page
                assert len(page) <= self.page_size
                counter += 1
            assert counter == math.ceil((self.records_count - id_offset) / self.page_size)

    async def test_paginator__get_page_by_index(self):
        async with self.db.session as session:
            paginator = AsyncPaginator[ExampleORMModel](
                session=session,
                query=select(ExampleORMModel),
                page_size=self.page_size,
            )
            page = await paginator.get_page(page_index=3)
            assert page
            assert len(page) == self.page_size

    async def test_paginator__size(self):
        async with self.db.session as session:
            paginator = AsyncPaginator[ExampleORMModel](
                session=session,
                query=select(ExampleORMModel),
                page_size=self.page_size,
            )
            size = await paginator.size
            assert size == math.ceil(self.records_count / self.page_size)


class AsyncDeferredJoinPaginatorTestCase(AsyncPaginatorTestCaseBase):
    async def test_paginator__paginate(self):
        async with self.db.session as session:
            paginator = AsyncDeferredJoinPaginator[ExampleORMModel](
                session=session,
                query=select(ExampleORMModel),
                page_size=self.page_size,
                pk_field=ExampleORMModel.id,
            )
            counter = 0
            async for page in paginator.paginate():
                assert page
                assert len(page) <= self.page_size
                assert isinstance(page[0], ExampleORMModel)
                counter += 1
            assert counter == math.ceil(self.records_count / self.page_size)

    async def test_paginator__paginate_with_condition(self):
        id_offset = 55
        async with self.db.session as session:
            paginator = AsyncDeferredJoinPaginator[ExampleORMModel](
                session=session,
                query=select(ExampleORMModel).where(ExampleORMModel.id > id_offset),
                page_size=self.page_size,
                pk_field=ExampleORMModel.id,
            )
            counter = 0
            async for page in paginator.paginate():
                assert page
                assert len(page) <= self.page_size
                counter += 1
            assert counter == math.ceil((self.records_count - id_offset) / self.page_size)

    async def test_paginator__get_page_by_index(self):
        async with self.db.session as session:
            paginator = AsyncDeferredJoinPaginator[ExampleORMModel](
                session=session,
                query=select(ExampleORMModel),
                page_size=self.page_size,
                pk_field=ExampleORMModel.id,
            )
            page = await paginator.get_page(page_index=3)
            assert page
            assert len(page) == self.page_size
