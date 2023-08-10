import typing as t
from abc import ABC
from functools import cached_property

from sqlalchemy import ScalarResult, inspect

from ash_dal.typing import Entity, ORMModel
from ash_dal.utils.paginator import PaginatorPage

DEFAULT_PAGE_SIZE = 20


class BaseDAOMixin(ABC, t.Generic[Entity]):
    __entity__: type[Entity]
    __model__: type[ORMModel]  # pyright: ignore [reportGeneralTypeIssues]
    __default_page_size__: int = DEFAULT_PAGE_SIZE

    @cached_property
    def _model_columns(self) -> tuple[str, ...]:
        mapper = inspect(self.__model__)
        columns = tuple(c.key for c in mapper.attrs)
        return columns

    def _convert_db_item_in_entity(self, db_item: t.Any) -> Entity:
        item_dict = {k: getattr(db_item, k) for k in self._model_columns}
        return self._dict_to_entity(dict_=item_dict)

    def _get_entities_from_db_items(
        self,
        db_items: t.Sequence[ORMModel] | ScalarResult[ORMModel] | PaginatorPage[ORMModel],
    ) -> tuple[Entity, ...]:
        entities = tuple(self._convert_db_item_in_entity(db_item=db_item) for db_item in db_items)
        return entities

    def _dict_to_entity(
        self,
        dict_: dict[str, t.Any],
    ) -> Entity:
        """
        Method is responsible for converting ORM model data (represented by a dict) to an entity.
        This method exists for cases when you entity schema doesn't match ORM Model schema.
        You can overwrite this method and do all the mappings.
        """
        entity = self.__entity__(**dict_)
        return entity
