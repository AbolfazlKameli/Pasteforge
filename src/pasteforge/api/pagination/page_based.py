from typing import Annotated

from fastapi import Query
from sqlalchemy import Select, func, select

from dependencies import db_dependency


class PageBasedPaginator:
    def __init__(
        self,
        db: db_dependency,
        page: Annotated[int, Query(ge=1)] = 1,
        per_page: Annotated[int, Query(ge=1, le=100)] = 10,
    ):
        self.db = db
        self.page = page
        self.per_page = per_page
        self.offset = (page - 1) * per_page
        # computed later
        self.number_of_pages = 0
        self.next_page = ""
        self.previous_page = ""

    def _get_next_page(self) -> int | None:
        if self.page >= self.number_of_pages:
            return None
        return self.page + 1

    def _get_previous_page(self) -> int | None:
        if self.page == 1 or self.page > self.number_of_pages + 1:
            return None
        return self.page - 1

    def _get_number_of_pages(self, count: int) -> int:
        rest = count % self.per_page
        quotient = count // self.per_page
        return quotient if not rest else quotient + 1

    async def _get_total_count(self, query: Select) -> int:
        count = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        self.number_of_pages = self._get_number_of_pages(count)
        return count

    async def get_response(self, query: Select) -> dict:
        return {
            "count": await self._get_total_count(query),
            "last_page": self.number_of_pages or None,
            "previous_page": self._get_previous_page(),
            "next_page": self._get_next_page(),
            "items": list(await self.db.scalars(query.limit(self.per_page).offset(self.offset))),
        }
