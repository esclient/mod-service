from unittest.mock import AsyncMock

import pytest
from faker import Faker
from pytest_mock import MockerFixture

from modservice.repository.repository import ModRepository
from modservice.service.s3_service import S3Service
from modservice.service.service import ModService


@pytest.mark.asyncio
async def test_service_set_status_uses_helper(
    mocker: MockerFixture, faker: Faker
) -> None:
    repo = mocker.Mock(spec=ModRepository)
    s3_service = mocker.Mock(spec=S3Service)
    helper = AsyncMock(return_value=True)
    mocker.patch("modservice.service.service._set_status", helper)

    service = ModService(repo, s3_service)

    mod_id = faker.random_int(min=1, max=100000)
    status = "UPLOADED"

    result = await service.set_status(mod_id, status)

    assert result is True
    helper.assert_awaited_once_with(repo, mod_id, status)
