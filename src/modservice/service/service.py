from typing import Any

from modservice.repository.repository import ModRepository
from modservice.service.create_mod import create_mod as _create_mod
from modservice.service.get_mods import get_mods as _get_mods
from modservice.service.s3_service import S3Service
from modservice.service.set_status import set_status as _set_status


class ModService:
    def __init__(self, repo: ModRepository, s3_service: S3Service) -> None:
        self._repo = repo
        self._s3_service = s3_service

    async def create_mod(
        self, title: str, author_id: int, description: str
    ) -> tuple[int, str, str]:
        return await _create_mod(
            self._repo,
            self._s3_service,
            title,
            author_id,
            description,
        )

    async def generate_s3_key(
        self, author_id: int, filename: str, title: str | None = None
    ) -> str:
        return self._s3_service.generate_s3_key(author_id, filename, title)

    async def generate_upload_url(
        self,
        author_id: int,
        filename: str,
        title: str | None = None,
        expiration: int = 3600,
        content_type: str | None = None,
    ) -> tuple[str, str]:
        return await self._s3_service.generate_upload_url(
            author_id, filename, title, expiration, content_type
        )

    async def get_file_info_from_s3_key(self, s3_key: str) -> dict[str, Any]:
        return self._s3_service.get_file_info_from_s3_key(s3_key)

    async def generate_mod_download_url(
        self,
        s3_key_prefix: str,
        expiration: int = 3600,
    ) -> str:
        return await self._s3_service.generate_mod_download_url(
            s3_key_prefix, expiration
        )

    async def generate_mod_upload_url(
        self,
        s3_key_prefix: str,
        expiration: int = 3600,
    ) -> str:
        return await self._s3_service.generate_mod_upload_url(
            s3_key_prefix, expiration
        )

    async def get_mod_download_link(
        self,
        mod_id: int,
        expiration: int = 3600,
    ) -> str:
        s3_key = await self._repo.get_mod_s3_key(mod_id)
        return await self._s3_service.generate_mod_download_url(
            s3_key, expiration
        )

    async def set_status(self, mod_id: int, status: str) -> bool:
        return await _set_status(self._repo, mod_id, status)

    async def get_mods(
        self,
    ) -> list[dict[str, Any]]:
        return await _get_mods(self._repo)
