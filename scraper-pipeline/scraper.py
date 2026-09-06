import asyncpg
from playwright.async_api import async_playwright
from pydantic import ValidationError

from database import update_scrape_job
from models import QuoteItem


async def run_scraper_task(
    db_pool: asyncpg.Pool,
    job_id: int,
    target_url: str,
    page_limit: int,
    card_selector: str,
    quote_selector: str,
    author_selector: str,
    tags_selector: str,
) -> None:
    browser = None
    pages_completed = 0
    items_inserted = 0

    try:
        await update_scrape_job(db_pool, job_id, "running")

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()

            for page_number in range(1, page_limit + 1):
                page_url = f"{target_url.rstrip('/')}/page/{page_number}"
                await page.goto(page_url, wait_until="domcontentloaded")
                await page.wait_for_selector(card_selector)

                quote_cards = page.locator(card_selector)

                async with db_pool.acquire() as connection:
                    for index in range(await quote_cards.count()):
                        quote_card = quote_cards.nth(index)
                        content = {
                            "quote": await quote_card.locator(quote_selector).inner_text(),
                            "by": await quote_card.locator(author_selector).inner_text(),
                            "tags": await quote_card.locator(tags_selector).all_inner_texts(),
                        }

                        try:
                            quote_item = QuoteItem.model_validate(content)
                        except ValidationError as error:
                            print(f"Invalid quote: {error.errors()}")
                            continue

                        inserted_id = await connection.fetchval(
                            """
                            INSERT INTO quotes (quote, author, tags)
                            VALUES ($1, $2, $3)
                            ON CONFLICT (quote) DO NOTHING
                            RETURNING id
                            """,
                            quote_item.quote,
                            quote_item.by,
                            quote_item.tags,
                        )

                        if inserted_id is not None:
                            items_inserted += 1

                pages_completed += 1
                await update_scrape_job(
                    db_pool,
                    job_id,
                    "running",
                    pages_completed,
                    items_inserted,
                )

        await update_scrape_job(
            db_pool,
            job_id,
            "completed",
            pages_completed,
            items_inserted,
        )
        print(f"Scraping completed: {pages_completed} pages")

    except Exception as error:
        error_message = str(error)[:1000]
        await update_scrape_job(
            db_pool,
            job_id,
            "failed",
            pages_completed,
            items_inserted,
            error_message,
        )
        print(f"Scraping failed: {error_message}")
    finally:
        if browser is not None:
            await browser.close()
