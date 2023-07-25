import ssl
import typing as t

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from ash_dal.database.sync_session import Session
from ash_dal.exceptions.database import DBConnectionError


class AsyncDatabase:
    _engine: AsyncEngine
    _ro_engine: AsyncEngine | None
    _session_maker: async_sessionmaker[AsyncSession]

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
    def engine(self) -> AsyncEngine:
        assert getattr(self, "_engine", None)
        return self._engine

    @property
    def read_only_engine(self) -> AsyncEngine:
        assert getattr(self, "_ro_engine", None)
        return self._engine

    @property
    def session_maker(self) -> async_sessionmaker[AsyncSession]:
        assert getattr(self, "_session_maker", None)
        return self._session_maker

    async def connect(self):
        self._engine = self._create_engine(url=self.db_url, ssl_context=self._ssl_context)
        if self.read_replica_url:
            self._ro_engine = self._create_engine(url=self.read_replica_url, ssl_context=self._read_replica_ssl_context)
        self._session_maker = async_sessionmaker(
            expire_on_commit=False,
            sync_session_class=Session,
            info={
                'master': self._engine.sync_engine,
                'slave': self._ro_engine.sync_engine
            }
        )

    async def disconnect(self):
        await self.engine.dispose() if self.engine else ...

    @property
    def session(self) -> AsyncSession:
        return self.session_maker()  # pyright: ignore [ reportOptionalCall ]

    @staticmethod
    def _create_engine(url: URL, ssl_context: ssl.SSLContext | None) -> AsyncEngine:
        connect_args = {"ssl": ssl_context} if ssl_context else {}
        try:
            engine = create_async_engine(
                url,
                connect_args=connect_args,
                pool_pre_ping=True,
            )
            return engine
        except Exception as ex:
            raise DBConnectionError("Can not connect to DB") from ex
