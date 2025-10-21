from unittest.mock import AsyncMock

import grpc
import pytest
from faker import Faker
from pytest_mock import MockerFixture

from modservice.grpc import mod_pb2
from modservice.handler.set_status import SetStatus
from modservice.service.service import ModService


@pytest.mark.asyncio
async def test_set_status_success(mocker: MockerFixture, faker: Faker) -> None:
    context = mocker.Mock(spec=grpc.ServicerContext)
    service = mocker.Mock(spec=ModService)
    service.set_status = AsyncMock(return_value=True)

    mod_id = faker.random_int(min=1, max=100000)
    request = mod_pb2.SetStatusRequest(
        mod_id=mod_id,
        status=mod_pb2.ModStatus.MOD_STATUS_UPLOADED,
    )

    response = await SetStatus(service, request, context)

    assert isinstance(response, mod_pb2.SetStatusResponse)
    assert response.success is True
    service.set_status.assert_awaited_once_with(mod_id, "UPLOADED")
    context.set_code.assert_not_called()
    context.set_details.assert_not_called()


@pytest.mark.asyncio
async def test_set_status_invalid_enum_sets_error(
    mocker: MockerFixture, faker: Faker
) -> None:
    context = mocker.Mock(spec=grpc.ServicerContext)
    service = mocker.Mock(spec=ModService)
    service.set_status = AsyncMock()

    request = mod_pb2.SetStatusRequest(
        mod_id=faker.random_int(min=1, max=100000),
        status=mod_pb2.ModStatus.MOD_STATUS_UNSPECIFIED,
    )

    response = await SetStatus(service, request, context)

    assert response.success is False
    service.set_status.assert_not_called()
    context.set_code.assert_called_once_with(grpc.StatusCode.INVALID_ARGUMENT)
    context.set_details.assert_called_once_with("Status must be specified")


@pytest.mark.asyncio
async def test_set_status_internal_error_sets_context(
    mocker: MockerFixture, faker: Faker
) -> None:
    context = mocker.Mock(spec=grpc.ServicerContext)
    service = mocker.Mock(spec=ModService)
    error = RuntimeError(faker.sentence())
    service.set_status = AsyncMock(side_effect=error)

    request = mod_pb2.SetStatusRequest(
        mod_id=faker.random_int(min=1, max=100000),
        status=mod_pb2.ModStatus.MOD_STATUS_BANNED,
    )

    response = await SetStatus(service, request, context)

    assert response.success is False
    context.set_code.assert_called_once_with(grpc.StatusCode.INTERNAL)
    assert (
        context.set_details.call_args.args[0]
        == f"Failed to set status: {error!s}"
    )
