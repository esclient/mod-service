import grpc
from pytest_mock import MockerFixture

from modservice.grpc.mod_pb2 import CreateModRequest, CreateModResponse
from modservice.handler.test_mod import TestMod


def test_testmod_returns_success_true(mocker: MockerFixture) -> None:
    ctx = mocker.Mock(spec=grpc.ServicerContext)

    request = CreateModRequest()
    response = TestMod(request, ctx)

    assert isinstance(response, CreateModResponse)
    assert response.success is True

    assert response == CreateModResponse(success=True)
