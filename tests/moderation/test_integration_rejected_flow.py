"""Integration test for rejected moderation flow.

Tests the complete flow:
1. Create mod with ON_MODERATION status
2. Send moderation request to Kafka
3. Receive rejected response from Kafka
4. Status updates to HIDDEN

Validates Requirements: 2.1, 6.1, 6.3, 6.6
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
    
    # Mock fetchval for create_mod
    conn.fetchval = AsyncMock(return_value=456)
    
    # Mock execute for set_status
    conn.execute = AsyncMock(return_value="UPDATE 1")
    
    pool.acquire = Mock(return_value=conn)
    
    return pool


@pytest.fixture
def repository(mock_db_pool):
    """Create a ModRepository with mocked database."""
    return ModRepository(mock_db_pool)


@pytest.fixture
def mock_kafka_producer():
    """Create a mock Kafka producer."""
    with patch('modservice.moderation.moderation_service.KafkaProducer') as mock_producer_class:
        producer_instance = Mock()
        producer_instance.send_moderation_request = Mock(return_value=True)
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
def moderation_service(repository, mock_kafka_producer, mock_kafka_consumer):
    """Create a ModerationService with mocked Kafka components."""
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
async def test_rejected_mod_flow_integration(
    repository: ModRepository,
    moderation_service: ModerationService,
    mock_kafka_producer: Mock,
    caplog: pytest.LogCaptureFixture
) -> None:
    """Test complete rejected moderation flow.
    
    Validates Requirements:
    - 2.1: Mod created with ON_MODERATION status
    - 6.1: Extracts mod_id from message key
    - 6.3: Updates status to HIDDEN on success=false
    - 6.6: Completes processing without exceptions
    """
    import logging
    caplog.set_level(logging.INFO)
    
    # Step 1: Create mod with ON_MODERATION status
    mod_id = await repository.create_mod(
        title="Rejected Mod",
        author_id=2,
        description="This mod will be rejected"
    )
    
    assert mod_id == 456
    
    # Step 2: Send moderation request to Kafka
    success = moderation_service.send_moderation_request(
        mod_id=mod_id,
        title="Rejected Mod",
        description="This mod will be rejected"
    )
    
    assert success is True
    
    # Verify Kafka producer was called
    mock_kafka_producer.send_moderation_request.assert_called_once()
    call_args = mock_kafka_producer.send_moderation_request.call_args
    request = call_args[0][0]
    
    # Validate request structure
    assert isinstance(request, moderation_pb2.ModerateObjectRequest)
    assert request.id == mod_id
    assert request.type == moderation_pb2.OBJECT_TYPE_MOD_DESCRIPTION
    
    # Step 3: Simulate receiving rejected response from Kafka
    response = moderation_pb2.ModerateObjectResponse()
    response.success = False
    
    # Call the callback directly to simulate Kafka consumer receiving message
    moderation_service._handle_moderation_response(response, mod_id)
    
    # Wait for async status update to complete
    await asyncio.sleep(0.2)
    
    # Step 4: Verify status was updated to HIDDEN
    # Check that set_status was called with correct parameters
    repository._db_pool.acquire.return_value.execute.assert_called()
    
    # Verify the correct status was set
    conn = repository._db_pool.acquire.return_value
    call_args = conn.execute.call_args
    assert call_args[0][1] == "HIDDEN"  # First parameter is status
    assert call_args[0][2] == mod_id  # Second parameter is mod_id


@pytest.mark.asyncio
async def test_rejected_flow_with_actual_status_update(
    repository: ModRepository,
    moderation_service: ModerationService
) -> None:
    """Test that status update is actually called with HIDDEN for rejected mods.
    
    Validates Requirements 6.3, 6.6:
    - Status updates to HIDDEN when success=false
    - Processing completes without exceptions
    """
    mod_id = 789
    
    # Simulate rejected response
    response = moderation_pb2.ModerateObjectResponse()
    response.success = False
    
    # Call the callback
    moderation_service._handle_moderation_response(response, mod_id)
    
    # Wait for async operation
    await asyncio.sleep(0.2)
    
    # Verify set_status was called with HIDDEN
    conn = repository._db_pool.acquire.return_value
    conn.execute.assert_called_with(
        """
            UPDATE mods
            SET status = $1
            WHERE id = $2
            """,
        "HIDDEN",
        mod_id
    )


@pytest.mark.asyncio
async def test_rejected_processing_completes_without_exceptions(
    moderation_service: ModerationService,
    repository: ModRepository
) -> None:
    """Test that rejected mod processing completes without exceptions.
    
    Validates Requirement 6.6:
    - When status update succeeds, processing must complete without exceptions
    """
    mod_id = 333
    
    # Simulate rejected response
    response = moderation_pb2.ModerateObjectResponse()
    response.success = False
    
    # This should not raise any exceptions
    try:
        moderation_service._handle_moderation_response(response, mod_id)
        await asyncio.sleep(0.2)
    except Exception as e:
        pytest.fail(f"Processing raised unexpected exception: {e}")


@pytest.mark.asyncio
async def test_mod_id_extraction_from_rejected_response(
    moderation_service: ModerationService,
    repository: ModRepository
) -> None:
    """Test that mod_id is correctly extracted from rejected Kafka message.
    
    Validates Requirement 6.1:
    - ModerationService SHALL extract mod_id from message key
    """
    mod_id = 555
    
    # Simulate rejected response with specific mod_id
    response = moderation_pb2.ModerateObjectResponse()
    response.success = False
    
    # Call handler with mod_id
    moderation_service._handle_moderation_response(response, mod_id)
    
    # Wait for async operation
    await asyncio.sleep(0.2)
    
    # Verify the correct mod_id was used in status update
    conn = repository._db_pool.acquire.return_value
    call_args = conn.execute.call_args
    assert call_args[0][2] == mod_id  # Second parameter is mod_id


@pytest.mark.asyncio
async def test_multiple_rejected_mods_processed_correctly(
    moderation_service: ModerationService,
    repository: ModRepository
) -> None:
    """Test that multiple rejected mods are processed correctly.
    
    Validates Requirements 6.1, 6.3, 6.6:
    - Each mod_id is extracted correctly
    - Each mod status is updated to HIDDEN
    - All processing completes without exceptions
    """
    mod_ids = [111, 222, 333]
    
    for mod_id in mod_ids:
        # Simulate rejected response
        response = moderation_pb2.ModerateObjectResponse()
        response.success = False
        
        # Process each rejection
        moderation_service._handle_moderation_response(response, mod_id)
    
    # Wait for all async operations
    await asyncio.sleep(0.3)
    
    # Verify all mods were updated to HIDDEN
    conn = repository._db_pool.acquire.return_value
    assert conn.execute.call_count == len(mod_ids)
    
    # Check that all calls used HIDDEN status
    for call in conn.execute.call_args_list:
        assert call[0][1] == "HIDDEN"
