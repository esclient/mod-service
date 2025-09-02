from psycopg2.pool import ThreadedConnectionPool


def create_mod(
    db_pool: ThreadedConnectionPool,
    mod_title: str,  # noqa: ARG001
    author_id: int,  # noqa: ARG001
    description: str,  # noqa: ARG001
) -> int:  # Возвращаем только id нового мода
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
            # Вставка нового мода в базу данных
            cursor.execute(
                """
                INSERT INTO mods (author_id, title, description, version, status, created_at)
                VALUES (%s, %s, %s, %s, 'UPLOADING', NOW())
                RETURNING id
                """,
                (
                    author_id,
                    mod_title,
                    description,
                    1,
                ),  # Указываем версию как 1
            )
            result = cursor.fetchone()
            conn.commit()
            return result[0] if result else 0  # Возвращаем id нового мода
    finally:
        db_pool.putconn(conn)
