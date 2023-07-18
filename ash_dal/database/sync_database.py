import ssl
import typing as t

from sqlalchemy import Engine, create_engine, URL
from sqlalchemy.orm import sessionmaker, Session

from ash_dal.exceptions.database import DBConnectionError


class Database:
    _engine: Engine
    _session_maker: t.Callable[[], Session]

    def __init__(
        self,
        db_url: URL,
        read_replica_url: URL | None = None,
        ssl_context: ssl.SSLContext | None = None,
    ):
        self.db_url = db_url
        self.read_replica_url = read_replica_url
        self._ssl_context = ssl_context

    @property
    def engine(self) -> Engine:
        assert getattr(self, "_engine", None)
        return self._engine

    @property
    def session_maker(self) -> t.Callable[[], Session]:
        assert getattr(self, "_session_maker", None)
        return self._session_maker

    def connect(self):
        self._engine = self._create_engine()
        self._session_maker = sessionmaker(self.engine, expire_on_commit=False)

    def disconnect(self):
        self.engine.dispose() if self.engine else ...

    @property
    def session(self) -> Session:
        return self.session_maker()  # pyright: ignore [ reportOptionalCall ]

    def _create_engine(self) -> Engine:
        connect_args = {"ssl": self._ssl_context} if self._ssl_context else {}
        try:
            engine = create_engine(
                self.db_url,
                connect_args=connect_args,
                pool_pre_ping=True,
            )
            return engine
        except Exception as ex:
            raise DBConnectionError("Can not connect to DB") from ex
