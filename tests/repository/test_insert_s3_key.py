import textwrap

import pytest
from faker import Faker
from pytest_mock import MockerFixture

from modservice.repository.insert_s3_key import insert_s3_key


@pytest.mark.asyncio
async def test_insert_s3_key_updates_row(
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
    author_id = faker.random_int(min=1, max=100000)

    s3_key = await insert_s3_key(pool, mod_id, author_id)

    expected_key = f"{author_id}/{mod_id}"
    assert s3_key == expected_key

    actual_sql = conn.execute.await_args.args[0]
    expected_sql = """
        UPDATE mods
        SET s3_key = $1
        WHERE id = $2
        """
    assert (
        textwrap.dedent(actual_sql).strip()
        == textwrap.dedent(expected_sql).strip()
    )
    assert conn.execute.await_args.args[1:] == (expected_key, mod_id)
