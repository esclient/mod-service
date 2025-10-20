from asyncpg import Pool


async def create_mod(
    db_pool: Pool,
    title: str,  # noqa: ARG001
    author_id: int,  # noqa: ARG001
    description: str,  # noqa: ARG001
) -> int:
    async with db_pool.acquire() as conn:
        mod_id: int = await conn.fetchval(
            """
            INSERT INTO mods (author_id, title, description, version, status, created_at)
            VALUES ($1, $2, $3, $4, 'UPLOADING', NOW())
            RETURNING id
            """,
            author_id,
            title,
            description,
            1,
        )
        return mod_id
