import math
from unittest import TestCase

from ash_dal import BaseDAO, Database
from ash_dal.utils.paginator import PaginatorPage
from faker import Faker

from tests.constants import SYNC_DB_URL
from tests.dao.infrastructure import ExampleEntity, ExampleORMModel


class ExampleDAO(BaseDAO[ExampleEntity]):
    __entity__ = ExampleEntity
    __model__ = ExampleORMModel


class SyncDAOFetchingTestCaseBase(TestCase):
    def setUp(self) -> None:
        self.faker = Faker()
        self.db = Database(db_url=SYNC_DB_URL)
        self.db.connect()
        ExampleORMModel.metadata.drop_all(self.db.engine)
        ExampleORMModel.metadata.create_all(self.db.engine)
        self.dao = ExampleDAO(database=self.db)

    def tearDown(self) -> None:
        self.db.disconnect()

    def _generate_record(
        self, id_: int, first_name: str | None = None, last_name: str | None = None, age: int | None = None
    ):
        return ExampleORMModel(
            id=id_,
            first_name=first_name or self.faker.first_name(),
            last_name=last_name or self.faker.last_name(),
            age=age or self.faker.pyint(min_value=10, max_value=100),
        )


class SyncDAOGetOneRecordTestCase(SyncDAOFetchingTestCaseBase):
    def test_get_by_pk(self):
        expected_entity = ExampleEntity(
            id=self.faker.pyint(min_value=1, max_value=10000),
            first_name=self.faker.first_name(),
            last_name=self.faker.last_name(),
            age=self.faker.pyint(min_value=16, max_value=100),
        )
        db_obj = self._generate_record(
            id_=expected_entity.id,
            first_name=expected_entity.first_name,
            last_name=expected_entity.last_name,
            age=expected_entity.age,
        )
        with self.db.session as session:
            session.add(db_obj)
            session.commit()

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


class SyncDAOFetchAllTestCase(SyncDAOFetchingTestCaseBase):
    def setUp(self) -> None:
        super().setUp()
        self.records_count = self.faker.pyint(min_value=50, max_value=200)
        self._create_records(self.records_count)

    def _create_records(self, count: int):
        records = tuple(self._generate_record(id_=i) for i in range(1, count + 1))
        with self.db.session as session:
            session.bulk_save_objects(objects=records)
            session.commit()

    def test_all(self):
        results = self.dao.all()
        assert results
        assert isinstance(results, tuple)
        assert len(results) == self.records_count
        assert isinstance(results[0], ExampleEntity)

    def test_get_page__default_page_size(self):
        results = self.dao.get_page()
        assert results
        assert isinstance(results, PaginatorPage)
        assert len(results) == self.dao.Config.default_page_size
        assert isinstance(results[0], ExampleEntity)

    def test_get_page__custom_page_size(self):
        page_size = self.faker.pyint(min_value=2, max_value=20)
        results = self.dao.get_page(page_size=page_size)
        assert results
        assert len(results) == page_size

    def test_get_page__defined_page_index(self):
        page_index = self.faker.pyint(min_value=1, max_value=4)
        page_size = 10
        results = self.dao.get_page(page_index=page_index, page_size=page_size)
        assert results
        assert len(results) == page_size

    def test_get_page__page_index_out_of_range(self):
        page_size = 10
        page_index = math.ceil(self.records_count / page_size) + 1
        results = self.dao.get_page(page_index=page_index, page_size=page_size)
        assert not results
        assert isinstance(results, PaginatorPage)

    def test_paginate__default_page_size(self):
        page_size = self.dao.Config.default_page_size
        pages_count = math.ceil(self.records_count / page_size)
        pages_counter = 0
        for page in self.dao.paginate():
            assert isinstance(page, PaginatorPage)
            assert isinstance(page[0], ExampleEntity)
            if page.index + 1 < pages_count:
                assert len(page) == page_size
            else:
                assert len(page) <= page_size
            pages_counter += 1
        assert pages_count == pages_counter

    def test_paginate__custom_page_size(self):
        page_size = self.faker.pyint(min_value=2, max_value=20)
        pages_count = math.ceil(self.records_count / page_size)
        pages_counter = 0
        for page in self.dao.paginate(page_size=page_size):
            assert isinstance(page, PaginatorPage)
            if page.index + 1 < pages_count:
                assert len(page) == page_size
            else:
                assert len(page) <= page_size
            pages_counter += 1
        assert pages_count == pages_counter
