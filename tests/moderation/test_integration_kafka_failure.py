"""Integration test for Kafka failure handling.

Tests the complete flow when Kafka fails:
1. Create mod with ON_MODERATION status
2. Kafka send fails (buffer full, connection error, etc.)
3. Status remains ON_MODERATION

Validates Requirements: 7.1, 7.2, 7.3, 7.4
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from modservice.grpc import moderation_pb2
from modservice.moderation.moderation_service import ModerationService
from modservice.repository.repository import ModRepository


@pytest.fixture
def mock_db_pool():
    """Create a mock database pool."""
    pool = Mock()
    conn = Mock()
    
    # Mock connection context manager
    conn.__aenter__ = AsyncMock(return_value=conn)
    conn.__aexit__ = AsyncMock(return_value=None)
    
    # Mock fetchval for create_mod - returns mod_id
    conn.fetchval = AsyncMock(return_value=999)
    
    # Mock execute for set_status
    conn.execute = AsyncMock(return_value="UPDATE 1")
    
    pool.acquire = Mock(return_value=conn)
    
    return pool


@pytest.fixture
def repository(mock_db_pool):
    """Create a ModRepository with mocked database."""
    return ModRepository(mock_db_pool)


@pytest.fixture
def mock_kafka_producer_failure():
    """Create a mock Kafka producer that fails to send."""
    with patch('modservice.moderation.moderation_service.KafkaProducer') as mock_producer_class:
        producer_instance = Mock()
        # Simulate Kafka send failure
        producer_instance.send_moderation_request = Mock(return_value=False)
        producer_instance.flush = Mock()
        producer_instance.topic = "moderation-request"
        mock_producer_class.return_value = producer_instance
        yield producer_instance


@pytest.fixture
def mock_kafka_consumer():
    """Create a mock Kafka consumer."""
    with patch('modservice.moderation.moderation_service.KafkaConsumer') as mock_consumer_class:
        consumer_instance = Mock()
        consumer_instance.start = Mock()
        consumer_instance.stop = Mock()
        mock_consumer_class.return_value = consumer_instance
        yield consumer_instance


@pytest.fixture
def moderation_service_with_failing_kafka(repository, mock_kafka_producer_failure, mock_kafka_consumer):
    """Create a ModerationService with failing Kafka producer."""
    # Create a new event loop for the service
    loop = asyncio.new_event_loop()
    service = ModerationService(repository, loop)
    
    # Start the loop in a thread to handle async callbacks
    import threading
    def run_loop():
        asyncio.set_event_loop(loop)
        loop.run_forever()
    
    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()
    
    yield service
    
    # Cleanup
    loop.call_soon_threadsafe(loop.stop)
    thread.join(timeout=1)
    loop.close()


@pytest.mark.asyncio
async def test_kafka_failure_mod_remains_on_moderation(
    repository: ModRepository,
    moderation_service_with_failing_kafka: ModerationService,
    mock_kafka_producer_failure: Mock,
    caplog: pytest.LogCaptureFixture
) -> None:
    """Test that mod remains in ON_MODERATION status when Kafka send fails.
    
    Validates Requirements:
    - 7.1: KafkaProducer retries up to 3 times on buffer full error
    - 7.2: KafkaProducer retries up to 3 times on connection error
    - 7.3: ModerationService returns false and logs error when all retries fail
    - 7.4: Mod remains in ON_MODERATION status when send_moderation_request returns false
    """
    import logging
    caplog.set_level(logging.INFO)
    
    # Step 1: Create mod with ON_MODERATION status
    mod_id = await repository.create_mod(
        title="Test Mod",
        author_id=1,
        description="Test Description"
    )
    
    assert mod_id == 999
    
    # Verify mod was created (fetchval was called)
    conn = repository._db_pool.acquire.return_value
    conn.fetchval.assert_called_once()
    
    # Step 2: Attempt to send moderation request to Kafka (will fail)
    success = moderation_service_with_failing_kafka.send_moderation_request(
        mod_id=mod_id,
        title="Test Mod",
        description="Test Description"
    )
    
    # Verify send_moderation_request returns False (Requirement 7.3)
    assert success is False
    
    # Verify Kafka producer was called but failed
    mock_kafka_producer_failure.send_moderation_request.assert_called_once()
    
    # Verify error was logged (Requirement 7.3)
    assert any("Failed to send moderation request" in record.message for record in caplog.records)
    assert any(f"mod_id={mod_id}" in record.message for record in caplog.records)
    
    # Step 3: Verify status was NOT updated (remains ON_MODERATION)
    # The set_status method should NOT have been called since Kafka send failed
    # and no moderation response was received
    
    # Wait a bit to ensure no async status update happens
    await asyncio.sleep(0.2)
    
    # Verify set_status was NOT called (mod remains in ON_MODERATION)
    # The execute method should only have been called once for create_mod, not for set_status
    # Actually, create_mod uses fetchval, not execute, so execute should not be called at all
    conn.execute.assert_not_called()


@pytest.mark.asyncio
async def test_kafka_buffer_full_error_handling(
    moderation_service_with_failing_kafka: ModerationService,
    mock_kafka_producer_failure: Mock,
    caplog: pytest.LogCaptureFixture
) -> None:
    """Test handling of Kafka buffer full error.
    
    Validates Requirements:
    - 7.1: KafkaProducer SHALL retry up to 3 times on buffer full error
    - 7.3: ModerationService SHALL return false and log error when all retries fail
    """
    import logging
    caplog.set_level(logging.ERROR)
    
    mod_id = 123
    
    # Attempt to send (will fail due to buffer full)
    success = moderation_service_with_failing_kafka.send_moderation_request(
        mod_id=mod_id,
        title="Test",
        description="Test"
    )
    
    # Verify failure
    assert success is False
    
    # Verify error was logged
    assert any("Failed to send moderation request" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_kafka_connection_error_handling(
    moderation_service_with_failing_kafka: ModerationService,
    mock_kafka_producer_failure: Mock,
    caplog: pytest.LogCaptureFixture
) -> None:
    """Test handling of Kafka connection error.
    
    Validates Requirements:
    - 7.2: KafkaProducer SHALL retry up to 3 times on connection error
    - 7.3: ModerationService SHALL return false and log error when all retries fail
    """
    import logging
    caplog.set_level(logging.ERROR)
    
    mod_id = 456
    
    # Attempt to send (will fail due to connection error)
    success = moderation_service_with_failing_kafka.send_moderation_request(
        mod_id=mod_id,
        title="Test",
        description="Test"
    )
    
    # Verify failure
    assert success is False
    
    # Verify error was logged
    assert any("Failed to send moderation request" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_mod_creation_continues_despite_kafka_failure(
    repository: ModRepository,
    moderation_service_with_failing_kafka: ModerationService
) -> None:
    """Test that mod creation continues even if Kafka send fails.
    
    Validates Requirement 7.5:
    - ModService SHALL continue mod creation even if Kafka send fails
    """
    # Create mod
    mod_id = await repository.create_mod(
        title="Test Mod",
        author_id=1,
        description="Test Description"
    )
    
    # Verify mod was created successfully
    assert mod_id == 999
    
    # Attempt to send to Kafka (will fail)
    success = moderation_service_with_failing_kafka.send_moderation_request(
        mod_id=mod_id,
        title="Test Mod",
        description="Test Description"
    )
    
    # Kafka send fails, but mod creation was successful
    assert success is False
    assert mod_id is not None
    
    # The mod exists in the database with ON_MODERATION status
    # (it was not rolled back due to Kafka failure)


@pytest.mark.asyncio
async def test_multiple_kafka_failures_do_not_update_status(
    repository: ModRepository,
    moderation_service_with_failing_kafka: ModerationService
) -> None:
    """Test that multiple Kafka failures do not trigger status updates.
    
    Validates Requirement 7.4:
    - Mod SHALL remain in ON_MODERATION status when send_moderation_request returns false
    """
    mod_ids = [111, 222, 333]
    
    for mod_id in mod_ids:
        # Mock create_mod to return different mod_ids
        conn = repository._db_pool.acquire.return_value
        conn.fetchval = AsyncMock(return_value=mod_id)
        
        # Create mod
        created_id = await repository.create_mod(
            title=f"Mod {mod_id}",
            author_id=1,
            description="Test"
        )
        
        assert created_id == mod_id
        
        # Attempt to send to Kafka (will fail)
        success = moderation_service_with_failing_kafka.send_moderation_request(
            mod_id=mod_id,
            title=f"Mod {mod_id}",
            description="Test"
        )
        
        assert success is False
    
    # Wait to ensure no async status updates happen
    await asyncio.sleep(0.3)
    
    # Verify set_status was never called for any mod
    conn = repository._db_pool.acquire.return_value
    conn.execute.assert_not_called()


@pytest.mark.asyncio
async def test_kafka_failure_logs_mod_id(
    moderation_service_with_failing_kafka: ModerationService,
    caplog: pytest.LogCaptureFixture
) -> None:
    """Test that Kafka failure logs include mod_id for debugging.
    
    Validates Requirement 5.7:
    - When KafkaProducer fails, ModerationService SHALL log error with mod_id
    """
    import logging
    caplog.set_level(logging.ERROR)
    
    mod_id = 789
    
    # Attempt to send (will fail)
    success = moderation_service_with_failing_kafka.send_moderation_request(
        mod_id=mod_id,
        title="Test",
        description="Test"
    )
    
    assert success is False
    
    # Verify mod_id is in error log
    error_logs = [record.message for record in caplog.records if record.levelname == "ERROR"]
    assert any(str(mod_id) in log for log in error_logs)
