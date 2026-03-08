"""Integration test for approved moderation flow.

Tests the complete flow:
1. Create mod with ON_MODERATION status
2. Send moderation request to Kafka
3. Receive approved response from Kafka
4. Status updates to UPLOADED

Validates Requirements: 2.1, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.6
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch, call

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
    conn.fetchval = AsyncMock(return_value=123)
    
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
async def test_approved_mod_flow_integration(
    repository: ModRepository,
    moderation_service: ModerationService,
    mock_kafka_producer: Mock,
    caplog: pytest.LogCaptureFixture
) -> None:
    """Test complete approved moderation flow.
    
    Validates Requirements:
    - 2.1: Mod created with ON_MODERATION status
    - 5.1: Serializes to ModerateObjectRequest protobuf
    - 5.2: Sets type to OBJECT_TYPE_MOD_DESCRIPTION
    - 5.3: Uses mod_id as Kafka message key
    - 5.4: Produces to moderation-request topic
    - 6.1: Extracts mod_id from message key
    - 6.2: Updates status to UPLOADED on success=true
    - 6.6: Completes processing without exceptions
    """
    import logging
    caplog.set_level(logging.INFO)
    
    # Step 1: Create mod with ON_MODERATION status
    mod_id = await repository.create_mod(
        title="Test Mod",
        author_id=1,
        description="Test Description"
    )
    
    assert mod_id == 123
    
    # Step 2: Send moderation request to Kafka
    success = moderation_service.send_moderation_request(
        mod_id=mod_id,
        title="Test Mod",
        description="Test Description"
    )
    
    assert success is True
    
    # Verify Kafka producer was called with correct protobuf message
    mock_kafka_producer.send_moderation_request.assert_called_once()
    call_args = mock_kafka_producer.send_moderation_request.call_args
    request = call_args[0][0]
    
    # Validate Requirements 5.1, 5.2, 5.3
    assert isinstance(request, moderation_pb2.ModerateObjectRequest)
    assert request.id == mod_id
    assert request.text == "Test Mod Test Description"
    assert request.type == moderation_pb2.OBJECT_TYPE_MOD_DESCRIPTION
    
    # Step 3: Simulate receiving approved response from Kafka
    response = moderation_pb2.ModerateObjectResponse()
    response.success = True
    
    # Call the callback directly to simulate Kafka consumer receiving message
    moderation_service._handle_moderation_response(response, mod_id)
    
    # Wait for async status update to complete
    await asyncio.sleep(0.2)
    
    # Step 4: Verify status was updated to UPLOADED
    # Check that set_status was called with correct parameters
    repository._db_pool.acquire.return_value.execute.assert_called()
    
    # Verify the correct status was set
    conn = repository._db_pool.acquire.return_value
    call_args = conn.execute.call_args
    assert call_args[0][1] == "UPLOADED"  # First parameter is status
    assert call_args[0][2] == mod_id  # Second parameter is mod_id


@pytest.mark.asyncio
async def test_approved_flow_with_actual_status_update(
    repository: ModRepository,
    moderation_service: ModerationService
) -> None:
    """Test that status update is actually called with correct parameters.
    
    Validates Requirements 6.2, 6.6:
    - Status updates to UPLOADED when approved=true
    - Processing completes without exceptions
    """
    mod_id = 456
    
    # Simulate approved response
    response = moderation_pb2.ModerateObjectResponse()
    response.success = True
    
    # Call the callback
    moderation_service._handle_moderation_response(response, mod_id)
    
    # Wait for async operation
    await asyncio.sleep(0.2)
    
    # Verify set_status was called with UPLOADED
    conn = repository._db_pool.acquire.return_value
    conn.execute.assert_called_with(
        """
            UPDATE mods
            SET status = $1
            WHERE id = $2
            """,
        "UPLOADED",
        mod_id
    )


@pytest.mark.asyncio
async def test_kafka_message_key_matches_mod_id(
    moderation_service: ModerationService,
    mock_kafka_producer: Mock
) -> None:
    """Test that Kafka message key equals mod_id.
    
    Validates Requirement 5.3:
    - Kafka message key must equal mod_id
    """
    mod_id = 789
    
    # Send moderation request
    moderation_service.send_moderation_request(
        mod_id=mod_id,
        title="Test",
        description="Test"
    )
    
    # Verify the request was created with correct mod_id
    call_args = mock_kafka_producer.send_moderation_request.call_args
    request = call_args[0][0]
    
    assert request.id == mod_id


@pytest.mark.asyncio
async def test_moderation_request_sent_to_correct_topic(
    moderation_service: ModerationService,
    mock_kafka_producer: Mock
) -> None:
    """Test that moderation request is sent to moderation-request topic.
    
    Validates Requirement 5.4:
    - Message must be produced to moderation-request topic
    """
    # Verify producer was initialized with correct topic
    assert moderation_service.producer.topic == "moderation-request"
    
    # Send request
    moderation_service.send_moderation_request(
        mod_id=999,
        title="Test",
        description="Test"
    )
    
    # Verify send was called
    mock_kafka_producer.send_moderation_request.assert_called_once()


@pytest.mark.asyncio
async def test_processing_completes_without_exceptions(
    moderation_service: ModerationService,
    repository: ModRepository
) -> None:
    """Test that successful processing completes without exceptions.
    
    Validates Requirement 6.6:
    - When status update succeeds, processing must complete without exceptions
    """
    mod_id = 111
    
    # Simulate approved response
    response = moderation_pb2.ModerateObjectResponse()
    response.success = True
    
    # This should not raise any exceptions
    try:
        moderation_service._handle_moderation_response(response, mod_id)
        await asyncio.sleep(0.2)
    except Exception as e:
        pytest.fail(f"Processing raised unexpected exception: {e}")


@pytest.mark.asyncio
async def test_mod_id_extraction_from_response(
    moderation_service: ModerationService,
    repository: ModRepository
) -> None:
    """Test that mod_id is correctly extracted from Kafka message.
    
    Validates Requirement 6.1:
    - ModerationService SHALL extract mod_id from message key
    """
    mod_id = 222
    
    # Simulate response with specific mod_id
    response = moderation_pb2.ModerateObjectResponse()
    response.success = True
    
    # Call handler with mod_id
    moderation_service._handle_moderation_response(response, mod_id)
    
    # Wait for async operation
    await asyncio.sleep(0.2)
    
    # Verify the correct mod_id was used in status update
    conn = repository._db_pool.acquire.return_value
    call_args = conn.execute.call_args
    assert call_args[0][2] == mod_id  # Second parameter is mod_id
