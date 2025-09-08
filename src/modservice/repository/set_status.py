from typing import cast

from psycopg2.pool import ThreadedConnectionPool


def set_status(
    db_pool: ThreadedConnectionPool, mod_id: int, status: str
) -> bool:
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE mods
                SET status = %s
                WHERE id = %s
                """,
                [status, mod_id],
            )
            rows_affected: int = cast(int, cursor.rowcount)
            conn.commit()
            return rows_affected > 0
    except Exception:
        conn.rollback()
        return False
    finally:
        db_pool.putconn(conn)
