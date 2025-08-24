import os
from datetime import datetime
from typing import Optional, Tuple
from modservice.s3_client import S3Client


class S3Service:
    """Сервис для работы с S3"""
    
    def __init__(self, s3_client: S3Client):
        self._s3_client = s3_client
    
    def generate_s3_key(
        self,
        author_id: int,
        filename: str,
        mod_title: Optional[str] = None
    ) -> str:
        """
        Генерирует уникальный S3-ключ для файла мода
        
        Args:
            author_id: ID автора мода
            filename: Имя файла
            mod_title: Название мода (опционально)
        
        Returns:
            Уникальный S3-ключ в формате: mods/{author_id}/{timestamp}_{filename}
        """
        file_extension = os.path.splitext(filename)[1]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        base_filename = os.path.splitext(filename)[0]
        
        # Создаем S3-ключ
        if mod_title: # Если название имя мода в параметры при генерации s3 ключа
            # Очищаем название мода от недопустимых символов
            safe_title = "".join(c for c in mod_title if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            safe_title = safe_title.replace(' ', '_').replace('.', '_')
            safe_title = '_'.join(filter(None, safe_title.split('_'))) # Убираем множественные подчеркивания
            s3_key = f"mods/{author_id}/{timestamp}_{safe_title}{file_extension}"
        else:
            s3_key = f"mods/{author_id}/{timestamp}_{base_filename}{file_extension}"
        
        return s3_key
    
    def generate_upload_url(
        self,
        author_id: int,
        filename: str,
        mod_title: Optional[str] = None,
        expiration: int = 3600,
        content_type: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Генерирует S3-ключ и presigned URL для загрузки файла
        
        Args:
            author_id: ID автора мода
            filename: Имя файла
            mod_title: Название мода (опционально)
            expiration: Время жизни URL в секундах (по умолчанию 1 час)
            content_type: Тип содержимого файла (опционально)
        
        Returns:
            Кортеж (s3_key, presigned_url)
        """
        s3_key = self.generate_s3_key(author_id, filename, mod_title)
        
        # Определяем content_type на основе расширения файла, если не указан
        if not content_type:
            file_extension = os.path.splitext(filename)[1].lower()
            content_type_map = {
                '.zip': 'application/zip',
                '.rar': 'application/x-rar-compressed',
                '.7z': 'application/x-7z-compressed',
                '.tar': 'application/x-tar',
                '.gz': 'application/gzip',
                '.bz2': 'application/x-bzip2'
            }
            content_type = content_type_map.get(file_extension, 'application/octet-stream')
        
        presigned_url = self._s3_client.generate_presigned_put_url(
            s3_key=s3_key,
            expiration=expiration,
            content_type=content_type
        )
        
        return s3_key, presigned_url
    
    def get_file_info_from_s3_key(self, s3_key: str) -> dict:
        """
        Извлекает информацию о файле из S3-ключа
        
        Args:
            s3_key: S3-ключ в формате mods/{author_id}/{timestamp}_{filename}
        
        Returns:
            Словарь с информацией о файле
        """
        try:
            parts = s3_key.split('/')
            if len(parts) >= 3 and parts[0] == 'mods':
                author_id = int(parts[1])
                
                # Разбираем оставшуюся часть
                remaining_parts = parts[2:]
                if len(remaining_parts) == 1:
                    timestamp_filename = remaining_parts[0] # timestamp имеет формат YYYYMMDD_HHMMSS (15 символов + underscore)
                    
                    if len(timestamp_filename) > 16:  # Минимальная длина timestamp + underscore + filename
                        # Ищем позицию после timestamp (YYYYMMDD_HHMMSS_)
                        timestamp_end = timestamp_filename.find('_', 15)  # Ищем _ после timestamp
                        if timestamp_end > 0:
                            timestamp_part = timestamp_filename[:timestamp_end]
                            filename = timestamp_filename[timestamp_end + 1:]
                            
                            return {
                                'author_id': author_id,
                                'timestamp': timestamp_part,
                                'filename': filename,
                                'full_s3_key': s3_key
                            }
                
                return {
                    'author_id': author_id,
                    'filename': '_'.join(remaining_parts),
                    'full_s3_key': s3_key
                }
        except (ValueError, IndexError):
            pass
        
        return {
            'full_s3_key': s3_key,
            'error': 'Не удалось разобрать S3-ключ'
        }
