from dataclasses import dataclass

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ExampleORMModel(Base):
    __tablename__ = "example_table"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(64))
    last_name: Mapped[str] = mapped_column(String(64))
    age: Mapped[int]


@dataclass()
class ExampleEntity:
    id: int
    first_name: str
    last_name: str
    age: int
