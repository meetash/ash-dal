import math
import typing as t

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.roles import ColumnsClauseRole

from ash_dal.typing import ORMModel
from ash_dal.utils.paginator.base import BasePaginator
from ash_dal.utils.paginator.interface import IAsyncPaginator
from ash_dal.utils.paginator.paginator_page import PaginatorPage


class AsyncPaginator(IAsyncPaginator[ORMModel], BasePaginator):
    _size: int | None = None

    def __init__(self, session: AsyncSession, query: Select[t.Any], page_size: int):
        self._session = session
        self._page_size = page_size
        self._query = query

    async def get_page(self, page_index: int) -> PaginatorPage[ORMModel]:
        offset = self._calculate_offset(page_index)
        page_stmt = self._query.offset(offset).limit(self._page_size)
        result = await self._session.scalars(page_stmt)
        page: t.Sequence[ORMModel] = result.unique().all()
        return PaginatorPage(index=page_index, items=tuple(page), pages_count=await self.size)

    async def paginate(self) -> t.AsyncIterator[PaginatorPage[ORMModel]]:
        current_page = self._first_page_index
        while True:
            page = await self.get_page(page_index=current_page)
            if not page:
                break
            yield page
            current_page += 1

    @property
    async def size(self) -> int:
        """Returns the count of pages the requested resource has"""
        if self._size is None:
            stmt = select(func.count()).select_from(self._query.subquery())
            items_count: int = await self._session.scalar(stmt) or 0
            self._size = math.ceil(items_count / self._page_size)
        return self._size


class AsyncDeferredJoinPaginator(AsyncPaginator[ORMModel]):
    def __init__(self, session: AsyncSession, query: Select[t.Any], page_size: int, pk_field: ColumnsClauseRole):
        super().__init__(session=session, query=query, page_size=page_size)
        self._pk_field = pk_field

    async def get_page(self, page_index: int) -> PaginatorPage[ORMModel]:
        offset = self._calculate_offset(page_index)
        deferred_join_subquery = (
            self._query.with_only_columns(self._pk_field).offset(offset).limit(self._page_size).subquery()
        )
        stmt = self._query.join(
            target=deferred_join_subquery,
            onclause=self._pk_field == deferred_join_subquery.c[0],  # pyright: ignore [reportArgumentType]
        )
        result = await self._session.scalars(stmt)
        page: t.Sequence[ORMModel] = result.unique().all()
        return PaginatorPage(index=page_index, items=tuple(page), pages_count=await self.size)
