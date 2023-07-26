import typing as t

from sqlalchemy import inspect

from ash_dal import Database

_M = t.TypeVar("_M")  # ORM Model type
_E = t.TypeVar("_E")  # Entity model


class BaseDAO(t.Generic[_E]):
    __model__: type[_M]
    __entity__: type[_E]
    _db: Database

    @property
    def db(self) -> Database:
        assert getattr(self, "_db", None)
        return self._db

    @property
    def __model_columns(self) -> tuple[str, ...]:
        mapper = inspect(self.__model__)
        columns = tuple(c.key for c in mapper.attrs)
        return columns

    def get_by_pk(self, pk: t.Any) -> _E | None:
        with self.db.session as session:
            db_item = session.get(self.__model__, pk)
            if not db_item:
                return None
            item_dict = {k: getattr(db_item, k) for k in self.__model_columns}
            return self.__entity__(**item_dict)
