from psycopg2.pool import ThreadedConnectionPool


def create_mod(
    db_pool: ThreadedConnectionPool,
    mod_title: str,
    author_id: int,
    filename: str,
    description: str,
) -> int:
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO mods (mod_title, author_id, filename, description)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (mod_title, author_id, filename, description),
            )
            row = cur.fetchone()
            conn.commit()
            mod_id: int = row[0]
            upload_url: int = row[0]
            s3_key: int = row[0]
            return mod_id, upload_url, s3_key
    finally:
        db_pool.putconn(conn)
