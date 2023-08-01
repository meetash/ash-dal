import typing as t
from abc import ABC

from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase

from ash_dal.database import AsyncDatabase

_M = t.TypeVar("_M", bound=DeclarativeBase)  # ORM Model
_E = t.TypeVar("_E")  # Entity model


class AsyncBaseDAO(ABC, t.Generic[_E]):
    __model__: type[_M]  # pyright: ignore [reportGeneralTypeIssues]
    __entity__: type[_E]
    _db: AsyncDatabase

    @property
    def db(self) -> AsyncDatabase:
        assert hasattr(self, "_db")
        return self._db

    @property
    def __model_columns(self) -> tuple[str, ...]:
        mapper = inspect(self.__model__)
        columns: tuple[str, ...] = tuple(c.key for c in mapper.attrs)
        return columns

    async def get_by_pk(self, pk: t.Any) -> _E | None:
        async with self.db.session as session:
            db_item = await session.get(self.__model__, pk)
            if not db_item:
                return None
            item_dict = {k: getattr(db_item, k) for k in self.__model_columns}
            return self.__entity__(**item_dict)
