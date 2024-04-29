import math
from abc import ABC, abstractmethod
from unittest import IsolatedAsyncioTestCase

from ash_dal import AsyncDatabase
from ash_dal.utils import AsyncDeferredJoinPaginator, AsyncPaginator
from ash_dal.utils.paginator.interface import IAsyncPaginator
from faker import Faker
from parameterized import parameterized
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.constants import ASYNC_DB_URL
from tests.utils.paginator.infrastructure import ExampleORMModel


class AsyncPaginatorTestCaseBase(ABC):
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

    @abstractmethod
    def _build_paginator(self, query: Select, session: AsyncSession) -> IAsyncPaginator:
        ...

    async def test_paginator__paginate(self):
        async with self.db.session as session:
            paginator = self._build_paginator(
                session=session,
                query=select(ExampleORMModel),
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
            paginator = self._build_paginator(
                session=session,
                query=select(ExampleORMModel).where(ExampleORMModel.id > id_offset),
            )
            counter = 0
            async for page in paginator.paginate():
                assert page
                assert len(page) <= self.page_size
                counter += 1
            assert counter == math.ceil((self.records_count - id_offset) / self.page_size)

    async def test_paginator__get_page_by_index(self):
        async with self.db.session as session:
            paginator = self._build_paginator(
                session=session,
                query=select(ExampleORMModel),
            )
            page = await paginator.get_page(page_index=3)
            assert page
            assert len(page) == self.page_size

    async def test_paginator__get_page_by_index__page_has_pages_count(self):
        async with self.db.session as session:
            expected_pages_count = math.ceil(self.records_count / self.page_size)
            paginator = self._build_paginator(
                session=session,
                query=select(ExampleORMModel),
            )
            page = await paginator.get_page(page_index=3)
            assert page.pages_count == expected_pages_count

    @parameterized.expand((10, 20, 50, 100, 200))
    async def test_paginator__size(self, page_size):
        self.page_size = page_size
        async with self.db.session as session:
            paginator = self._build_paginator(
                session=session,
                query=select(ExampleORMModel),
            )
            size = await paginator.size
            assert size == math.ceil(self.records_count / self.page_size)


class AsyncPaginatorTestCase(AsyncPaginatorTestCaseBase, IsolatedAsyncioTestCase):
    def _build_paginator(self, query: Select, session: AsyncSession) -> IAsyncPaginator:
        return AsyncPaginator[ExampleORMModel](
            session=session,
            query=query,
            page_size=self.page_size,
        )


class AsyncDeferredJoinPaginatorTestCase(AsyncPaginatorTestCaseBase, IsolatedAsyncioTestCase):
    def _build_paginator(self, query: Select, session: AsyncSession) -> IAsyncPaginator:
        return AsyncDeferredJoinPaginator[ExampleORMModel](
            session=session,
            query=query,
            page_size=self.page_size,
            pk_field=ExampleORMModel.id,
        )
