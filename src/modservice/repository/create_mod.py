from psycopg2.pool import ThreadedConnectionPool


def create_mod(
    db_pool: ThreadedConnectionPool,
    mod_title: str,  # noqa: ARG001
    author_id: int,  # noqa: ARG001
    filename: str,  # noqa: ARG001
    description: str,  # noqa: ARG001
    s3_key: str,  # noqa: ARG001
) -> tuple[int, str, str]:
    conn = db_pool.getconn()
    try:
        with conn.cursor():
            # Вставка нового мода в базу данных - на будущее для работы с бд
            # надо не забыть поменять тип данных на возврат
            # с tuple[int, str, str] на int, так как будем возвращать success
            # cursor.execute(
            #     """
            #     INSERT INTO mods (mod_title, author_id, filename, description, s3_key)
            #     VALUES (%s, %s, %s, %s, %s)
            #     RETURNING id
            #     """,
            #     (mod_title, author_id, filename, description, s3_key)
            # )
            # result = cursor.fetchone()
            # conn.commit()
            # return result[0] if result else 0
            return 1, "upload_url", "s3_key"
    finally:
        db_pool.putconn(conn)
