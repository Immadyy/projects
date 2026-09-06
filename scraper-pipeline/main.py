from contextlib import asynccontextmanager
from fastapi import BackgroundTasks, FastAPI, Query
import uvicorn

from config import DATABASE_URL, HOST, PORT, SCRAPE_PAGES
from database import create_db_pool, fetch_quotes
from scraper import run_scraper_task

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_pool = await create_db_pool(DATABASE_URL)
    yield
    await app.state.db_pool.close()

app = FastAPI(lifespan=lifespan)


@app.get("/api/quotes")
async def get_quotes(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    quotes, total = await fetch_quotes(app.state.db_pool, limit, offset)

    return {
        "data": quotes,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(quotes) < total,
        "next_offset": offset + limit if offset + len(quotes) < total else None,
    }


@app.post("/api/scrape/quotes", status_code=202)
async def trigger_scrape(background_tasks: BackgroundTasks):
    background_tasks.add_task(
        run_scraper_task,
        app.state.db_pool,
        SCRAPE_PAGES,
    )

    return {
        "status": "processing",
        "message": "Scraper initialized in the background.",
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=False,
    )