import math
import random
from collections import Counter
from unittest import TestCase

import pytest
from ash_dal import BaseDAO, Database, DeferredJoinPaginator, PaginatorPage
from ash_dal.utils import DeferredJoinPaginatorFactory
from faker import Faker
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from tests.constants import SYNC_DB_URL
from tests.dao.infrastructure import ExampleEntity, ExampleORMModel


class ExampleDAO(BaseDAO[ExampleEntity]):
    __entity__ = ExampleEntity
    __model__ = ExampleORMModel
    __default_load_options__ = (joinedload(ExampleORMModel.children),)


class ExampleDAOCustomPaginator(ExampleDAO):
    __paginator_factory__ = DeferredJoinPaginatorFactory[DeferredJoinPaginator](
        paginator_class=DeferredJoinPaginator,
        pk_field=ExampleORMModel.id,
    )


class SyncDAOTestCaseBase(TestCase):
    def setUp(self) -> None:
        self.faker = Faker()
        self.db = Database(db_url=SYNC_DB_URL)
        self.db.connect()
        ExampleORMModel.metadata.drop_all(self.db.engine)
        ExampleORMModel.metadata.create_all(self.db.engine)
        self.dao = ExampleDAO(database=self.db)

    def tearDown(self) -> None:
        self.db.disconnect()


class SyncDAOFetchingTestCaseBase(SyncDAOTestCaseBase):
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
        assert len(results) == self.dao.__default_page_size__
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
        page_size = self.dao.__default_page_size__
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


class SyncDAOFetchFilteredTestCase(SyncDAOFetchingTestCaseBase):
    def setUp(self) -> None:
        super().setUp()
        self.records_count = self.faker.pyint(min_value=50, max_value=200)
        self.records_counter = Counter()
        self._create_records(self.records_count)

    def _create_records(self, count: int):
        records = tuple(self._generate_record(id_=i) for i in range(1, count + 1))
        with self.db.session as session:
            session.bulk_save_objects(objects=records)
            session.commit()

    def _generate_record(
        self, id_: int, first_name: str | None = None, last_name: str | None = None, age: int | None = None
    ):
        record = ExampleORMModel(
            id=id_,
            first_name=first_name or self.faker.first_name(),
            last_name=last_name or self.faker.last_name(),
            age=age or random.choice((20, 30)),
        )
        self.records_counter[str(record.age)] += 1
        return record

    def test_filter(self):
        results_20_age = self.dao.filter(specification={"age": 20})
        results_30_age = self.dao.filter(specification={"age": 30})
        assert len(results_20_age) == self.records_counter["20"]
        assert len(results_30_age) == self.records_counter["30"]

    def test_filter__not_found(self):
        results = self.dao.filter(specification={"age": 40})
        assert not results
        assert isinstance(results, tuple)

    def test_paginate_filtered(self):
        page_size = 3
        pages_count = math.ceil(self.records_counter["30"] / page_size)
        results = self.dao.paginate(specification={"age": 30}, page_size=page_size)
        page_counter = 0
        for page in results:
            assert page
            assert isinstance(page, PaginatorPage)
            if page.index + 1 < pages_count:
                assert len(page) == page_size
            else:
                assert len(page) <= page_size
            assert isinstance(page[0], ExampleEntity)
            page_counter += 1
        assert page_counter == pages_count


class SyncDAOCustomPaginatorUseCase(SyncDAOFetchAllTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.dao = ExampleDAOCustomPaginator(database=self.db)


class SyncDAOCreateTestCase(SyncDAOTestCaseBase):
    def test_create(self):
        data = {
            "first_name": self.faker.first_name(),
            "last_name": self.faker.last_name(),
            "age": self.faker.pyint(min_value=10, max_value=100),
        }
        entity = self.dao.create(data=data)
        assert isinstance(entity, ExampleEntity)
        with self.db.session as session:
            instance = session.get(ExampleORMModel, entity.id)
            assert instance

    def test_bulk_create(self):
        items_count = self.faker.pyint(min_value=2, max_value=10)
        data = tuple(
            {
                "first_name": self.faker.first_name(),
                "last_name": self.faker.last_name(),
                "age": self.faker.pyint(min_value=10, max_value=100),
            }
            for _ in range(items_count)
        )
        self.dao.bulk_create(data=data)
        with self.db.session as session:
            results = session.execute(select(ExampleORMModel)).all()
            assert len(results) == items_count


class SyncDAOUpdateTestCase(SyncDAOTestCaseBase):
    def _create_record(self):
        data = {
            "first_name": self.faker.first_name(),
            "last_name": self.faker.last_name(),
            "age": self.faker.pyint(min_value=10, max_value=100),
        }
        with self.db.session as session:
            db_item = ExampleORMModel(**data)
            session.add(db_item)
            session.commit()
        return {**data, "id": db_item.id}

    def test_update(self):
        created_record = self._create_record()
        update_data = {
            "first_name": self.faker.first_name(),
            "last_name": self.faker.last_name(),
            "age": self.faker.pyint(min_value=10, max_value=100),
        }
        record_id = created_record.get("id")
        is_updated = self.dao.update(specification={"id": record_id}, update_data=update_data)
        assert is_updated
        with self.db.session as session:
            instance = session.get(ExampleORMModel, record_id)
            assert instance
            assert instance.first_name == update_data["first_name"]
            assert instance.last_name == update_data["last_name"]
            assert instance.age == update_data["age"]

    def test_update__empty_specification(self):
        with pytest.raises(ValueError):
            self.dao.update(specification={}, update_data={})


class SyncDAODeleteTestCase(SyncDAOTestCaseBase):
    def _create_record(self):
        data = {
            "first_name": self.faker.first_name(),
            "last_name": self.faker.last_name(),
            "age": self.faker.pyint(min_value=10, max_value=100),
        }
        with self.db.session as session:
            db_item = ExampleORMModel(**data)
            session.add(db_item)
            session.commit()
        return {**data, "id": db_item.id}

    def test_delete(self):
        created_record = self._create_record()
        record_id = created_record.get("id")
        is_deleted = self.dao.delete(specification={"id": record_id})
        assert is_deleted
        with self.db.session as session:
            instance = session.get(ExampleORMModel, record_id)
            assert not instance

    def test_delete__empty_specification(self):
        with pytest.raises(ValueError):
            self.dao.delete(specification={})
