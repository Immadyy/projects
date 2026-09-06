from typing import List

from pydantic import BaseModel


class QuoteItem(BaseModel):
    quote: str
    by: str
    tags: List[str]
