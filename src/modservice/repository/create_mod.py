from psycopg2.pool import ThreadedConnectionPool


def create_mod(
    db_pool: ThreadedConnectionPool,
    mod_title: str,  # noqa: ARG001
    author_id: int,  # noqa: ARG001
    filename: str,  # noqa: ARG001
    description: str,  # noqa: ARG001
) -> tuple[int, str, str]:
    conn = db_pool.getconn()
    try:
        with conn.cursor():
            return 1, "upload_url", "s3_key"
    finally:
        db_pool.putconn(conn)
