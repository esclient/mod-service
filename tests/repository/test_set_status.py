import textwrap

import pytest
from faker import Faker
from pytest_mock import MockerFixture

from modservice.repository.set_status import set_status


@pytest.mark.asyncio
async def test_set_status_returns_true_on_update(
    mocker: MockerFixture, faker: Faker
) -> None:
    conn = mocker.Mock()
    conn.execute = mocker.AsyncMock(return_value="UPDATE 1")
    acquire_cm = mocker.AsyncMock()
    acquire_cm.__aenter__.return_value = conn
    acquire_cm.__aexit__.return_value = None
    pool = mocker.Mock()
    pool.acquire.return_value = acquire_cm

    mod_id = faker.random_int(min=1, max=100000)
    status = "UPLOADED"

    result = await set_status(pool, mod_id, status)

    assert result is True
    expected_sql = """
        UPDATE mods
        SET status = $1
        WHERE id = $2
        """
    actual_sql = conn.execute.await_args.args[0]
    assert (
        textwrap.dedent(actual_sql).strip()
        == textwrap.dedent(expected_sql).strip()
    )
    assert conn.execute.await_args.args[1:] == (status, mod_id)


@pytest.mark.asyncio
async def test_set_status_returns_false_on_exception(
    mocker: MockerFixture, faker: Faker
) -> None:
    pool = mocker.Mock()
    pool.acquire.side_effect = RuntimeError("boom")

    result = await set_status(
        pool, faker.random_int(min=1, max=100000), "BANNED"
    )

    assert result is False
