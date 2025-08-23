from psycopg2.pool import ThreadedConnectionPool


def create_mod(
    db_pool: ThreadedConnectionPool,
    mod_title: str,
    author_id: int,
    filename: str,
    description: str,
) -> tuple[int, str, str]:
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO mods (mod_title, author_id, filename, description)
                VALUES (%s, %s, %s, %s)
                RETURNING mod_id, upload_url, s3_key
                """,
                (mod_title, author_id, filename, description),
            )
            row = cur.fetchone()
            conn.commit()
            mod_id: int = row[0]
            upload_url: str = row[1]
            s3_key: str = row[2]
            return mod_id, upload_url, s3_key
    finally:
        db_pool.putconn(conn)
