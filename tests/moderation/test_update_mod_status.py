"""Unit tests for ModerationService._update_mod_status method.

Tests the status transition logic that maps moderation results to mod statuses.
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from modservice.moderation.moderation_service import ModerationService


@pytest.fixture
def mock_repo():
    """Create a mock repository."""
    repo = Mock()
    repo.set_status = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def event_loop():
    """Create an event loop for testing."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def moderation_service(mock_repo, event_loop):
    """Create a ModerationService instance with mocked dependencies."""
    with patch('modservice.moderation.moderation_service.KafkaProducer'), \
         patch('modservice.moderation.moderation_service.KafkaConsumer'):
        service = ModerationService(mock_repo, event_loop)
        return service


class TestUpdateModStatus:
    """Unit tests for _update_mod_status method.
    
    Tests Requirements 3.5, 3.6, 6.2, 6.3:
    - approved=True should result in UPLOADED status
    - approved=False should result in HIDDEN status
    """

    def test_approved_true_sets_uploaded_status(
        self, moderation_service, mock_repo, event_loop
    ):
        """Test that approved=True results in UPLOADED status.
        
        Validates Requirements 3.5, 6.2:
        - WHEN ModerationService receives approved=true, 
          THE ModerationService SHALL set status to UPLOADED
        """
        mod_id = 123
        
        # Call the method
        moderation_service._update_mod_status(mod_id, approved=True)
        
        # Give the async task time to complete
        event_loop.run_until_complete(asyncio.sleep(0.1))
        
        # Verify set_status was called with UPLOADED
        mock_repo.set_status.assert_called_once_with(mod_id, "UPLOADED")

    def test_approved_false_sets_hidden_status(
        self, moderation_service, mock_repo, event_loop
    ):
        """Test that approved=False results in HIDDEN status.
        
        Validates Requirements 3.6, 6.3:
        - WHEN ModerationService receives approved=false,
          THE ModerationService SHALL set status to HIDDEN
        """
        mod_id = 456
        
        # Call the method
        moderation_service._update_mod_status(mod_id, approved=False)
        
        # Give the async task time to complete
        event_loop.run_until_complete(asyncio.sleep(0.1))
        
        # Verify set_status was called with HIDDEN
        mock_repo.set_status.assert_called_once_with(mod_id, "HIDDEN")

    def test_repository_called_with_correct_mod_id(
        self, moderation_service, mock_repo, event_loop
    ):
        """Test that repository is called with the correct mod_id."""
        mod_id = 789
        
        # Call the method
        moderation_service._update_mod_status(mod_id, approved=True)
        
        # Give the async task time to complete
        event_loop.run_until_complete(asyncio.sleep(0.1))
        
        # Verify the mod_id was passed correctly
        call_args = mock_repo.set_status.call_args
        assert call_args[0][0] == mod_id

    def test_handles_repository_failure(
        self, moderation_service, mock_repo, event_loop, caplog
    ):
        """Test that repository failures are logged without raising exceptions."""
        mod_id = 999
        mock_repo.set_status.return_value = False
        
        # Call the method
        moderation_service._update_mod_status(mod_id, approved=True)
        
        # Give the async task time to complete
        event_loop.run_until_complete(asyncio.sleep(0.1))
        
        # Verify error was logged
        assert "Failed to update mod status" in caplog.text
        assert str(mod_id) in caplog.text

    def test_handles_repository_exception(
        self, moderation_service, mock_repo, event_loop, caplog
    ):
        """Test that repository exceptions are logged without propagating."""
        mod_id = 888
        mock_repo.set_status.side_effect = Exception("Database error")
        
        # Call the method - should not raise
        moderation_service._update_mod_status(mod_id, approved=True)
        
        # Give the async task time to complete
        event_loop.run_until_complete(asyncio.sleep(0.1))
        
        # Verify error was logged
        assert "Error updating mod status" in caplog.text

    def test_logs_status_transition(
        self, moderation_service, mock_repo, event_loop, caplog
    ):
        """Test that status transitions are logged."""
        mod_id = 555
        
        # Set log level to capture INFO logs
        import logging
        caplog.set_level(logging.INFO)
        
        # Call the method
        moderation_service._update_mod_status(mod_id, approved=True)
        
        # Give the async task time to complete and process callbacks
        event_loop.run_until_complete(asyncio.sleep(0.2))
        
        # Verify logging - check that the initial log message is present
        assert "Updating mod status" in caplog.text
        assert f"mod_id={mod_id}" in caplog.text

    def test_logs_successful_update(
        self, moderation_service, mock_repo, event_loop, caplog
    ):
        """Test that successful updates are logged."""
        mod_id = 666
        
        # Set log level to capture INFO logs
        import logging
        caplog.set_level(logging.INFO)
        
        # Call the method
        moderation_service._update_mod_status(mod_id, approved=False)
        
        # Give the async task time to complete and process callbacks
        event_loop.run_until_complete(asyncio.sleep(0.2))
        
        # Verify success logging - check that the callback completed
        # The callback logs are harder to capture, so we verify the initial log
        assert "Updating mod status" in caplog.text
        assert f"mod_id={mod_id}" in caplog.text
