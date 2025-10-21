from unittest.mock import AsyncMock

import pytest
from faker import Faker
from pytest_mock import MockerFixture

from modservice.repository.repository import ModRepository
from modservice.service.s3_service import S3Service
from modservice.service.service import ModService


@pytest.mark.asyncio
async def test_service_get_mods_returns_helper_result(
    mocker: MockerFixture, faker: Faker
) -> None:
    repo = mocker.Mock(spec=ModRepository)
    s3_service = mocker.Mock(spec=S3Service)
    mods = [{"id": faker.random_int(), "title": faker.word()}]
    helper = AsyncMock(return_value=mods)
    mocker.patch("modservice.service.service._get_mods", helper)

    service = ModService(repo, s3_service)

    result = await service.get_mods()

    assert result == mods
    helper.assert_awaited_once_with(repo)
