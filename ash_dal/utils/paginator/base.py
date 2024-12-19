from ash_dal.constants import PAGINATOR_FIRST_PAGE_INDEX


class BasePaginator:
    _page_size: int
    _first_page_index: int = PAGINATOR_FIRST_PAGE_INDEX

    def _calculate_offset(self, page_index: int) -> int:
        assert page_index >= self._first_page_index, f"Page index must be greater or equal to {self._first_page_index}"
        return (page_index - 1) * self._page_size
