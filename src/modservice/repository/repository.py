from psycopg2.pool import ThreadedConnectionPool

from modservice.repository.create_mod import create_mod as _create_mod
from modservice.repository.insert_s3_key import insert_s3_key as _insert_s3_key


class ModRepository:
    def __init__(self, db_pool: ThreadedConnectionPool):
        self._db_pool = db_pool

    def create_mod(
        self,
        mod_title: str,
        author_id: int,
        description: str,
    ) -> int:
        return _create_mod(
            self._db_pool, mod_title, author_id, description
        )
    
    def insert_s3_key(
        self,
        mod_id: int,
        author_id: int,
    ) -> bool:
        return _insert_s3_key(
            self._db_pool, mod_id, author_id
        )
