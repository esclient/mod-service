from typing import Any

from asyncpg import Pool

from modservice.repository.create_mod import create_mod as _create_mod
from modservice.repository.get_mod_s3_key import (
    get_mod_s3_key as _get_mod_s3_key,
)
from modservice.repository.get_mods import get_mods as _get_mods
from modservice.repository.insert_s3_key import insert_s3_key as _insert_s3_key
from modservice.repository.set_status import set_status as _set_status


class ModRepository:
    def __init__(self, db_pool: Pool):
        self._db_pool = db_pool

    async def create_mod(
        self,
        title: str,
        author_id: int,
        description: str,
    ) -> int:
        return await _create_mod(self._db_pool, title, author_id, description)

    async def insert_s3_key(
        self,
        mod_id: int,
        author_id: int,
    ) -> str:
        return await _insert_s3_key(self._db_pool, mod_id, author_id)

    async def get_mod_s3_key(self, mod_id: int) -> str:
        return str(await _get_mod_s3_key(self._db_pool, mod_id))

    async def set_status(self, mod_id: int, status: str) -> bool:
        return await _set_status(self._db_pool, mod_id, status)

    async def get_mods(
        self,
    ) -> list[dict[str, Any]]:
        return await _get_mods(self._db_pool)
