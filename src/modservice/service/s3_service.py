import logging
import mimetypes
import os
from datetime import datetime
from typing import Any

from modservice.s3_client import S3Client

logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self, s3_client: S3Client) -> None:
        self._s3_client = s3_client

    def generate_s3_key(
        self, author_id: int, filename: str, title: str | None = None
    ) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        safe_filename = self._sanitize_filename(filename)

        if title:
            safe_title = self._sanitize_title(title)
            file_ext = os.path.splitext(safe_filename)[1]
            safe_filename = safe_title + file_ext

        s3_key = f"{author_id}/{timestamp}_{safe_filename}"
        logger.info(f"Сгенерирован S3 ключ: {s3_key}")

        return s3_key

    def _sanitize_filename(self, filename: str) -> str:
        invalid_chars = ["<", ">", ":", '"', "|", "?", "*", "\\", "/"]
        safe_filename = filename
        for char in invalid_chars:
            safe_filename = safe_filename.replace(char, "_")
        return safe_filename

    def _sanitize_title(self, title: str) -> str:
        safe_title = title.replace(" ", "_")
        safe_title = "".join(
            c for c in safe_title if c.isalnum() or c in ["_", "-", "."]
        )
        safe_title = safe_title.rstrip("_")
        return safe_title

    def _detect_content_type(self, filename: str) -> str | None:
        content_type, _ = mimetypes.guess_type(filename)
        return content_type

    def generate_mod_upload_url(
        self,
        s3_key_prefix: str,
        expiration: int = 3600,
    ) -> str:
        full_s3_key = f"{s3_key_prefix}/mod.zip"

        content_type = "application/zip"

        presigned_url = self._s3_client.generate_presigned_put_url(
            s3_key=full_s3_key,
            expiration=expiration,
            content_type=content_type,
        )

        logger.info(f"Presigned PUT URL MOD сгенерирован для {full_s3_key}")
        return presigned_url

    def generate_mod_download_url(
        self,
        s3_key_prefix: str,
        expiration: int = 3600,
    ) -> str:
        full_s3_key = f"{s3_key_prefix}/mod.zip"

        presigned_url = self._s3_client.generate_presigned_get_url(
            s3_key=full_s3_key, expiration=expiration
        )

        logger.info(f"Presigned GET URL MOD сгенерирован для {full_s3_key}")
        return presigned_url

    def generate_upload_url(
        self,
        author_id: int,
        filename: str,
        title: str | None = None,
        expiration: int = 3600,
        content_type: str | None = None,
    ) -> tuple[str, str]:
        logger.info(
            f"Генерируем Presigned PUT URL для автора {author_id}, файл: {filename}"
        )

        s3_key = self.generate_s3_key(author_id, filename, title)

        if content_type is None:
            content_type = self._detect_content_type(filename)

        presigned_url = self._s3_client.generate_presigned_put_url(
            s3_key=s3_key, expiration=expiration, content_type=content_type
        )

        logger.info(f"Presigned PUT URL успешно сгенерирован для {s3_key}")
        return s3_key, presigned_url

    def generate_upload_url_for_key(
        self,
        s3_key: str,
        expiration: int = 3600,
        content_type: str | None = None,
    ) -> str:
        logger.info(
            f"Генерируем Presigned PUT URL для существующего s3_key: {s3_key}"
        )

        presigned_url = self._s3_client.generate_presigned_put_url(
            s3_key=s3_key, expiration=expiration, content_type=content_type
        )

        logger.info(f"Presigned PUT URL успешно сгенерирован для {s3_key}")
        return presigned_url

    def generate_download_url(
        self,
        s3_key: str,
        expiration: int = 3600,
    ) -> str:
        logger.info(f"Генерируем Presigned GET URL для s3_key: {s3_key}")

        presigned_url = self._s3_client.generate_presigned_get_url(
            s3_key=s3_key, expiration=expiration
        )

        logger.info(f"Presigned GET URL успешно сгенерирован для {s3_key}")
        return presigned_url

    def upload_file(
        self,
        file_path: str,
        s3_key: str,
    ) -> bool:
        logger.info(f"Загружаем файл {file_path} с ключом {s3_key}")

        success = self._s3_client.upload_file(file_path, s3_key)

        if success:
            logger.info(f"Файл успешно загружен: {s3_key}")
        else:
            logger.error(f"Ошибка загрузки файла: {s3_key}")

        return success

    def download_file(
        self,
        s3_key: str,
        local_path: str,
    ) -> bool:
        logger.info(f"Скачиваем файл {s3_key} в {local_path}")

        success = self._s3_client.download_file(s3_key, local_path)

        if success:
            logger.info(f"Файл успешно скачан: {local_path}")
        else:
            logger.error(f"Ошибка скачивания файла: {s3_key}")

        return success

    def list_files(self, prefix: str = "") -> list[dict[str, Any]]:
        logger.info(f"Получаем список файлов с префиксом: '{prefix}'")

        files = self._s3_client.list_objects(prefix)

        logger.info(f"Найдено {len(files)} файлов")
        return files

    def get_file_info_from_s3_key(self, s3_key: str) -> dict[str, Any]:
        try:
            parts = s3_key.split("/")
            if len(parts) >= 2:
                author_id = int(parts[0])

                remaining_parts = parts[1:]
                if len(remaining_parts) == 1:
                    mod_part = remaining_parts[0]

                    try:
                        mod_id = int(mod_part)
                        return {
                            "author_id": author_id,
                            "mod_id": mod_id,
                            "full_s3_key": s3_key,
                        }
                    except ValueError:
                        timestamp_filename = mod_part

                        if len(timestamp_filename) > 16:
                            timestamp_end = timestamp_filename.find("_", 15)
                            if timestamp_end > 0:
                                timestamp_part = timestamp_filename[
                                    :timestamp_end
                                ]
                                filename = timestamp_filename[
                                    timestamp_end + 1 :
                                ]

                                return {
                                    "author_id": author_id,
                                    "timestamp": timestamp_part,
                                    "filename": filename,
                                    "full_s3_key": s3_key,
                                }

                return {
                    "author_id": author_id,
                    "filename": "/".join(remaining_parts),
                    "full_s3_key": s3_key,
                }

        except (ValueError, IndexError) as e:
            logger.error(f"Ошибка парсинга S3 ключа '{s3_key}': {e}")

        return {"full_s3_key": s3_key, "error": "Не удалось разобрать S3-ключ"}
