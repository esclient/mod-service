from typing import Any

from psycopg2.pool import ThreadedConnectionPool

from modservice.repository.create_mod import create_mod as _create_mod
from modservice.repository.get_mod_s3_key import (
    get_mod_s3_key as _get_mod_s3_key,
)
from modservice.repository.get_mods import get_mods as _get_mods
from modservice.repository.insert_s3_key import insert_s3_key as _insert_s3_key
from modservice.repository.set_status import set_status as _set_status


class ModRepository:
    def __init__(self, db_pool: ThreadedConnectionPool):
        self._db_pool = db_pool

    def create_mod(
        self,
        mod_title: str,
        author_id: int,
        description: str,
    ) -> int:
        return _create_mod(self._db_pool, mod_title, author_id, description)

    def insert_s3_key(
        self,
        mod_id: int,
        author_id: int,
    ) -> str:
        return _insert_s3_key(self._db_pool, mod_id, author_id)

    def get_mod_s3_key(self, mod_id: int) -> str:
        return str(_get_mod_s3_key(self._db_pool, mod_id))

    def set_status(self, mod_id: int, status: str) -> bool:
        return _set_status(self._db_pool, mod_id, status)

    def get_mods(
        self,
    ) -> list[dict[str, Any]]:
        return _get_mods(self._db_pool)
