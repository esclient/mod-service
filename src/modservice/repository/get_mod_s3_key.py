from psycopg2.pool import ThreadedConnectionPool


def get_mod_s3_key(db_pool: ThreadedConnectionPool, id: int) -> int:
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT s3_key
                FROM mods
                WHERE id = %s
                AND status = 'UPLOADED';
                """,
                [id],
            )
            result = cursor.fetchone()
            return result[0] if result else 0
    finally:
        db_pool.putconn(conn)
