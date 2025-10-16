from modservice.repository.repository import ModRepository
from modservice.service.s3_service import S3Service


async def get_mod_download_link(
    repo: ModRepository,
    s3_service: S3Service,
    mod_id: int,
    expiration: int = 3600,
) -> str:
    s3_key = await repo.get_mod_s3_key(mod_id)

    download_url = await s3_service.generate_mod_download_url(
        s3_key_prefix=s3_key, expiration=expiration
    )

    return download_url
