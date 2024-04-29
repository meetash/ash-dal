import math
from abc import ABC, abstractmethod
from unittest import TestCase

from ash_dal import Database
from ash_dal.utils import Paginator
from ash_dal.utils.paginator.interface import IPaginator
from ash_dal.utils.paginator.sync_paginator import DeferredJoinPaginator
from faker import Faker
from parameterized import parameterized
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from tests.constants import SYNC_DB_URL
from tests.utils.paginator.infrastructure import ExampleORMModel


class SyncPaginatorTestCaseBase(ABC):
    def setUp(self) -> None:
        self.faker = Faker()
        self.records_count = 1000
        self.page_size = 10
        self.db = Database(db_url=SYNC_DB_URL)
        self.db.connect()
        ExampleORMModel.metadata.drop_all(self.db.engine)
        ExampleORMModel.metadata.create_all(self.db.engine)
        self._create_mock_records()

    def tearDown(self) -> None:
        self.db.disconnect()

    def _create_mock_records(self):
        records = tuple(
            ExampleORMModel(
                id=i,
                first_name=self.faker.first_name(),
                last_name=self.faker.last_name(),
                age=self.faker.pyint(min_value=10, max_value=100),
            )
            for i in range(1, self.records_count + 1)
        )
        with self.db.session as session:
            session.bulk_save_objects(objects=records)
            session.commit()

    @abstractmethod
    def _build_paginator(self, query: Select, session: Session) -> IPaginator:
        ...

    def test_paginator__paginate(self):
        expected_pages_count = math.ceil(self.records_count / self.page_size)
        with self.db.session as session:
            paginator = self._build_paginator(
                session=session,
                query=select(ExampleORMModel),
            )
            counter = 0
            for page in paginator.paginate():
                assert page
                assert len(page) == self.page_size
                assert isinstance(page[0], ExampleORMModel)
                assert page.pages_count == expected_pages_count
                counter += 1
            assert counter == expected_pages_count

    def test_paginator__paginate_with_condition(self):
        id_offset = 40
        expected_pages_count = (self.records_count - id_offset) / self.page_size
        with self.db.session as session:
            paginator = self._build_paginator(
                session=session,
                query=select(ExampleORMModel).where(ExampleORMModel.id > id_offset),
            )
            counter = 0
            for page in paginator.paginate():
                assert page
                assert page.pages_count == expected_pages_count
                assert len(page) == self.page_size
                counter += 1
            assert counter == expected_pages_count

    def test_paginator__get_page_by_index(self):
        with self.db.session as session:
            paginator = self._build_paginator(
                session=session,
                query=select(ExampleORMModel),
            )
            page = paginator.get_page(page_index=3)
            assert page
            assert len(page) == self.page_size

    def test_paginator__get_page_by_index__page_has_pages_count(self):
        with self.db.session as session:
            expected_pages_count = math.ceil(self.records_count / self.page_size)
            paginator = self._build_paginator(
                session=session,
                query=select(ExampleORMModel),
            )
            page = paginator.get_page(page_index=3)
            assert page.pages_count == expected_pages_count

    @parameterized.expand((10, 20, 50, 100, 200))
    def test_paginator__size(self, page_size):
        self.page_size = page_size
        with self.db.session as session:
            paginator = self._build_paginator(
                session=session,
                query=select(ExampleORMModel),
            )
            assert paginator.size == math.ceil(self.records_count / self.page_size)


class SyncPaginatorTestCase(SyncPaginatorTestCaseBase, TestCase):
    def _build_paginator(self, query: Select, session: Session) -> IPaginator:
        return Paginator[ExampleORMModel](
            session=session,
            query=query,
            page_size=self.page_size,
        )


class SyncDeferredJoinPaginatorTestCase(SyncPaginatorTestCaseBase, TestCase):
    def _build_paginator(self, query: Select, session: Session) -> IPaginator:
        return DeferredJoinPaginator[ExampleORMModel](
            session=session,
            query=query,
            page_size=self.page_size,
            pk_field=ExampleORMModel.id,
        )
