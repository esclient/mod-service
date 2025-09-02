from modservice.repository.repository import ModRepository
from modservice.service.s3_service import S3Service


def create_mod(
    repo: ModRepository,
    s3_service: S3Service,
    mod_title: str,
    author_id: int,
    description: str,
) -> tuple[int, str, str]:
    mod_id = repo.create_mod(mod_title, author_id, description)

    s3_key = repo.insert_s3_key(mod_id, author_id)

    upload_url = s3_service.generate_mod_upload_url(s3_key_prefix=s3_key)

    return mod_id, s3_key, upload_url
