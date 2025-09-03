from modservice.repository.repository import ModRepository
from modservice.service.s3_service import S3Service


def get_mod_download_link(
    repo: ModRepository,
    s3_service: S3Service,
    mod_id: int,
    expiration: int = 3600
) -> tuple[int, str, str]:


    s3_key = repo.get_mod_download_link(mod_id)

    download_url = s3_service.generate_mod_download_url(
        s3_key_prefix=s3_key,
        expiration=expiration
    )

    return mod_id, s3_key, download_url
