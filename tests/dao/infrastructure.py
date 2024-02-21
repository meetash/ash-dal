from dataclasses import dataclass, field

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ExampleORMModel(Base):
    __tablename__ = "example_table"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(64))
    last_name: Mapped[str] = mapped_column(String(64))
    age: Mapped[int]
    children: Mapped[list["ExampleORMModelChild"]] = relationship(cascade="all, delete-orphan", lazy="noload")


class ExampleORMModelChild(Base):
    __tablename__ = "example_child_table"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    parent_id: Mapped[int] = mapped_column(ForeignKey("example_table.id"), nullable=False)


@dataclass
class ExampleChildEntity:
    id: int
    name: str


@dataclass()
class ExampleEntity:
    id: int
    first_name: str
    last_name: str
    age: int
    children: list[ExampleChildEntity] = field(default_factory=list)
