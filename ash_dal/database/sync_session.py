from typing import TYPE_CHECKING

from sqlalchemy.orm import Session as SQLAlchemySession, Query
from sqlalchemy import exc as sa_exc, inspect, Table, Select
from sqlalchemy.orm import exc
from sqlalchemy import Engine, Connection, ClauseElement
import typing as t

from sqlalchemy.orm.session import JoinTransactionMode
from sqlalchemy.sql import visitors


class Session(SQLAlchemySession):

    def get_bind(
        self,
        mapper=None,
        *,
        clause: ClauseElement | None = None,
        bind=None,
        _sa_skip_events: bool | None = None,
        _sa_skip_for_implicit_returning: bool = False,
        **kw: t.Any,
    ) -> Engine | Connection:
        try:
            super().get_bind(
                mapper=mapper,
                clause=clause,
                bind=bind,
                _sa_skip_events=_sa_skip_events,
                _sa_skip_for_implicit_returning=_sa_skip_for_implicit_returning,
                **kw,
            )
        except sa_exc.UnboundExecutionError as e:
            # Make decision either suse master or slave instance based on clause
            master_engine = self.info.get('master')
            slave_engine = self.info.get('slave')
            print(master_engine, slave_engine)
            if issubclass(clause.__class__, Select) and slave_engine:
                return slave_engine
            if master_engine:
                return master_engine
            raise e
