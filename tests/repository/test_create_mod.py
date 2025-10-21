import textwrap

import pytest
from faker import Faker
from pytest_mock import MockerFixture

from modservice.repository.repository import ModRepository


@pytest.mark.asyncio
async def test_repo_create_mod_inserts_row(
    mocker: MockerFixture, faker: Faker
) -> None:
    mod_id = faker.random_int(min=1, max=100000)
    conn = mocker.Mock()
    conn.fetchval = mocker.AsyncMock(return_value=mod_id)
    acquire_cm = mocker.AsyncMock()
    acquire_cm.__aenter__.return_value = conn
    acquire_cm.__aexit__.return_value = None
    pool = mocker.Mock()
    pool.acquire.return_value = acquire_cm

    repo = ModRepository(pool)

    title = faker.sentence(nb_words=3)
    author_id = faker.random_int(min=1, max=100000)
    description = faker.text()

    result = await repo.create_mod(title, author_id, description)

    assert result == mod_id
    expected_sql = """
        INSERT INTO mods (author_id, title, description, version, status, created_at)
        VALUES ($1, $2, $3, $4, 'UPLOADING', NOW())
        RETURNING id
        """
    actual_sql = conn.fetchval.await_args.args[0]
    assert (
        textwrap.dedent(actual_sql).strip()
        == textwrap.dedent(expected_sql).strip()
    )
    assert conn.fetchval.await_args.args[1:] == (
        author_id,
        title,
        description,
        1,
    )
    pool.acquire.assert_called_once()
