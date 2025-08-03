from modservice.grpc.mod_pb2 import TestModRequest, TestModResponse
from modservice.handler.test_mod import TestMod

def test_testmod_returns_success_true():
    request = TestModRequest()
    response = TestMod(request, None)

    assert isinstance(response, TestModResponse)
    assert response.success is True

    assert response == TestModResponse(success=True)
