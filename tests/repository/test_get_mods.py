import textwrap
from datetime import UTC

import pytest
from faker import Faker
from pytest_mock import MockerFixture

from modservice.repository.get_mods import get_mods


@pytest.mark.asyncio
async def test_get_mods_maps_rows(mocker: MockerFixture, faker: Faker) -> None:
    created_at_first = faker.date_time(tzinfo=UTC)
    created_at_second = faker.date_time(tzinfo=UTC)
    rows = [
        {
            "id": faker.random_int(min=1, max=100000),
            "author_id": faker.random_int(min=1, max=100000),
            "title": faker.sentence(nb_words=3),
            "description": faker.text(),
            "version": 1,
            "s3_key": faker.file_path(depth=2),
            "status": "UPLOADED",
            "created_at": created_at_first,
        },
        {
            "id": faker.random_int(min=1, max=100000),
            "author_id": faker.random_int(min=1, max=100000),
            "title": faker.sentence(nb_words=4),
            "description": faker.text(),
            "version": 2,
            "s3_key": faker.file_path(depth=2),
            "status": "BANNED",
            "created_at": created_at_second,
        },
    ]

    conn = mocker.Mock()
    conn.fetch = mocker.AsyncMock(return_value=rows)
    acquire_cm = mocker.AsyncMock()
    acquire_cm.__aenter__.return_value = conn
    acquire_cm.__aexit__.return_value = None
    pool = mocker.Mock()
    pool.acquire.return_value = acquire_cm

    result = await get_mods(pool)

    assert len(result) == 2
    assert result[0]["id"] == rows[0]["id"]
    assert result[0]["status"] == rows[0]["status"]
    assert result[0]["created_at"] == created_at_first
    assert result[1]["id"] == rows[1]["id"]
    assert result[1]["status"] == rows[1]["status"]

    expected_sql = """
        SELECT
            id,
            author_id,
            title,
            description,
            version,
            s3_key,
            status,
            created_at
        FROM mods
        ORDER BY created_at DESC
        """
    actual_sql = conn.fetch.await_args.args[0]
    assert (
        textwrap.dedent(actual_sql).strip()
        == textwrap.dedent(expected_sql).strip()
    )
