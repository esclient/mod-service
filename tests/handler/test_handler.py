from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock

import grpc
import pytest
from faker import Faker
from pytest_mock import MockerFixture

import modservice.handler.handler as handler_module
from modservice.grpc import mod_pb2
from modservice.handler.handler import ModHandler
from modservice.service.service import ModService


def _build_create_pair(
    faker: Faker,
) -> tuple[mod_pb2.CreateModRequest, mod_pb2.CreateModResponse]:
    mod_id = faker.random_int(min=1, max=100000)
    s3_key = f"{faker.random_int(min=1, max=100000)}/{mod_id}"
    response = mod_pb2.CreateModResponse(
        mod_id=mod_id,
        upload_url=faker.uri(),
        s3_key=s3_key,
    )
    request = mod_pb2.CreateModRequest(
        title=faker.sentence(nb_words=3),
        author_id=faker.random_int(min=1, max=100000),
        filename=faker.file_name(),
        description=faker.text(),
    )
    return request, response


def _build_download_link_pair(
    faker: Faker,
) -> tuple[
    mod_pb2.GetModDownloadLinkRequest, mod_pb2.GetModDownloadLinkResponse
]:
    mod_id = faker.random_int(min=1, max=100000)
    response = mod_pb2.GetModDownloadLinkResponse(link_url=faker.uri())
    request = mod_pb2.GetModDownloadLinkRequest(mod_id=mod_id)
    return request, response


def _build_set_status_pair(
    faker: Faker,
) -> tuple[mod_pb2.SetStatusRequest, mod_pb2.SetStatusResponse]:
    request = mod_pb2.SetStatusRequest(
        mod_id=faker.random_int(min=1, max=100000),
        status=mod_pb2.ModStatus.MOD_STATUS_BANNED,
    )
    response = mod_pb2.SetStatusResponse(success=True)
    return request, response


def _build_get_mods_pair(
    faker: Faker,
) -> tuple[mod_pb2.GetModsRequest, mod_pb2.GetModsResponse]:
    response = mod_pb2.GetModsResponse()
    response.mods.add(
        id=faker.random_int(min=1, max=100000),
        author_id=faker.random_int(min=1, max=100000),
        title=faker.sentence(nb_words=3),
        description=faker.text(),
        version=1,
        status=mod_pb2.ModStatus.MOD_STATUS_UPLOADED,
    )
    request = mod_pb2.GetModsRequest()
    return request, response


@dataclass(frozen=True)
class HandlerCase:
    method_name: str
    helper_attr: str
    builder: Callable[[Faker], tuple[Any, Any]]


CASES: tuple[HandlerCase, ...] = (
    HandlerCase("CreateMod", "_create_mod", _build_create_pair),
    HandlerCase(
        "GetModDownloadLink",
        "_get_mod_download_link",
        _build_download_link_pair,
    ),
    HandlerCase("SetStatus", "_set_status", _build_set_status_pair),
    HandlerCase("GetMods", "_get_mods", _build_get_mods_pair),
)


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.method_name)
async def test_mod_handler_delegates_to_helper(
    mocker: MockerFixture,
    faker: Faker,
    case: HandlerCase,
) -> None:
    service = mocker.Mock(spec=ModService)
    handler = ModHandler(service)
    request, expected_response = case.builder(faker)

    helper = mocker.patch.object(
        handler_module,
        case.helper_attr,
        new=AsyncMock(return_value=expected_response),
    )
    context = mocker.Mock(spec=grpc.ServicerContext)

    method = getattr(handler, case.method_name)
    result = await method(request, context)

    assert result is expected_response
    helper.assert_awaited_once_with(service, request, context)
