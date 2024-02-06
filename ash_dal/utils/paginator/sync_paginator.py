import math
import typing as t

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.roles import ColumnsClauseRole

from ash_dal.typing import ORMModel
from ash_dal.utils.paginator.interface import IPaginator
from ash_dal.utils.paginator.paginator_page import PaginatorPage


class Paginator(IPaginator[ORMModel]):
    def __init__(self, session: Session, query: Select[t.Any], page_size: int):
        self._session = session
        self._page_size = page_size
        self._query = query

    def get_page(self, page_index: int) -> PaginatorPage[ORMModel]:
        offset = page_index * self._page_size
        page_stmt = self._query.offset(offset).limit(self._page_size)
        page: t.Sequence[ORMModel] = self._session.scalars(page_stmt).all()
        return PaginatorPage(index=page_index, items=tuple(page))

    def paginate(self) -> t.Iterator[PaginatorPage[ORMModel]]:
        current_page = 0
        while True:
            page = self.get_page(page_index=current_page)
            if not page:
                break
            yield page
            current_page += 1

    @property
    def size(self) -> int:
        """Returns the count of pages the requested resource has"""
        stmt = select(func.count()).select_from(self._query.subquery())
        items_count: int = self._session.scalar(stmt) or 0
        return math.ceil(items_count / self._page_size)


class DeferredJoinPaginator(Paginator[ORMModel]):
    def __init__(self, session: Session, query: Select[t.Any], page_size: int, pk_field: ColumnsClauseRole):
        super().__init__(session=session, query=query, page_size=page_size)
        self._pk_field = pk_field

    def get_page(self, page_index: int) -> PaginatorPage[ORMModel]:
        offset = page_index * self._page_size
        deferred_join_subquery = (
            self._query.with_only_columns(self._pk_field).offset(offset).limit(self._page_size).subquery()
        )
        stmt = self._query.join(
            target=deferred_join_subquery,
            onclause=self._pk_field == deferred_join_subquery.c[0],  # pyright: ignore [reportArgumentType]
        )
        page: t.Sequence[ORMModel] = self._session.scalars(stmt).all()
        return PaginatorPage(index=page_index, items=tuple(page))
