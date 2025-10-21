import pytest
from faker import Faker
from pytest_mock import MockerFixture

from modservice.repository.repository import ModRepository
from modservice.service.s3_service import S3Service
from modservice.service.service import ModService


@pytest.mark.asyncio
async def test_service_get_file_info_from_s3_key_passes_through(
    mocker: MockerFixture, faker: Faker
) -> None:
    repo = mocker.Mock(spec=ModRepository)
    s3_service = mocker.Mock(spec=S3Service)
    info = {
        "author_id": faker.random_int(min=1, max=100000),
        "full_s3_key": faker.file_path(depth=2),
    }
    s3_service.get_file_info_from_s3_key.return_value = info

    service = ModService(repo, s3_service)

    s3_key = faker.file_path(depth=2)
    result = await service.get_file_info_from_s3_key(s3_key)

    assert result is info
    s3_service.get_file_info_from_s3_key.assert_called_once_with(s3_key)
