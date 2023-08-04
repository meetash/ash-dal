import typing as t
from dataclasses import dataclass

T = t.TypeVar("T")


@dataclass
class PaginatorPage(t.Generic[T]):
    index: int
    items: tuple[T, ...]

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int):
        return self.items[index]

    def __bool__(self):
        return bool(self.items)
