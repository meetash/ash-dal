import typing as t

from sqlalchemy import ClauseElement, Connection, Engine, Select
from sqlalchemy import exc as sa_exc
from sqlalchemy.orm import Session as SQLAlchemySession


class Session(SQLAlchemySession):
    def get_bind(
        self,
        mapper=None,  # pyright: ignore [reportMissingParameterType]
        *,
        clause: ClauseElement | None = None,
        bind: Engine | Connection | None = None,
        _sa_skip_events: bool | None = None,
        _sa_skip_for_implicit_returning: bool = False,
        **kw: t.Any,
    ) -> Engine | Connection:
        try:
            return super().get_bind(
                mapper=mapper,
                clause=clause,
                bind=bind,
                _sa_skip_events=_sa_skip_events,
                _sa_skip_for_implicit_returning=_sa_skip_for_implicit_returning,
                **kw,
            )
        except sa_exc.UnboundExecutionError as e:
            # Make decision either suse master or slave instance based on clause
            master_engine = self.info.get("master")
            slave_engine = self.info.get("slave")
            if issubclass(clause.__class__, Select) and slave_engine:
                return slave_engine
            if master_engine:
                return master_engine
            raise e
