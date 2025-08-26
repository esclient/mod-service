import os
from datetime import datetime
from typing import Any

from modservice.s3_client import S3Client


class S3Service:
    def __init__(self, s3_client: S3Client) -> None:
        self._s3_client = s3_client

    def generate_s3_key(
        self, author_id: int, filename: str, mod_title: str | None = None
    ) -> str:
        file_extension = os.path.splitext(filename)[1]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        base_filename = os.path.splitext(filename)[0]

        # Создаем S3-ключ
        if (
            mod_title
        ):  # Если название имя мода в параметры при генерации s3 ключа
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
            s3_key = (
                f"{author_id}/{timestamp}_{safe_title}{file_extension}"
            )
        else:
            s3_key = (
                f"{author_id}/{timestamp}_{base_filename}{file_extension}"
            )

        return s3_key

    def generate_upload_url(
        self,
        author_id: int,
        filename: str,
        mod_title: str | None = None,
        expiration: int = 3600,
        content_type: str | None = None,
    ) -> tuple[str, str]:
        s3_key = self.generate_s3_key(author_id, filename, mod_title)

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

    def get_file_info_from_s3_key(self, s3_key: str) -> dict[str, Any]:
        try:
            parts = s3_key.split("/")
            if len(parts) >= 2:
                author_id = int(parts[0])

                # Разбираем оставшуюся часть
                remaining_parts = parts[1:]
                if len(remaining_parts) == 1:
                    timestamp_filename = remaining_parts[
                        0
                    ]  # формат timestamp - YYYYMMDD_HHMMSS

                    if (
                        len(timestamp_filename) > 16
                    ):  # Минимальная длина timestamp + underscore + filename
                        # Ищем позицию после timestamp (YYYYMMDD_HHMMSS_)
                        timestamp_end = timestamp_filename.find(
                            "_", 15
                        )  # Ищем _ после timestamp
                        if timestamp_end > 0:
                            timestamp_part = timestamp_filename[:timestamp_end]
                            filename = timestamp_filename[timestamp_end + 1 :]

                            return {
                                "author_id": author_id,
                                "timestamp": timestamp_part,
                                "filename": filename,
                                "full_s3_key": s3_key,
                            }

                return {
                    "author_id": author_id,
                    "filename": "_".join(remaining_parts),
                    "full_s3_key": s3_key,
                }
        except (ValueError, IndexError):
            pass

        return {"full_s3_key": s3_key, "error": "Не удалось разобрать S3-ключ"}
