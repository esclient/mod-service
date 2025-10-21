import pytest
from faker import Faker
from pytest_mock import MockerFixture

from modservice.repository.repository import ModRepository
from modservice.service.s3_service import S3Service
from modservice.service.service import ModService


@pytest.mark.asyncio
async def test_service_generate_s3_key_uses_s3_service(
    mocker: MockerFixture, faker: Faker
) -> None:
    repo = mocker.Mock(spec=ModRepository)
    s3_service = mocker.Mock(spec=S3Service)
    expected_key = faker.file_path(depth=2)
    s3_service.generate_s3_key.return_value = expected_key

    service = ModService(repo, s3_service)

    author_id = faker.random_int(min=1, max=100000)
    filename = faker.file_name()
    title = faker.sentence(nb_words=2)

    result = await service.generate_s3_key(author_id, filename, title)

    assert result == expected_key
    s3_service.generate_s3_key.assert_called_once_with(
        author_id, filename, title
    )
