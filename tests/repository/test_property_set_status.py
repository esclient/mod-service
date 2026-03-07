"""Property-based tests for mod status updates.

**Feature: mod-kafka-moderation**
"""

from unittest.mock import AsyncMock, Mock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from modservice.repository.set_status import set_status

# Valid mod_status values from the design
VALID_MOD_STATUSES = ["UPLOADING", "UPLOADED", "FAILED", "HIDDEN", "BANNED"]


class TestModStatusUpdateProperty:
    """Property-based tests for mod status updates.

    **Validates: Requirements 3.4, 7.4**
    """

    @given(
        mod_id=st.integers(min_value=1, max_value=1000000),
        status=st.sampled_from(VALID_MOD_STATUSES),
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_property_2_mod_status_can_be_updated(
        self,
        mod_id: int,
        status: str,
    ) -> None:
        """Property 2: Mod status can be updated.

        **Feature: mod-kafka-moderation, Property 2: For any existing mod and
        any valid mod_status value, calling set_status should successfully
        update the mod's status in the database and return True**

        For any existing mod_id and any valid mod_status value, calling set_status
        should successfully update the mod's status in the database and return True.
        """
        # Mock database pool and connection
        conn = Mock()
        conn.execute = AsyncMock(return_value="UPDATE 1")
        acquire_cm = AsyncMock()
        acquire_cm.__aenter__.return_value = conn
        acquire_cm.__aexit__.return_value = None
        pool = Mock()
        pool.acquire.return_value = acquire_cm

        # Call set_status
        result = await set_status(pool, mod_id, status)

        # Assert set_status returns True
        assert (
            result is True
        ), f"set_status should return True for existing mod {mod_id} with status {status}"

        # Assert the correct SQL was executed
        assert (
            conn.execute.await_count == 1
        ), "execute should be called exactly once"

        # Verify the SQL parameters
        call_args = conn.execute.await_args.args
        assert (
            len(call_args) == 3
        ), "execute should be called with 3 arguments (SQL, status, mod_id)"
        assert call_args[1] == status, f"Status parameter should be {status}"
        assert call_args[2] == mod_id, f"Mod ID parameter should be {mod_id}"
