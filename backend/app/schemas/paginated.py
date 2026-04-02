from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Paginated[T](BaseModel):
    items: list[T]
    total: int
    skip: int
    limit: int
