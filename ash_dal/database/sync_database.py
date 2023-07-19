import ssl
import typing as t

from sqlalchemy import URL, Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from ash_dal.exceptions.database import DBConnectionError


class Database:
    _engine: Engine
    _ro_engine: Engine
    _session_maker: t.Callable[[], Session]

    def __init__(
        self,
        db_url: URL,
        ssl_context: ssl.SSLContext | None = None,
        read_replica_url: URL | None = None,
        read_replica_ssl_context: ssl.SSLContext | None = None,
    ):
        self.db_url = db_url
        self.read_replica_url = read_replica_url
        self._ssl_context = ssl_context
        self._read_replica_ssl_context = read_replica_ssl_context

    @property
    def engine(self) -> Engine:
        assert getattr(self, "_engine", None)
        return self._engine

    @property
    def read_only_engine(self) -> Engine:
        assert getattr(self, "_ro_engine", None)
        return self._engine

    @property
    def session_maker(self) -> t.Callable[[], Session]:
        assert getattr(self, "_session_maker", None)
        return self._session_maker

    def connect(self):
        self._engine = self._create_engine(url=self.db_url, ssl_context=self._ssl_context)
        if self.read_replica_url:
            self._ro_engine = self._create_engine(url=self.read_replica_url, ssl_context=self._read_replica_ssl_context)
        # TODO: Implement a custom session class that will route queries between main and read replicas
        self._session_maker = sessionmaker(self.engine, expire_on_commit=False)

    def disconnect(self):
        self.engine.dispose() if self._engine else ...
        self.read_only_engine.dispose() if self._ro_engine else ...

    @property
    def session(self) -> Session:
        return self.session_maker()  # pyright: ignore [ reportOptionalCall ]

    @staticmethod
    def _create_engine(url: URL, ssl_context: ssl.SSLContext | None) -> Engine:
        connect_args = {"ssl": ssl_context} if ssl_context else {}
        try:
            engine = create_engine(
                url,
                connect_args=connect_args,
                pool_pre_ping=True,
            )
            return engine
        except Exception as ex:
            raise DBConnectionError("Can not connect to DB") from ex
