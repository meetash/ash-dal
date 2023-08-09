import ssl

from sqlalchemy import URL, Engine, create_engine
from sqlalchemy.orm import sessionmaker

from ash_dal.database.sync_session import Session
from ash_dal.exceptions.database import DBConnectionError


class Database:
    _engine: Engine
    _ro_engine: Engine | None
    _session_maker: sessionmaker[Session]

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
        assert hasattr(self, "_engine")
        return self._engine

    @property
    def read_only_engine(self) -> Engine:
        assert hasattr(self, "_ro_engine")
        return self._engine

    @property
    def session_maker(self) -> sessionmaker[Session]:
        assert hasattr(self, "_session_maker")
        return self._session_maker

    def connect(self):
        """
        Create SQLAlchemy engine(s) and session maker. If read replica information was provided during initialization
        an engine for read replica will be created as well and all fetching queries will be routed to the read replica.
        A typical use case is to run this method once your application is starting.
        """
        self._engine = self._create_engine(url=self.db_url, ssl_context=self._ssl_context)
        slave_engine = None
        if self.read_replica_url:
            self._ro_engine = self._create_engine(url=self.read_replica_url, ssl_context=self._read_replica_ssl_context)
            slave_engine = self._ro_engine
        self._session_maker = sessionmaker(
            class_=Session, expire_on_commit=False, info={"master": self._engine, "slave": slave_engine}
        )

    def disconnect(self):
        """
        Close connections to DB. A typical use case is to run this method before shutting down your application
        """
        self._engine.dispose() if hasattr(self, "_engine") else ...
        self._ro_engine.dispose() if hasattr(self, "_ro_engine") and isinstance(self._ro_engine, Engine) else ...

    @property
    def session(self) -> Session:
        """
        Create a session instance using session maker
        :return: a session instance
        """
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
