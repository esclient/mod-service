"""Tests for ModerationService."""

from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from modservice.grpc.moderation_pb2 import ObjectType
from modservice.moderation.moderation_service import ModerationService


@pytest.fixture
def mock_producer() -> Mock:
    """Create a mock Kafka producer."""
    producer = Mock()
    producer.send_moderation_request = AsyncMock()
    return producer


@pytest.fixture
def mock_repository() -> Mock:
    """Create a mock repository."""
    repository = Mock()
    repository.set_status = AsyncMock()
    return repository


@pytest.fixture
def moderation_service(
    mock_producer: Mock, mock_repository: Mock
) -> ModerationService:
    """Create a ModerationService instance with mocked dependencies."""
    return ModerationService(mock_producer, mock_repository)


@pytest.mark.asyncio
async def test_send_moderation_request_combines_title_and_description(
    moderation_service: ModerationService, mock_producer: Mock
) -> None:
    """Test that send_moderation_request combines title and description with single space."""
    mod_id = 123
    title = "Test Mod"
    description = "This is a test mod"

    await moderation_service.send_moderation_request(
        mod_id, title, description
    )

    mock_producer.send_moderation_request.assert_called_once_with(
        object_id=mod_id,
        object_type=ObjectType.OBJECT_TYPE_MOD_DESCRIPTION,
        text="Test Mod This is a test mod",
    )


@pytest.mark.asyncio
async def test_send_moderation_request_handles_producer_failure(
    moderation_service: ModerationService, mock_producer: Mock, caplog: Any
) -> None:
    """Test that send_moderation_request logs errors without raising exceptions."""
    mock_producer.send_moderation_request.side_effect = Exception(
        "Kafka error"
    )

    # Should not raise exception
    await moderation_service.send_moderation_request(
        123, "Title", "Description"
    )

    # Should log error
    assert "Failed to send moderation request for mod 123" in caplog.text


@pytest.mark.asyncio
async def test_process_moderation_response_approved(
    moderation_service: ModerationService, mock_repository: Mock
) -> None:
    """Test that approved response sets status to UPLOADED."""
    mock_repository.set_status.return_value = True

    await moderation_service.process_moderation_response(123, approved=True)

    mock_repository.set_status.assert_called_once_with(123, "UPLOADED")


@pytest.mark.asyncio
async def test_process_moderation_response_rejected(
    moderation_service: ModerationService, mock_repository: Mock
) -> None:
    """Test that rejected response sets status to BANNED."""
    mock_repository.set_status.return_value = True

    await moderation_service.process_moderation_response(123, approved=False)

    mock_repository.set_status.assert_called_once_with(123, "BANNED")


@pytest.mark.asyncio
async def test_process_moderation_response_mod_not_found(
    moderation_service: ModerationService, mock_repository: Mock, caplog: Any
) -> None:
    """Test that warning is logged when mod is not found."""
    mock_repository.set_status.return_value = False

    await moderation_service.process_moderation_response(123, approved=True)

    assert "Mod 123 not found for status update" in caplog.text


@pytest.mark.asyncio
async def test_process_moderation_response_handles_exception(
    moderation_service: ModerationService, mock_repository: Mock, caplog: Any
) -> None:
    """Test that exceptions during status update are logged."""
    mock_repository.set_status.side_effect = Exception("Database error")

    await moderation_service.process_moderation_response(123, approved=True)

    assert "Failed to update mod 123 status" in caplog.text
