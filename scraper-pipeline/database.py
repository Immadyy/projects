import asyncpg


CREATE_QUOTES_TABLE = """
CREATE TABLE IF NOT EXISTS quotes (
    id SERIAL PRIMARY KEY,
    quote TEXT NOT NULL UNIQUE,
    author TEXT NOT NULL,
    tags TEXT[] NOT NULL
)
"""


async def create_db_pool(database_url: str) -> asyncpg.Pool:
    pool = await asyncpg.create_pool(database_url)

    async with pool.acquire() as connection:
        await connection.execute(CREATE_QUOTES_TABLE)

    return pool


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
