from psycopg2.pool import ThreadedConnectionPool


def generate_s3_key(author_id: int, mod_id: int) -> str:
    """Генерирует s3_key в формате author_id/mod_id/"""
    return f"{author_id}/{mod_id}"


def insert_s3_key(
    db_pool: ThreadedConnectionPool,
    mod_id: int,
    author_id: int,
) -> str:  # Возвращаем успех операции
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
            # Генерируем s3_key в формате author_id/mod_id/
            s3_key = generate_s3_key(author_id, mod_id)
            
            # Обновляем мод с s3_key
            cursor.execute(
                """
                UPDATE mods 
                SET s3_key = %s
                WHERE id = %s
                """,
                (
                    s3_key,
                    mod_id,
                )
            )
            
            # Проверяем, что запись была обновлена
            conn.commit()
            return s3_key
    finally:
        db_pool.putconn(conn)
