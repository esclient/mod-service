from psycopg2.pool import ThreadedConnectionPool

from modservice.repository.create_mod import create_mod as _create_mod


class ModRepository:
    def __init__(self, db_pool: ThreadedConnectionPool):
        self._db_pool = db_pool

    def create_mod(
        self, mod_title: str, author_id: int, filename: str, description: str, s3_key: str
    ) -> int:
        return _create_mod(
            self._db_pool, mod_title, author_id, filename, description, s3_key
        )
