from typing import Any

from psycopg2.pool import ThreadedConnectionPool


def get_mods(
    db_pool: ThreadedConnectionPool,
) -> list[dict[str, Any]]:
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
            # TODO: Когда добавятся поля в БД, добавить:
            # - avatar_url
            # - download_count
            # - rating
            # - tags
            # - updated_at
            cursor.execute(
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

            results = cursor.fetchall()

            mods = []
            for row in results:
                mod = {
                    "id": row[0],
                    "author_id": row[1],
                    "title": row[2],
                    "description": row[3],
                    "version": row[4],
                    "s3_key": row[5],
                    "status": row[6],
                    "created_at": row[7],
                }
                mods.append(mod)

            return mods
    finally:
        db_pool.putconn(conn)
