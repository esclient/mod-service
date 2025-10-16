from asyncpg import Pool  # type: ignore[import-untyped]


def generate_s3_key(author_id: int, mod_id: int) -> str:
    return f"{author_id}/{mod_id}"


async def insert_s3_key(db_pool: Pool, mod_id: int, author_id: int) -> str:
    async with db_pool.acquire() as conn:
        s3_key = generate_s3_key(author_id, mod_id)

        await conn.execute(
            """
            UPDATE mods
            SET s3_key = $1
            WHERE id = $2
            """,
            s3_key,
            mod_id,
        )

        return s3_key
