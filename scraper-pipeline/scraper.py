import asyncpg
from playwright.async_api import async_playwright
from pydantic import ValidationError

from models import QuoteItem


async def run_scraper_task(db_pool: asyncpg.Pool, page_limit: int) -> None:
    browser = None

    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()

            async with db_pool.acquire() as connection:
                for page_number in range(1, page_limit + 1):
                    await page.goto(
                        f"https://quotes.toscrape.com/js/page/{page_number}"
                    )
                    await page.wait_for_selector(".quote")

                    quote_cards = page.locator(".quote")

                    for index in range(await quote_cards.count()):
                        quote_card = quote_cards.nth(index)
                        content = {
                            "quote": await quote_card.locator(".text").inner_text(),
                            "by": await quote_card.locator(".author").inner_text(),
                            "tags": await quote_card.locator(".tag").all_inner_texts(),
                        }

                        try:
                            quote_item = QuoteItem.model_validate(content)
                        except ValidationError as error:
                            print(f"Invalid quote: {error.errors()}")
                            continue

                        await connection.execute(
                            """
                            INSERT INTO quotes (quote, author, tags)
                            VALUES ($1, $2, $3)
                            ON CONFLICT (quote) DO NOTHING
                            """,
                            quote_item.quote,
                            quote_item.by,
                            quote_item.tags,
                        )

            print(f"Scraping completed: {page_limit} pages")

    except Exception as error:
        print(f"Scraping failed: {error}")
    finally:
        if browser is not None:
            await browser.close()
