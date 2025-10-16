from asyncpg import Pool  # type: ignore[import-untyped]


async def get_mod_s3_key(db_pool: Pool, id: int) -> int:
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
        return s3_key if s3_key else 0
