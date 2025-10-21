from typing import Literal

from asyncpg import Pool


async def get_mod_s3_key(db_pool: Pool, id: int) -> str | Literal[0]:
    async with db_pool.acquire() as conn:
        s3_key = await conn.fetchval(
            """
            SELECT s3_key
            FROM mods
            WHERE id = $1
            AND status = 'UPLOADED';
            """,
            id,
        )
        if s3_key is None:
            return 0
        return str(s3_key)
