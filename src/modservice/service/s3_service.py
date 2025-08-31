import os
import logging
from datetime import datetime
from typing import Any
import mimetypes

from modservice.repository import insert_s3_key
from modservice.s3_client import S3Client

logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self, s3_client: S3Client) -> None:
        self._s3_client = s3_client

    def generate_s3_key(
        self, 
        author_id: int, 
        filename: str, 
        mod_title: str | None = None
    ) -> str:
        """
        Генерирует S3 ключ с timestamp для уникальности
        
        Args:
            author_id: ID автора
            filename: Имя файла
            mod_title: Заголовок мода (опционально)
            
        Returns:
            str: S3 ключ в формате "author_id/timestamp_filename" 
        """
        # Генерируем timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Очищаем имя файла от недопустимых символов
        safe_filename = self._sanitize_filename(filename)
        
        if mod_title:
            # Очищаем заголовок мода
            safe_title = self._sanitize_title(mod_title)
            # Меняем расширение файла на основе очищенного заголовка
            file_ext = os.path.splitext(safe_filename)[1]
            safe_filename = safe_title + file_ext
        
        s3_key = f"{author_id}/{timestamp}_{safe_filename}"
        logger.info(f"Сгенерирован S3 ключ: {s3_key}")
        
        return s3_key

    def _sanitize_filename(self, filename: str) -> str:
        """Очищает имя файла от недопустимых символов"""
        # Убираем недопустимые символы для S3
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        safe_filename = filename
        for char in invalid_chars:
            safe_filename = safe_filename.replace(char, '_')
        return safe_filename

    def _sanitize_title(self, title: str) -> str:
        """Очищает заголовок мода для использования в имени файла"""
        # Заменяем пробелы и специальные символы на подчеркивания
        safe_title = title.replace(' ', '_')
        safe_title = ''.join(c for c in safe_title if c.isalnum() or c in ['_', '-', '.'])
        # Убираем лишние подчеркивания в конце
        safe_title = safe_title.rstrip('_')
        return safe_title

    def _detect_content_type(self, filename: str) -> str | None:
        """Определяет MIME тип файла по расширению"""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type

    def generate_upload_url(
        self,
        author_id: int,
        filename: str,
        mod_title: str | None = None,
        expiration: int = 3600,
        content_type: str | None = None,
    ) -> tuple[str, str]:
        """
        Генерирует S3 ключ и presigned URL для загрузки файла
        
        Args:
            author_id: ID автора
            filename: Имя файла
            mod_title: Заголовок мода (опционально)
            expiration: Время жизни ссылки в секундах
            content_type: MIME тип контента (автоопределение если None)
            
        Returns:
            tuple[str, str]: (s3_key, presigned_url)
        """
        logger.info(f"Генерируем upload URL для автора {author_id}, файл: {filename}")
        
        # Генерируем S3 ключ
        s3_key = self.generate_s3_key(author_id, filename, mod_title)
        
        # Автоопределение content_type если не указан
        if content_type is None:
            content_type = self._detect_content_type(filename)
        
        # Генерируем presigned URL
        presigned_url = self._s3_client.generate_presigned_put_url(
            s3_key=s3_key, 
            expiration=expiration,
            content_type=content_type
        )
        
        logger.info(f"Upload URL успешно сгенерирован для {s3_key}\nUpload URL: {presigned_url}")
        return s3_key, presigned_url

    def generate_upload_url_for_key(
        self,
        s3_key: str,
        expiration: int = 3600,
        content_type: str | None = None,
    ) -> str:
        """
        Генерирует presigned URL для загрузки файла по существующему S3 ключу
        Используется когда S3 ключ уже создан (например, из базы данных)
        
        Args:
            s3_key: Ключ файла в S3 (обычно в формате "author_id/mod_id")
            expiration: Время жизни ссылки в секундах
            content_type: MIME тип контента (опционально)
            
        Returns:
            str: Presigned URL для загрузки
        """
        logger.info(f"Генерируем upload URL для существующего s3_key: {s3_key}")
        
        presigned_url = self._s3_client.generate_presigned_put_url(
            s3_key=s3_key, 
            expiration=expiration,
            content_type=content_type
        )
        
        logger.info(f"Upload URL успешно сгенерирован для {s3_key}\nUpload URL: {presigned_url}")
        return presigned_url

    def generate_download_url(
        self,
        s3_key: str,
        expiration: int = 3600,
    ) -> str:
        """
        Генерирует presigned URL для скачивания файла
        
        Args:
            s3_key: Ключ файла в S3
            expiration: Время жизни ссылки в секундах
            
        Returns:
            str: Presigned URL для скачивания
        """
        logger.info(f"Генерируем download URL для s3_key: {s3_key}")
        
        presigned_url = self._s3_client.generate_presigned_get_url(
            s3_key=s3_key, 
            expiration=expiration
        )
        
        logger.info(f"Download URL успешно сгенерирован для {s3_key}")
        return presigned_url

    def upload_file(
        self,
        file_path: str,
        s3_key: str,
    ) -> bool:
        """
        Загружает файл напрямую в S3
        
        Args:
            file_path: Путь к локальному файлу
            s3_key: Ключ файла в S3
            
        Returns:
            bool: True если загрузка успешна, False иначе
        """
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
        """
        Скачивает файл из S3
        
        Args:
            s3_key: Ключ файла в S3
            local_path: Путь для сохранения локального файла
            
        Returns:
            bool: True если скачивание успешно, False иначе
        """
        logger.info(f"Скачиваем файл {s3_key} в {local_path}")
        
        success = self._s3_client.download_file(s3_key, local_path)
        
        if success:
            logger.info(f"Файл успешно скачан: {local_path}")
        else:
            logger.error(f"Ошибка скачивания файла: {s3_key}")
            
        return success

    def list_files(self, prefix: str = "") -> list[dict[str, Any]]:
        """
        Получает список файлов в бакете
        
        Args:
            prefix: Префикс для фильтрации файлов
            
        Returns:
            list[dict]: Список файлов с метаданными
        """
        logger.info(f"Получаем список файлов с префиксом: '{prefix}'")
        
        files = self._s3_client.list_objects(prefix)
        
        logger.info(f"Найдено {len(files)} файлов")
        return files

    def get_file_info_from_s3_key(self, s3_key: str) -> dict[str, Any]:
        """
        Парсит информацию из S3 ключа
        
        Args:
            s3_key: Ключ файла в S3 (формат: "author_id/mod_id" или более сложный)
            
        Returns:
            dict: Информация о файле
        """
        try:
            parts = s3_key.split("/")
            if len(parts) >= 2:
                author_id = int(parts[0])

                # Разбираем оставшуюся часть
                remaining_parts = parts[1:]
                if len(remaining_parts) == 1:
                    # Возможно это просто mod_id или timestamp_filename
                    mod_part = remaining_parts[0]

                    # Проверяем, является ли это числом (mod_id)
                    try:
                        mod_id = int(mod_part)
                        return {
                            "author_id": author_id,
                            "mod_id": mod_id,
                            "full_s3_key": s3_key,
                        }
                    except ValueError:
                        # Это не число, возможно timestamp_filename
                        timestamp_filename = mod_part
                        
                        if len(timestamp_filename) > 16:  # Минимальная длина timestamp + underscore + filename
                            # Ищем позицию после timestamp (YYYYMMDD_HHMMSS_)
                            timestamp_end = timestamp_filename.find("_", 15)  # Ищем _ после timestamp
                            if timestamp_end > 0:
                                timestamp_part = timestamp_filename[:timestamp_end]
                                filename = timestamp_filename[timestamp_end + 1 :]

                                return {
                                    "author_id": author_id,
                                    "timestamp": timestamp_part,
                                    "filename": filename,
                                    "full_s3_key": s3_key,
                                }
                
                # Если не удалось разобрать как одну часть, склеиваем все остальные части
                return {
                    "author_id": author_id,
                    "filename": "/".join(remaining_parts),
                    "full_s3_key": s3_key,
                }
                
        except (ValueError, IndexError) as e:
            logger.error(f"Ошибка парсинга S3 ключа '{s3_key}': {e}")

        return {"full_s3_key": s3_key, "error": "Не удалось разобрать S3-ключ"}
