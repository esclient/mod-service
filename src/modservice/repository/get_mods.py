from typing import Any

from asyncpg import Pool


async def get_mods(
    db_pool: Pool,
) -> list[dict[str, Any]]:
    async with db_pool.acquire() as conn:
        # NOTE: Поля для будущего добавления в БД:
        # - avatar_url
        # - download_count
        # - tags
        # - updated_at
        results = await conn.fetch(
            """
            SELECT
                id,
                author_id,
                title,
                description,
                version,
                s3_key,
                status,
                created_at
            FROM mods
            ORDER BY created_at DESC
            """
        )

        mods = []
        for row in results:
            mod = {
                "id": row["id"],
                "author_id": row["author_id"],
                "title": row["title"],
                "description": row["description"],
                "version": row["version"],
                "s3_key": row["s3_key"],
                "status": row["status"],
                "created_at": row["created_at"],
            }
            mods.append(mod)

        return mods
