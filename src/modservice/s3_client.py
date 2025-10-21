import logging
from typing import Any

import aioboto3
import aiofiles
from aiobotocore.config import AioConfig

logger = logging.getLogger(__name__)


class S3Client:
    def __init__(
        self,
        access_key: str,
        secret_key: str,
        endpoint_url: str,
        bucket_name: str,
        verify: bool,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.ssl_verify = verify

        self.config = AioConfig(
            signature_version="s3v4",
            s3={"addressing_style": "virtual"},
            region_name="ru-central-1",
        )

        self.session = aioboto3.Session()

        logger.info(f"Инициализирован S3Client для бакета: {self.bucket_name}")
        logger.info(f"Endpoint: {self.endpoint_url}")
        logger.info(f"SSL Verify: {self.ssl_verify}")
        logger.info("Addressing style: virtual")
        logger.info("Region: ru-central-1")

    def get_client(self) -> Any:
        return self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=self.config,
            verify=self.ssl_verify,
            region_name="ru-central-1",
        )

    async def upload_file(self, file_path: str, s3_key: str) -> bool:
        try:
            logger.info(f"Загружаем файл {file_path} как {s3_key}")

            async with (
                self.get_client() as client,
                aiofiles.open(file_path, "rb") as file,
            ):
                payload = await file.read()
                await client.put_object(
                    Bucket=self.bucket_name, Key=s3_key, Body=payload
                )

            logger.info(f"Файл успешно загружен: {s3_key}")
            return True

        except Exception as e:
            logger.error(f"Ошибка при загрузке файла {file_path}: {e!s}")
            return False

    async def download_file(self, s3_key: str, local_path: str) -> bool:
        try:
            import os

            dir_path = os.path.dirname(local_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            async with self.get_client() as client:
                response = await client.get_object(
                    Bucket=self.bucket_name, Key=s3_key
                )
                async with response["Body"] as stream:
                    content = await stream.read()

                async with aiofiles.open(local_path, "wb") as file:
                    await file.write(content)

            return True

        except Exception as e:
            logger.error(f"Ошибка при скачивании файла {s3_key}: {e!s}")
            return False

    def time_format(self, seconds: int | None) -> str:
        if seconds is not None:
            seconds = int(seconds)
            d = seconds // (3600 * 24)
            h = seconds // 3600 % 24
            m = seconds % 3600 // 60
            s = seconds % 3600 % 60
            if d > 0:
                return f"{d:02d}d {h:02d}h {m:02d}m {s:02d}s"
            elif h > 0:
                return f"{h:02d}h {m:02d}m {s:02d}s"
            elif m > 0:
                return f"{m:02d}m {s:02d}s"
            elif s > 0:
                return f"{s:02d}s"
        return "-"

    async def generate_presigned_put_url(
        self,
        s3_key: str,
        expiration: int = 3600,
        content_type: str | None = None,
    ) -> str:
        """
        Генерирует presigned URL для загрузки файла (PUT)

        Args:
            s3_key: Ключ файла в S3
            expiration: Время жизни ссылки в секундах (по умолчанию 1 час)
            content_type: MIME тип контента (опционально)

        Returns:
            str: Presigned URL для загрузки

        Raises:
            Exception: В случае ошибки генерации URL
        """
        try:
            # Убираем ведущий слэш если есть
            s3_key = s3_key.lstrip("/")

            logger.info(f"Генерируем presigned PUT URL для {s3_key}")

            async with self.get_client() as client:
                params: dict[str, Any] = {
                    "Bucket": self.bucket_name,
                    "Key": s3_key,
                }

                if content_type:
                    params["ContentType"] = content_type

                url = await client.generate_presigned_url(
                    "put_object", Params=params, ExpiresIn=expiration
                )

            logger.info(f"Presigned PUT URL сгенерирован для {s3_key}")
            return str(url)

        except Exception as e:
            error_msg = (
                f"Ошибка при генерации presigned PUT URL для {s3_key}: {e!s}"
            )
            logger.error(error_msg)
            raise Exception(error_msg) from e

    async def generate_presigned_get_url(
        self,
        s3_key: str,
        expiration: int = 3600,
    ) -> str:
        """
        Генерирует presigned URL для скачивания файла (GET)

        Args:
            s3_key: Ключ файла в S3
            expiration: Время жизни ссылки в секундах (по умолчанию 1 час)

        Returns:
            str: Presigned URL для скачивания

        Raises:
            Exception: В случае ошибки генерации URL
        """
        try:
            # Убираем ведущий слэш если есть
            s3_key = s3_key.lstrip("/")

            logger.info(f"Генерируем presigned GET URL для {s3_key}")

            async with self.get_client() as client:
                url = await client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": s3_key},
                    ExpiresIn=expiration,
                )

            logger.info(f"Presigned GET URL сгенерирован для {s3_key}")
            return str(url)

        except Exception as e:
            error_msg = (
                f"Ошибка при генерации presigned GET URL для {s3_key}: {e!s}"
            )
            logger.error(error_msg)
            raise Exception(error_msg) from e

    async def list_objects(self, prefix: str = "") -> list[dict[str, Any]]:
        """
        Получает список всех объектов в бакете

        Args:
            prefix: Префикс для фильтрации объектов (например, для подпапки)

        Returns:
            list[dict]: Список объектов с их метаданными
        """
        try:
            logger.info(f"Получаем список объектов с префиксом: '{prefix}'")

            objects = []

            async with self.get_client() as client:
                paginator = client.get_paginator("list_objects_v2")

                async for page in paginator.paginate(
                    Bucket=self.bucket_name, Prefix=prefix
                ):
                    if "Contents" in page:
                        for obj in page["Contents"]:
                            objects.append(
                                {
                                    "key": obj["Key"],
                                    "size": obj["Size"],
                                    "last_modified": obj["LastModified"],
                                    "etag": obj["ETag"],
                                }
                            )

            logger.info(f"Найдено {len(objects)} объектов")
            return objects

        except Exception as e:
            logger.error(f"Ошибка при получении списка объектов: {e!s}")
            return []
