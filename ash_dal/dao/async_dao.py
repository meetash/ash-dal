import typing as t

from sqlalchemy import select

from ash_dal.dao.mixin import DEFAULT_PAGE_SIZE, BaseDAOMixin
from ash_dal.database import AsyncDatabase
from ash_dal.typing import Entity
from ash_dal.utils import AsyncPaginator


class AsyncBaseDAO(BaseDAOMixin[Entity]):
    def __init__(self, database: AsyncDatabase):
        self._db = database
        self._config = self.Config()

    class Config:
        paginator_class: type[AsyncPaginator[t.Any]] = AsyncPaginator
        default_page_size: int = DEFAULT_PAGE_SIZE

    @property
    def db(self) -> AsyncDatabase:
        assert hasattr(self, "_db")
        return self._db

    async def get_by_pk(self, pk: t.Any) -> Entity | None:
        async with self.db.session as session:
            db_item = await session.get(self.__model__, pk)
            if not db_item:
                return None
            item_dict = {k: getattr(db_item, k) for k in self._model_columns}
            return self.__entity__(**item_dict)

    async def all(self) -> tuple[Entity, ...]:
        async with self.db.session as session:
            db_items = await session.scalars(select(self.__model__))
            return self._get_entities_from_db_items(db_items=db_items)

    async def get_page(
        self,
        page_index: int = 0,
        page_size: int | None = None,
    ) -> tuple[Entity, ...]:
        async with self.db.session as session:
            paginator = self._config.paginator_class(
                session=session, query=select(self.__model__), page_size=page_size or self._config.default_page_size
            )
            page = await paginator.get_page(page_index=page_index)
            return self._get_entities_from_db_items(db_items=page)

    async def paginate(self, page_size: int | None = None) -> t.AsyncIterator[tuple[Entity, ...]]:
        async with self.db.session as session:
            paginator = self._config.paginator_class(
                session=session, query=select(self.__model__), page_size=page_size or self._config.default_page_size
            )
            async for page in paginator.paginate():
                yield self._get_entities_from_db_items(db_items=page)
