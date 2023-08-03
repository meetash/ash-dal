import typing as t

from sqlalchemy.orm import DeclarativeBase

ORMModel = t.TypeVar("ORMModel", bound=DeclarativeBase)
Entity = t.TypeVar("Entity")
