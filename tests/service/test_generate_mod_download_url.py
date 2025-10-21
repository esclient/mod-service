from unittest.mock import AsyncMock

import pytest
from faker import Faker
from pytest_mock import MockerFixture

from modservice.repository.repository import ModRepository
from modservice.service.s3_service import S3Service
from modservice.service.service import ModService


@pytest.mark.asyncio
async def test_service_generate_mod_download_url(
    mocker: MockerFixture, faker: Faker
) -> None:
    repo = mocker.Mock(spec=ModRepository)
    s3_service = mocker.Mock(spec=S3Service)
    download_url = faker.uri()
    s3_service.generate_mod_download_url = AsyncMock(return_value=download_url)

    service = ModService(repo, s3_service)

    prefix = faker.file_path(depth=1)
    expiration = faker.random_int(min=100, max=10000)

    result = await service.generate_mod_download_url(prefix, expiration)

    assert result == download_url
    s3_service.generate_mod_download_url.assert_awaited_once_with(
        prefix, expiration
    )
