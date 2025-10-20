from unittest.mock import AsyncMock

import grpc
import pytest
from faker import Faker
from pytest_mock import MockerFixture

from modservice.grpc import mod_pb2
from modservice.handler.get_mod_download_link import GetDownloadLink
from modservice.service.service import ModService


@pytest.mark.asyncio
async def test_get_download_link_returns_url(
    mocker: MockerFixture, faker: Faker
) -> None:
    context = mocker.Mock(spec=grpc.ServicerContext)
    service = mocker.Mock(spec=ModService)
    url = faker.uri()
    service.get_mod_download_link = AsyncMock(return_value=url)

    mod_id = faker.random_int(min=1, max=100000)
    request = mod_pb2.GetModDownloadLinkRequest(mod_id=mod_id)
    response = await GetDownloadLink(service, request, context)

    assert isinstance(response, mod_pb2.GetModDownloadLinkResponse)
    assert response.link_url == url
    service.get_mod_download_link.assert_awaited_once_with(mod_id)
