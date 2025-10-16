from modservice.repository.repository import ModRepository
from modservice.service.s3_service import S3Service


async def create_mod(
    repo: ModRepository,
    s3_service: S3Service,
    title: str,
    author_id: int,
    description: str,
) -> tuple[int, str, str]:
    mod_id = await repo.create_mod(title, author_id, description)

    s3_key = await repo.insert_s3_key(mod_id, author_id)

    upload_url = await s3_service.generate_mod_upload_url(s3_key_prefix=s3_key)

    return mod_id, s3_key, upload_url
