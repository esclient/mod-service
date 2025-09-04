from typing import cast

from psycopg2.pool import ThreadedConnectionPool


def confirm_upload(db_pool: ThreadedConnectionPool, mod_id: int) -> bool:
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE mods
                SET status = 'UPLOADED'
                WHERE id = %s AND status = 'UPLOADING'
                """,
                [mod_id],
            )
            rows_affected: int = cast(int, cursor.rowcount)
            conn.commit()
            return rows_affected > 0
    except Exception:
        conn.rollback()
        return False
    finally:
        db_pool.putconn(conn)
