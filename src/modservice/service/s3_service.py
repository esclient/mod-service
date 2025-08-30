import os
from datetime import datetime

from modservice.s3_client import S3Client


class S3Service:
    def __init__(self, s3_client: S3Client):
        self._s3_client = s3_client

    def generate_s3_key(self, author_id: int, mod_id: int) -> str:
        """
        Generate S3 key in format: author_id/mod_id
        """
        s3_key = f"{author_id}/{mod_id}"
        return s3_key

    def generate_s3_key_with_filename(
        self, author_id: int, filename: str, mod_title: str | None = None
    ) -> str:
        """
        Legacy method - generates keys with timestamp and filename
        Format: {author_id}/{timestamp}_{title/filename}{extension}
        Removed "mods/" prefix to avoid double "mods" in URL
        """
        file_extension = os.path.splitext(filename)[1]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = os.path.splitext(filename)[0]

        # Создаем S3-ключ без префикса "mods/"
        if mod_title:
            # Очищаем название мода от недопустимых символов
            safe_title = "".join(
                c
                for c in mod_title
                if c.isalnum() or c in (" ", "-", "_", ".")
            ).rstrip()
            safe_title = safe_title.replace(" ", "_").replace(".", "_")
            safe_title = "_".join(
                filter(None, safe_title.split("_"))
            )  # Убираем множественные подчеркивания
            s3_key = f"{author_id}/{timestamp}_{safe_title}{file_extension}"
        else:
            s3_key = f"{author_id}/{timestamp}_{base_filename}{file_extension}"

        return s3_key

    def generate_upload_url(
        self,
        author_id: int,
        filename_or_mod_id,  # Can be either filename (str) or mod_id (int)
        mod_title: str | None = None,
        expiration: int = 3600,
        content_type: str | None = None,
    ) -> tuple[str, str]:
        """
        Generate upload URL - supports both new format (author_id/mod_id) and legacy format

        If filename_or_mod_id is int: uses new format (author_id/mod_id)
        If filename_or_mod_id is str: uses legacy format with filename
        """

        # New format: if second parameter is int, treat as mod_id
        if isinstance(filename_or_mod_id, int):
            mod_id = filename_or_mod_id
            s3_key = self.generate_s3_key(author_id, mod_id)

            # Don't pass content_type to avoid signature mismatch
            presigned_url = self._s3_client.generate_presigned_put_url(
                s3_key=s3_key, expiration=expiration
            )

        # Legacy format: if second parameter is string, treat as filename
        else:
            filename = filename_or_mod_id
            s3_key = self.generate_s3_key_with_filename(
                author_id, filename, mod_title
            )

            # Определяем content_type на основе расширения файла, если не указан
            if not content_type:
                file_extension = os.path.splitext(filename)[1].lower()
                content_type_map = {
                    ".zip": "application/zip",
                    ".rar": "application/x-rar-compressed",
                    ".7z": "application/x-7z-compressed",
                    ".tar": "application/x-tar",
                    ".gz": "application/gzip",
                    ".bz2": "application/x-bzip2",
                }
                content_type = content_type_map.get(
                    file_extension, "application/octet-stream"
                )

            # Don't pass content_type to avoid signature mismatch
            presigned_url = self._s3_client.generate_presigned_put_url(
                s3_key=s3_key, expiration=expiration
            )

        return s3_key, presigned_url

    def generate_upload_url_legacy(
        self,
        author_id: int,
        filename: str,
        mod_title: str | None = None,
        expiration: int = 3600,
        content_type: str | None = None,
    ) -> tuple[str, str]:
        """
        Legacy method - generates upload URL with filename and timestamp
        """
        s3_key = self.generate_s3_key_with_filename(
            author_id, filename, mod_title
        )

        # Определяем content_type на основе расширения файла, если не указан
        if not content_type:
            file_extension = os.path.splitext(filename)[1].lower()
            content_type_map = {
                ".zip": "application/zip",
                ".rar": "application/x-rar-compressed",
                ".7z": "application/x-7z-compressed",
                ".tar": "application/x-tar",
                ".gz": "application/gzip",
                ".bz2": "application/x-bzip2",
            }
            content_type = content_type_map.get(
                file_extension, "application/octet-stream"
            )

        presigned_url = self._s3_client.generate_presigned_put_url(
            s3_key=s3_key, expiration=expiration, content_type=content_type
        )

        return s3_key, presigned_url

    def get_file_info_from_s3_key(self, s3_key: str) -> dict:
        """
        Parse S3 key and extract information
        Supports both new format (author_id/mod_id) and legacy format
        """
        try:
            parts = s3_key.split("/")

            # New format: author_id/mod_id
            if len(parts) == 2:
                try:
                    author_id = int(parts[0])
                    mod_id = int(parts[1])
                    return {
                        "author_id": author_id,
                        "mod_id": mod_id,
                        "full_s3_key": s3_key,
                        "format": "new",
                    }
                except ValueError:
                    # If second part is not integer, try legacy format
                    pass

            # Legacy format without "mods/" prefix: author_id/timestamp_filename
            if len(parts) == 2:
                try:
                    author_id = int(parts[0])
                    timestamp_filename = parts[1]

                    if len(timestamp_filename) > 16:
                        # Ищем позицию после timestamp (YYYYMMDD_HHMMSS_)
                        timestamp_end = timestamp_filename.find("_", 15)
                        if timestamp_end > 0:
                            timestamp_part = timestamp_filename[:timestamp_end]
                            filename = timestamp_filename[timestamp_end + 1 :]

                            return {
                                "author_id": author_id,
                                "timestamp": timestamp_part,
                                "filename": filename,
                                "full_s3_key": s3_key,
                                "format": "legacy",
                            }

                    return {
                        "author_id": author_id,
                        "filename": timestamp_filename,
                        "full_s3_key": s3_key,
                        "format": "legacy",
                    }
                except ValueError:
                    pass

            # Old legacy format with "mods/" prefix: mods/author_id/timestamp_filename
            if len(parts) >= 3 and parts[0] == "mods":
                author_id = int(parts[1])

                # Разбираем оставшуюся часть
                remaining_parts = parts[2:]
                if len(remaining_parts) == 1:
                    timestamp_filename = remaining_parts[0]

                    if len(timestamp_filename) > 16:
                        # Ищем позицию после timestamp (YYYYMMDD_HHMMSS_)
                        timestamp_end = timestamp_filename.find("_", 15)
                        if timestamp_end > 0:
                            timestamp_part = timestamp_filename[:timestamp_end]
                            filename = timestamp_filename[timestamp_end + 1 :]

                            return {
                                "author_id": author_id,
                                "timestamp": timestamp_part,
                                "filename": filename,
                                "full_s3_key": s3_key,
                                "format": "old_legacy",
                            }

                return {
                    "author_id": author_id,
                    "filename": "_".join(remaining_parts),
                    "full_s3_key": s3_key,
                    "format": "old_legacy",
                }

        except (ValueError, IndexError):
            pass

        return {"full_s3_key": s3_key, "error": "Не удалось разобрать S3-ключ"}

    def get_download_url(
        self, author_id: int, mod_id: int, expiration: int = 3600
    ) -> str:
        """
        Generate download URL for mod using author_id/mod_id format
        """
        s3_key = self.generate_s3_key(author_id, mod_id)

        return self._s3_client.generate_presigned_get_url(
            s3_key=s3_key, expiration=expiration
        )
