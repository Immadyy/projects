import asyncpg


CREATE_QUOTES_TABLE = """
CREATE TABLE IF NOT EXISTS quotes (
    id SERIAL PRIMARY KEY,
    quote TEXT NOT NULL UNIQUE,
    author TEXT NOT NULL,
    tags TEXT[] NOT NULL
)
"""

CREATE_SCRAPE_JOBS_TABLE = """
CREATE TABLE IF NOT EXISTS scrape_jobs (
    id SERIAL PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    target_url TEXT NOT NULL,
    pages_requested INTEGER NOT NULL,
    pages_completed INTEGER NOT NULL DEFAULT 0,
    items_inserted INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
)
"""


async def create_db_pool(database_url: str) -> asyncpg.Pool:
    pool = await asyncpg.create_pool(database_url)

    async with pool.acquire() as connection:
        await connection.execute(CREATE_QUOTES_TABLE)
        await connection.execute(CREATE_SCRAPE_JOBS_TABLE)

    return pool


async def create_scrape_job(
    pool: asyncpg.Pool,
    target_url: str,
    pages_requested: int,
) -> int:
    async with pool.acquire() as connection:
        return await connection.fetchval(
            """
            INSERT INTO scrape_jobs (status, target_url, pages_requested)
            VALUES ('pending', $1, $2)
            RETURNING id
            """,
            target_url,
            pages_requested,
        )


async def update_scrape_job(
    pool: asyncpg.Pool,
    job_id: int,
    status: str,
    pages_completed: int = 0,
    items_inserted: int = 0,
    error_message: str | None = None,
) -> None:
    async with pool.acquire() as connection:
        await connection.execute(
            """
            UPDATE scrape_jobs
            SET status = $2,
                pages_completed = $3,
                items_inserted = $4,
                error_message = $5,
                started_at = CASE
                    WHEN $2 = 'running' AND started_at IS NULL THEN NOW()
                    ELSE started_at
                END,
                finished_at = CASE
                    WHEN $2 IN ('completed', 'failed') THEN NOW()
                    ELSE finished_at
                END
            WHERE id = $1
            """,
            job_id,
            status,
            pages_completed,
            items_inserted,
            error_message,
        )


async def fetch_scrape_job(pool: asyncpg.Pool, job_id: int) -> dict | None:
    async with pool.acquire() as connection:
        row = await connection.fetchrow(
            """
            SELECT id, status, target_url, pages_requested, pages_completed,
                   items_inserted, error_message, created_at, started_at, finished_at
            FROM scrape_jobs
            WHERE id = $1
            """,
            job_id,
        )

    return dict(row) if row else None


async def fetch_active_scrape_job(pool: asyncpg.Pool) -> int | None:
    async with pool.acquire() as connection:
        return await connection.fetchval(
            """
            SELECT id
            FROM scrape_jobs
            WHERE status IN ('pending', 'running')
            ORDER BY id DESC
            LIMIT 1
            """
        )


async def database_is_ready(pool: asyncpg.Pool) -> bool:
    async with pool.acquire() as connection:
        await connection.execute("SELECT 1")
    return True


async def fetch_quotes(
    pool: asyncpg.Pool,
    limit: int,
    offset: int,
) -> tuple[list[dict], int]:
    async with pool.acquire() as connection:
        total = await connection.fetchval("SELECT COUNT(*) FROM quotes")
        rows = await connection.fetch(
            """
            SELECT id, quote, author, tags
            FROM quotes
            ORDER BY id
            LIMIT $1 OFFSET $2
            """,
            limit,
            offset,
        )

    quotes = [
        {
            "id": row["id"],
            "quote": row["quote"],
            "by": row["author"],
            "tags": row["tags"],
        }
        for row in rows
    ]

    return quotes, total
