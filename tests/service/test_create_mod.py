from unittest.mock import AsyncMock

import pytest
from faker import Faker
from pytest_mock import MockerFixture

from modservice.moderation.moderation_service import ModerationService
from modservice.repository.repository import ModRepository
from modservice.service.s3_service import S3Service
from modservice.service.service import ModService


@pytest.mark.asyncio
async def test_service_create_mod_invokes_helper(
    mocker: MockerFixture, faker: Faker
) -> None:
    repo = mocker.Mock(spec=ModRepository)
    s3_service = mocker.Mock(spec=S3Service)
    moderation_service = mocker.Mock(spec=ModerationService)
    moderation_service.send_moderation_request = AsyncMock()
    service = ModService(repo, s3_service, moderation_service)

    expected = (
        faker.random_int(min=1, max=100000),
        f"{faker.random_int(min=1, max=100000)}/{faker.random_int(min=1, max=100000)}",
        faker.uri(),
    )
    helper = AsyncMock(return_value=expected)
    mocker.patch("modservice.service.service._create_mod", helper)

    title = faker.sentence(nb_words=3)
    author_id = faker.random_int(min=1, max=100000)
    description = faker.text()

    result = await service.create_mod(title, author_id, description)

    assert result == expected
    helper.assert_awaited_once_with(
        repo, s3_service, title, author_id, description
    )
    moderation_service.send_moderation_request.assert_awaited_once_with(
        expected[0], title, description
    )
