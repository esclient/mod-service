# src/modservice/service/create_mod.py

from modservice.repository.repository import ModRepository
from modservice.service.s3_service import S3Service


def create_mod(
    repo: ModRepository,
    s3_service: S3Service,
    mod_title: str,
    author_id: int,
    filename: str,
    description: str,
) -> tuple[int, str, str]:
    """
    Создает новый мод в базе данных и генерирует ссылку для загрузки
    
    Args:
        repo: Репозиторий для работы с базой данных
        s3_service: Сервис для работы с S3
        mod_title: Название мода
        author_id: ID автора
        filename: Имя файла мода
        description: Описание мода
        
    Returns:
        tuple[int, str, str]: (mod_id, s3_key, upload_url)
    """
    # Сохраняем мод в базе данных с пустым s3_key
    mod_id = repo.create_mod(
        mod_title, author_id, description
    )
    
    # Генерируем S3 ключ для мода в формате author_id/mod_id
    s3_key = repo.insert_s3_key(mod_id, author_id)

    # Генерируем presigned URL для загрузки файла
    # Используем s3_key из базы данных (формат: "author_id/mod_id")
    upload_url = s3_service.generate_upload_url_for_key(s3_key)

    return mod_id, s3_key, upload_url
