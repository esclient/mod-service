from datetime import UTC, datetime
from unittest.mock import AsyncMock

import grpc
import pytest
from faker import Faker
from google.protobuf.timestamp_pb2 import Timestamp
from pytest_mock import MockerFixture

from modservice.constants import STATUS_BANNED, STATUS_UPLOADED
from modservice.grpc import mod_pb2
from modservice.handler.get_mods import GetMods
from modservice.service.service import ModService


def _ts_from_datetime(dt: datetime) -> Timestamp:
    ts = Timestamp()
    ts.FromDatetime(dt)
    return ts


@pytest.mark.asyncio
async def test_get_mods_converts_models(
    mocker: MockerFixture, faker: Faker
) -> None:
    context = mocker.Mock(spec=grpc.ServicerContext)
    service = mocker.Mock(spec=ModService)

    created_at_first = faker.date_time(tzinfo=UTC)
    created_at_second = faker.date_time(tzinfo=UTC)

    mods_data = [
        {
            "id": faker.random_int(min=1, max=100000),
            "author_id": faker.random_int(min=1, max=100000),
            "title": faker.sentence(nb_words=3),
            "description": faker.text(),
            "version": faker.random_int(min=1, max=10),
            "s3_key": faker.file_path(depth=2),
            "status": STATUS_UPLOADED,
            "created_at": _ts_from_datetime(created_at_first),
        },
        {
            "id": faker.random_int(min=1, max=100000),
            "author_id": faker.random_int(min=1, max=100000),
            "title": faker.sentence(nb_words=4),
            "description": faker.text(),
            "version": faker.random_int(min=1, max=10),
            "s3_key": faker.file_path(depth=2),
            "status": STATUS_BANNED,
            "created_at": _ts_from_datetime(created_at_second),
        },
    ]
    service.get_mods = AsyncMock(return_value=mods_data)

    request = mod_pb2.GetModsRequest()
    response = await GetMods(service, request, context)

    assert isinstance(response, mod_pb2.GetModsResponse)
    assert len(response.mods) == 2

    first_mod = response.mods[0]
    assert first_mod.id == mods_data[0]["id"]
    assert first_mod.author_id == mods_data[0]["author_id"]
    assert first_mod.title == mods_data[0]["title"]
    assert first_mod.description == mods_data[0]["description"]
    assert first_mod.version == mods_data[0]["version"]
    assert first_mod.status == mod_pb2.ModStatus.MOD_STATUS_UPLOADED
    assert first_mod.created_at == mods_data[0]["created_at"]

    second_mod = response.mods[1]
    assert second_mod.status == mod_pb2.ModStatus.MOD_STATUS_BANNED
    assert second_mod.created_at == mods_data[1]["created_at"]

    service.get_mods.assert_awaited_once_with()
