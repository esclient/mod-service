from unittest.mock import AsyncMock

import pytest
from faker import Faker
from pytest_mock import MockerFixture

from modservice.repository.repository import ModRepository
from modservice.service.s3_service import S3Service
from modservice.service.service import ModService


@pytest.mark.asyncio
async def test_service_get_mod_download_link(
    mocker: MockerFixture, faker: Faker
) -> None:
    repo = mocker.Mock(spec=ModRepository)
    s3_service = mocker.Mock(spec=S3Service)

    s3_key = faker.file_path(depth=2)
    repo.get_mod_s3_key = AsyncMock(return_value=s3_key)
    download_url = faker.uri()
    s3_service.generate_mod_download_url = AsyncMock(return_value=download_url)

    service = ModService(repo, s3_service)

    mod_id = faker.random_int(min=1, max=100000)
    expiration = faker.random_int(min=100, max=10000)

    result = await service.get_mod_download_link(mod_id, expiration)

    assert result == download_url
    repo.get_mod_s3_key.assert_awaited_once_with(mod_id)
    s3_service.generate_mod_download_url.assert_awaited_once_with(
        s3_key, expiration
    )
