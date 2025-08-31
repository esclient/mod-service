from typing import Any

from modservice.repository.repository import ModRepository
from modservice.service.create_mod import create_mod as _create_mod
from modservice.service.s3_service import S3Service


class ModService:
    def __init__(self, repo: ModRepository, s3_service: S3Service) -> None:
        self._repo = repo
        self._s3_service = s3_service

    def create_mod(
        self, mod_title: str, author_id: int, filename: str, description: str
    ) -> tuple[int, str, str]:
        return _create_mod(
            self._repo,
            self._s3_service,
            mod_title,
            author_id,
            filename,
            description,
        )

    def generate_s3_key(
        self, author_id: int, filename: str, mod_title: str | None = None
    ) -> str:
        return self._s3_service.generate_s3_key(author_id, filename, mod_title)

    def generate_upload_url(
        self,
        author_id: int,
        filename: str,
        mod_title: str | None = None,
        expiration: int = 3600,
        content_type: str | None = None,
    ) -> tuple[str, str]:
        return self._s3_service.generate_upload_url(
            author_id, filename, mod_title, expiration, content_type
        )

    def get_file_info_from_s3_key(self, s3_key: str) -> dict[str, Any]:
        return self._s3_service.get_file_info_from_s3_key(s3_key)

    def generate_mod_download_url(
        self,
        s3_key_prefix: str,
        expiration: int = 3600,
    ) -> str:
        return self._s3_service.generate_mod_download_url(s3_key_prefix, expiration)

    def generate_mod_upload_url(
        self,
        s3_key_prefix: str,
        expiration: int = 3600,
    ) -> str:
        return self._s3_service.generate_mod_upload_url(
            s3_key_prefix, expiration
        )
