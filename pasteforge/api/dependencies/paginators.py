from typing import Annotated

from fastapi import Depends

from pasteforge.api.pagination import PageBasedPaginator

page_based_paginator = Annotated[PageBasedPaginator, Depends(PageBasedPaginator)]
