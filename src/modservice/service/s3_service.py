import os
from datetime import datetime
from typing import Any

from modservice.repository import insert_s3_key
from modservice.s3_client import S3Client


class S3Service:
    def __init__(self, s3_client: S3Client) -> None:
        self._s3_client = s3_client

    def generate_upload_url(
        self,
        s3_key: str,
        expiration: int = 3600,
    ) -> tuple[str, str]:

        presigned_url = self._s3_client.generate_presigned_put_url(
            s3_key=s3_key, expiration=expiration
        )

        return presigned_url

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
