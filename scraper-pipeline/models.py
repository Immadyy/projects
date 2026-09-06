from typing import List

from pydantic import AnyHttpUrl, BaseModel, Field


class QuoteItem(BaseModel):
    quote: str
    by: str
    tags: List[str]


class ScrapeRequest(BaseModel):
    target_url: AnyHttpUrl = AnyHttpUrl("https://quotes.toscrape.com/js/")
    pages: int | None = Field(default=None, ge=1, le=100)
    card_selector: str = Field(default=".quote", min_length=1, max_length=200)
    quote_selector: str = Field(default=".text", min_length=1, max_length=200)
    author_selector: str = Field(default=".author", min_length=1, max_length=200)
    tags_selector: str = Field(default=".tag", min_length=1, max_length=200)
