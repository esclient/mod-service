from unittest.mock import AsyncMock

import grpc
import pytest
from faker import Faker
from pytest_mock import MockerFixture

from modservice.grpc import mod_pb2
from modservice.handler.create_mod import CreateMod
from modservice.service.service import ModService


@pytest.mark.asyncio
async def test_create_mod_returns_response(
    mocker: MockerFixture, faker: Faker
) -> None:
    context = mocker.Mock(spec=grpc.ServicerContext)
    service = mocker.Mock(spec=ModService)
    mod_id = faker.random_int(min=1, max=100000)
    s3_key = f"{faker.random_int(min=1, max=100000)}/{mod_id}"
    upload_url = faker.uri()
    service.create_mod = AsyncMock(return_value=(mod_id, s3_key, upload_url))

    request = mod_pb2.CreateModRequest(
        title=faker.sentence(nb_words=4),
        author_id=faker.random_int(min=1, max=100000),
        description=faker.text(),
    )

    response = await CreateMod(service, request, context)

    assert isinstance(response, mod_pb2.CreateModResponse)
    assert response.mod_id == mod_id
    assert response.s3_key == s3_key
    assert response.upload_url == upload_url
    service.create_mod.assert_awaited_once_with(
        request.title, request.author_id, request.description
    )
