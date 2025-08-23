import grpc
from pytest_mock import MockerFixture

from modservice.grpc.mod_pb2 import CreateModRequest, CreateModResponse
from modservice.handler.test_mod import TestMod


def test_testmod_returns_success_true(mocker: MockerFixture) -> None:
    ctx = mocker.Mock(spec=grpc.ServicerContext)

    request = CreateModRequest()
    response = TestMod(request, ctx)

    assert isinstance(response, CreateModResponse)

    assert hasattr(response, "mod_id")
    assert hasattr(response, "upload_url")
    assert hasattr(response, "s3_key")

    assert isinstance(response.mod_id, int)
    assert isinstance(response.upload_url, str)
    assert isinstance(response.s3_key, str)

    assert response.mod_id > 0
    assert response.upload_url != ""
    assert response.s3_key != ""
