from unittest.mock import AsyncMock

import pytest
from faker import Faker
from pytest_mock import MockerFixture

from modservice.repository.repository import ModRepository
from modservice.service.s3_service import S3Service
from modservice.service.service import ModService


@pytest.mark.asyncio
async def test_service_generate_upload_url_calls_s3_service(
    mocker: MockerFixture, faker: Faker
) -> None:
    repo = mocker.Mock(spec=ModRepository)
    s3_service = mocker.Mock(spec=S3Service)
    expected = (faker.file_path(depth=2), faker.uri())
    s3_service.generate_upload_url = AsyncMock(return_value=expected)

    service = ModService(repo, s3_service)

    author_id = faker.random_int(min=1, max=100000)
    filename = faker.file_name()
    title = faker.sentence(nb_words=2)
    expiration = faker.random_int(min=100, max=10000)
    content_type = "application/zip"

    result = await service.generate_upload_url(
        author_id, filename, title, expiration, content_type
    )

    assert result == expected
    s3_service.generate_upload_url.assert_awaited_once_with(
        author_id, filename, title, expiration, content_type
    )
