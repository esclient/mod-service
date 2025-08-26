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
    # Генерируем S3 ключ для папки мода
    s3_key = s3_service.generate_s3_key(author_id, filename, mod_title)

    s3_folder_key = s3_key.rsplit(".", 1)[0] if "." in s3_key else s3_key

    # Создаем upload_url как путь к папке в S3
    bucket_name = s3_service._s3_client.bucket_name
    endpoint_url = s3_service._s3_client.config.get("endpoint_url", "")
    upload_url = f"{endpoint_url}/{bucket_name}/{s3_folder_key}"

    # Сохраняем мод в базе данных с s3_key папки
    mod_id, _, _ = repo.create_mod(
        mod_title, author_id, filename, description, s3_folder_key
    )

    return mod_id, s3_folder_key, upload_url
