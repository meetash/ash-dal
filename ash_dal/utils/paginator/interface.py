import typing as t
from abc import ABC, abstractmethod

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ash_dal.typing import ORMModel
from ash_dal.utils.paginator.paginator_page import PaginatorPage


class IPaginator(ABC, t.Generic[ORMModel]):
    @abstractmethod
    def get_page(self, page_index: int) -> PaginatorPage[ORMModel]:
        ...

    @abstractmethod
    def paginate(self) -> t.Iterator[PaginatorPage[ORMModel]]:
        ...

    @property
    @abstractmethod
    def size(self) -> int:
        ...


class IAsyncPaginator(t.Generic[ORMModel], ABC):
    @abstractmethod
    async def get_page(self, page_index: int) -> PaginatorPage[ORMModel]:
        ...

    @abstractmethod
    def paginate(self) -> t.AsyncIterator[PaginatorPage[ORMModel]]:  # Make pyright happy by removing async keyword :)
        ...

    @property
    @abstractmethod
    async def size(self) -> int:
        ...


class PaginatorFactoryProtocol(t.Protocol):
    def __call__(self, session: Session, query: Select[t.Any], page_size: int) -> IPaginator[t.Any]:
        ...


class AsyncPaginatorFactoryProtocol(t.Protocol):
    def __call__(self, session: AsyncSession, query: Select[t.Any], page_size: int) -> IAsyncPaginator[t.Any]:
        ...
