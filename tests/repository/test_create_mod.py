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
        VALUES ($1, $2, $3, $4, 'ON_MODERATION', NOW())
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


@pytest.mark.asyncio
async def test_repo_create_mod_returns_positive_mod_id(
    mocker: MockerFixture, faker: Faker
) -> None:
    """Test that create_mod returns a positive integer mod_id"""
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

    assert isinstance(result, int)
    assert result > 0
    assert result == mod_id


@pytest.mark.asyncio
async def test_repo_create_mod_sets_version_to_1(
    mocker: MockerFixture, faker: Faker
) -> None:
    """Test that create_mod sets version to 1 for new mods"""
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

    await repo.create_mod(title, author_id, description)

    # Verify version parameter is 1 (4th parameter in the SQL call)
    assert conn.fetchval.await_args.args[4] == 1


@pytest.mark.asyncio
async def test_repo_create_mod_uses_on_moderation_status(
    mocker: MockerFixture, faker: Faker
) -> None:
    """Test that create_mod uses ON_MODERATION as the initial status"""
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

    await repo.create_mod(title, author_id, description)

    # Verify the SQL contains ON_MODERATION status
    actual_sql = conn.fetchval.await_args.args[0]
    assert "ON_MODERATION" in actual_sql


@pytest.mark.asyncio
async def test_repo_create_mod_requires_all_parameters(
    mocker: MockerFixture, faker: Faker
) -> None:
    """Test that create_mod requires title, author_id, and description"""
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

    await repo.create_mod(title, author_id, description)

    # Verify all three parameters are passed to the SQL query
    call_args = conn.fetchval.await_args.args
    assert call_args[1] == author_id
    assert call_args[2] == title
    assert call_args[3] == description
