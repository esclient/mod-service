import textwrap

import pytest
from faker import Faker
from pytest_mock import MockerFixture

from modservice.repository.get_mod_s3_key import get_mod_s3_key


@pytest.mark.asyncio
async def test_get_mod_s3_key_returns_value(
    mocker: MockerFixture, faker: Faker
) -> None:
    conn = mocker.Mock()
    s3_key = f"{faker.random_int(min=1, max=100000)}/{faker.random_int(min=1, max=100000)}"
    conn.fetchval = mocker.AsyncMock(return_value=s3_key)
    acquire_cm = mocker.AsyncMock()
    acquire_cm.__aenter__.return_value = conn
    acquire_cm.__aexit__.return_value = None
    pool = mocker.Mock()
    pool.acquire.return_value = acquire_cm

    mod_id = faker.random_int(min=1, max=100000)
    result = await get_mod_s3_key(pool, mod_id)

    assert result == s3_key
    expected_sql = """
        SELECT s3_key
        FROM mods
        WHERE id = $1
        AND status = 'UPLOADED';
        """
    actual_sql = conn.fetchval.await_args.args[0]
    assert (
        textwrap.dedent(actual_sql).strip()
        == textwrap.dedent(expected_sql).strip()
    )
    assert conn.fetchval.await_args.args[1:] == (mod_id,)


@pytest.mark.asyncio
async def test_get_mod_s3_key_returns_zero_when_missing(
    mocker: MockerFixture, faker: Faker
) -> None:
    conn = mocker.Mock()
    conn.fetchval = mocker.AsyncMock(return_value=None)
    acquire_cm = mocker.AsyncMock()
    acquire_cm.__aenter__.return_value = conn
    acquire_cm.__aexit__.return_value = None
    pool = mocker.Mock()
    pool.acquire.return_value = acquire_cm

    mod_id = faker.random_int(min=1, max=100000)
    result = await get_mod_s3_key(pool, mod_id)

    assert result == 0
