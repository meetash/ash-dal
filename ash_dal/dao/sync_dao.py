import typing as t

from sqlalchemy import insert, select

from ash_dal.dao.mixin import DEFAULT_PAGE_SIZE, BaseDAOMixin
from ash_dal.database import Database
from ash_dal.typing import Entity
from ash_dal.utils import Paginator
from ash_dal.utils.paginator import PaginatorPage


class BaseDAO(BaseDAOMixin[Entity]):
    def __init__(self, database: Database):
        self._db = database
        self._config = self.Config()

    class Config:
        paginator_class: type[Paginator[t.Any]] = Paginator
        default_page_size: int = DEFAULT_PAGE_SIZE

    @property
    def db(self) -> Database:
        assert hasattr(self, "_db")
        return self._db

    def get_by_pk(self, pk: t.Any) -> Entity | None:
        with self.db.session as session:
            db_item = session.get(self.__model__, pk)
            if not db_item:
                return None
            return self._convert_db_item_in_entity(db_item=db_item)

    def all(self) -> tuple[Entity, ...]:
        with self.db.session as session:
            db_items = session.scalars(select(self.__model__))
            return self._get_entities_from_db_items(db_items=db_items)

    def get_page(
        self,
        page_index: int = 0,
        page_size: int | None = None,
    ) -> PaginatorPage[Entity]:
        with self.db.session as session:
            paginator = self._config.paginator_class(
                session=session, query=select(self.__model__), page_size=page_size or self._config.default_page_size
            )
            page = paginator.get_page(page_index=page_index)
            entities = self._get_entities_from_db_items(db_items=page)
            return PaginatorPage(index=page_index, items=entities)

    def paginate(
        self,
        specification: dict[str, t.Any] | None = None,
        page_size: int | None = None,
    ) -> t.Iterator[PaginatorPage[Entity]]:
        with self.db.session as session:
            query = select(self.__model__)
            if specification:
                query = query.filter_by(**specification)
            paginator = self._config.paginator_class(
                session=session,
                query=query,
                page_size=page_size or self._config.default_page_size,
            )
            for page_index, page in enumerate(paginator.paginate()):
                entities = self._get_entities_from_db_items(db_items=page)
                yield PaginatorPage(index=page_index, items=entities)

    def filter(self, specification: dict[str, t.Any]) -> tuple[Entity, ...]:
        with self.db.session as session:
            db_items = session.scalars(select(self.__model__).filter_by(**specification))
            return self._get_entities_from_db_items(db_items=db_items)

    def create(self, data: dict[str, t.Any]) -> Entity:
        with self.db.session as session:
            result = session.execute(insert(self.__model__).values(**data))
            session.commit()
            pk_dict: dict[str, t.Any] = result.inserted_primary_key._asdict()  # pyright: ignore
            response_data = {**data, **pk_dict}
            return self._dict_to_entity(dict_=response_data)

    def bulk_create(self, data: t.Sequence[dict[str, t.Any]]):
        with self.db.session as session:
            session.execute(insert(self.__model__), data)
            session.commit()
