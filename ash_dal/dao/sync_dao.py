import typing as t

from sqlalchemy import delete, insert, select, update

from ash_dal.dao.mixin import BaseDAOMixin
from ash_dal.database import Database
from ash_dal.typing import Entity
from ash_dal.utils import Paginator
from ash_dal.utils.paginator import PaginatorPage
from ash_dal.utils.paginator.interface import PaginatorFactoryProtocol


class BaseDAO(BaseDAOMixin[Entity]):
    __paginator_factory__: PaginatorFactoryProtocol = Paginator

    def __init__(self, database: Database):
        self._db = database

    @property
    def db(self) -> Database:
        """
        Property returns an instance of :class:`Database` class
        :return: DB instance
        """
        assert hasattr(self, "_db")
        return self._db

    def get_by_pk(self, pk: t.Any) -> Entity | None:
        """
        Using this method you can fetch an entity by its primary key
        :param pk: the record's primary key value
        :return: Entity instance or None if the record is not found
        """
        with self.db.session as session:
            db_item = session.get(self.__model__, pk)
            if not db_item:
                return None
            return self._convert_db_item_in_entity(db_item=db_item)

    def all(self) -> tuple[Entity, ...]:
        """
        Using this method you can fetch all entities from the database
        :return: a tuple with entities
        """
        with self.db.session as session:
            db_items = session.scalars(select(self.__model__))
            return self._get_entities_from_db_items(db_items=db_items)

    def get_page(
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
        with self.db.session as session:
            paginator = self.__paginator_factory__(
                session=session, query=select(self.__model__), page_size=page_size or self.__default_page_size__
            )
            page = paginator.get_page(page_index=page_index)
            entities = self._get_entities_from_db_items(db_items=page)
            return PaginatorPage(index=page_index, items=entities)

    def paginate(
        self,
        specification: dict[str, t.Any] | None = None,
        page_size: int | None = None,
    ) -> t.Iterator[PaginatorPage[Entity]]:
        """
        An iterator that returns pages with entities.
        :param specification: Can be used to filter the entities you want to receive.
        :param page_size: Numeric value. Defines size of pages that will be returned
        :return: :class:`t.Iterator` that returns :class:`PaginatorPage` with entities
        """
        with self.db.session as session:
            query = select(self.__model__)
            if specification:
                query = query.filter_by(**specification)
            paginator = self.__paginator_factory__(
                session=session,
                query=query,
                page_size=page_size or self.__default_page_size__,
            )
            for page_index, page in enumerate(paginator.paginate()):
                entities = self._get_entities_from_db_items(db_items=page)
                yield PaginatorPage(index=page_index, items=entities)

    def filter(self, specification: dict[str, t.Any]) -> tuple[Entity, ...]:
        """
        Fetch entities from database by specification.
        :param specification: a dict that will be used for filtering
        :return: a tuple with entities
        """
        with self.db.session as session:
            db_items = session.scalars(select(self.__model__).filter_by(**specification))
            return self._get_entities_from_db_items(db_items=db_items)

    def create(self, data: dict[str, t.Any]) -> Entity:
        """
        Create an entity in database
        :param data: a dict that represents entity to be created.
        :return: a created entity instance
        """
        with self.db.session as session:
            result = session.execute(insert(self.__model__).values(**data))
            session.commit()
            pk_dict: dict[str, t.Any] = result.inserted_primary_key._asdict()  # pyright: ignore
            response_data = {**data, **pk_dict}
            return self._dict_to_entity(dict_=response_data)

    def bulk_create(self, data: t.Sequence[dict[str, t.Any]]):
        """
        Create multiple entities within one query
        :param data: a sequence with dicts that represent entities to be created
        """
        with self.db.session as session:
            session.execute(insert(self.__model__), data)
            session.commit()

    def update(self, specification: dict[str, t.Any], update_data: dict[str, t.Any]) -> bool:
        """
        Patch record(s)
        :param specification: record(s) for updating are chosen based on this specification. If an empy dict is passed,
        a :class:`ValueError` exception will be raised for safety reasons.
        :param update_data: a dict with new values to be written for the chosen record(s)
        :return: a :class:`bool` value that shows either the entity(ies) are updated or not.
        """
        if not specification:
            raise ValueError("Specification should be passed")
        with self.db.session as session:
            result = session.execute(update(self.__model__).filter_by(**specification), update_data)
            session.commit()
            return bool(result.rowcount)  # pyright: ignore

    def delete(self, specification: dict[str, t.Any]) -> bool:
        """
        Remove record(s).
        :param specification: record(s) for removing are chosen based on this specification. If an empy dict is passed,
        a :class:`ValueError` exception will be raised for safety reasons.
        :return: a :class:`bool` value that shows either the entity(ies) are removed or not.
        """
        if not specification:
            raise ValueError("Specification should be passed")
        with self.db.session as session:
            result = session.execute(delete(self.__model__).filter_by(**specification))
            session.commit()
            return bool(result.rowcount)  # pyright: ignore
