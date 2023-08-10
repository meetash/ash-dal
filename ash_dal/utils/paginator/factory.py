import typing as t

from sqlalchemy.sql.roles import ColumnsClauseRole

P = t.TypeVar("P")


class DeferredJoinPaginatorFactory(t.Generic[P]):
    _paginator_class: type[P]

    def __init__(
        self,
        paginator_class: type[P],
        pk_field: ColumnsClauseRole,
    ):
        self._pk_field = pk_field
        self._paginator_class = paginator_class

    def __call__(self, *args: t.Any, **kwargs: t.Any) -> P:
        return self._paginator_class(*args, **kwargs, pk_field=self._pk_field)
