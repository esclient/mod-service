from psycopg2.pool import ThreadedConnectionPool


def generate_s3_key(author_id: int, mod_id: int) -> str:
    return f"{author_id}/{mod_id}"


def insert_s3_key(
    db_pool: ThreadedConnectionPool,
    mod_id: int,
    author_id: int,
) -> str:
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
            s3_key = generate_s3_key(author_id, mod_id)

            cursor.execute(
                """
                UPDATE mods
                SET s3_key = %s
                WHERE id = %s
                """,
                (
                    s3_key,
                    mod_id,
                ),
            )

            conn.commit()
            return s3_key
    finally:
        db_pool.putconn(conn)
