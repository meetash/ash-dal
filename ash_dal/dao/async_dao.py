import typing as t

from sqlalchemy import delete, insert, select, update

from ash_dal.dao.mixin import BaseDAOMixin
from ash_dal.database import AsyncDatabase
from ash_dal.typing import Entity
from ash_dal.utils import AsyncPaginator
from ash_dal.utils.paginator import PaginatorPage
from ash_dal.utils.paginator.interface import AsyncPaginatorFactoryProtocol


class AsyncBaseDAO(BaseDAOMixin[Entity]):
    __paginator_factory__: AsyncPaginatorFactoryProtocol = AsyncPaginator

    def __init__(self, database: AsyncDatabase):
        self._db = database

    @property
    def db(self) -> AsyncDatabase:
        """
        Property returns an instance of :class:`AsyncDatabase` class
        :return: DB instance
        """
        assert hasattr(self, "_db")
        return self._db

    async def get_by_pk(self, pk: t.Any) -> Entity | None:
        """
        Using this method you can fetch an entity by its primary key
        :param pk: the record's primary key value
        :return: Entity instance or None if the record is not found
        """
        async with self.db.session as session:
            db_item = await session.get(self.__model__, pk)
            if not db_item:
                return None
            item_dict = {k: getattr(db_item, k) for k in self._model_columns}
            return self.__entity__(**item_dict)

    async def all(self) -> tuple[Entity, ...]:
        """
        Using this method you can fetch all entities from the database
        :return: a tuple with entities
        """
        async with self.db.session as session:
            db_items = await session.scalars(select(self.__model__))
            return self._get_entities_from_db_items(db_items=db_items)

    async def get_page(
        self,
        page_index: int = 0,
        page_size: int | None = None,
    ) -> PaginatorPage[Entity]:
        """
        Fetch a page with entities by page index. If the index is out of range, an empty page will be returned.
        :param page_index: Numeric value. Index starts from 0
        :param page_size: Numeric value. Defines size of the page that will be returned
        :return: An instance of :class:`PaginatorPage` that includes entities.
        """
        async with self.db.session as session:
            paginator = self.__paginator_factory__(
                session=session, query=select(self.__model__), page_size=page_size or self.__default_page_size__
            )
            page = await paginator.get_page(page_index=page_index)
            entities = self._get_entities_from_db_items(db_items=page)
            return PaginatorPage(index=page_index, items=entities)

    async def paginate(
        self,
        specification: dict[str, t.Any] | None = None,
        page_size: int | None = None,
    ) -> t.AsyncIterator[PaginatorPage[Entity]]:
        """
        An iterator that returns pages with entities.
        :param specification: Can be used to filter the entities you want to receive.
        :param page_size: Numeric value. Defines size of pages that will be returned
        :return: :class:`t.Iterator` that returns :class:`PaginatorPage` with entities
        """
        async with self.db.session as session:
            query = select(self.__model__)
            if specification:
                query = query.filter_by(**specification)
            paginator = self.__paginator_factory__(
                session=session,
                query=query,
                page_size=page_size or self.__default_page_size__,
            )
            async for page in paginator.paginate():
                entities = self._get_entities_from_db_items(db_items=page)
                yield PaginatorPage(index=page.index, items=entities)

    async def filter(self, specification: dict[str, t.Any]) -> tuple[Entity, ...]:
        """
        Fetches entities from database by specification.
        :param specification: a dict that will be used for filtering
        :return: a tuple with entities
        """
        async with self.db.session as session:
            db_items = await session.scalars(select(self.__model__).filter_by(**specification))
            return self._get_entities_from_db_items(db_items=db_items)

    async def create(self, data: dict[str, t.Any]) -> Entity:
        """
        Creates an entity in database
        :param data: a dict that represents entity to be created.
        :return: a created entity instance
        """
        async with self.db.session as session:
            result = await session.execute(insert(self.__model__).values(**data))
            await session.commit()
            pk_dict: dict[str, t.Any] = result.inserted_primary_key._asdict()  # pyright: ignore
            response_data = {**data, **pk_dict}
            return self._dict_to_entity(dict_=response_data)

    async def bulk_create(self, data: t.Sequence[dict[str, t.Any]]):
        """
        Create multiple records by one request
        :param data: a sequence with dicts that represent entities to be created
        """
        async with self.db.session as session:
            await session.execute(insert(self.__model__), data)
            await session.commit()

    async def update(self, specification: dict[str, t.Any], update_data: dict[str, t.Any]) -> bool:
        """
        Patches record(s)
        :param specification: record(s) for updating are chosen based on this specification. If an empy dict is passed,
        a :class:`ValueError` exception will be raised for safety reasons.
        :param update_data: a dict with new values to be written for the chosen record(s)
        :return: a :class:`bool` value that shows either the entity(ies) are updated or not.
        """
        if not specification:
            raise ValueError("Specification should be passed")
        async with self.db.session as session:
            result = await session.execute(update(self.__model__).filter_by(**specification), update_data)
            await session.commit()
            return bool(result.rowcount)  # pyright: ignore

    async def delete(self, specification: dict[str, t.Any]) -> bool:
        """
        Removes record(s).
        :param specification: record(s) for removing are chosen based on this specification. If an empy dict is passed,
        a :class:`ValueError` exception will be raised for safety reasons.
        :return: a :class:`bool` value that shows either the entity(ies) are removed or not.
        """
        if not specification:
            raise ValueError("Specification should be passed")
        async with self.db.session as session:
            result = await session.execute(delete(self.__model__).filter_by(**specification))
            await session.commit()
            return bool(result.rowcount)  # pyright: ignore
