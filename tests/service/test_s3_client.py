from __future__ import annotations

import asyncio
from collections.abc import Iterator
from contextlib import AbstractAsyncContextManager
from pathlib import Path
from types import TracebackType
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from pytest_mock import MockerFixture

from modservice.s3_client import S3Client


class _ValueContext[T](AbstractAsyncContextManager[T]):
    def __init__(self, value: T) -> None:
        self._value = value

    async def __aenter__(self) -> T:
        await asyncio.sleep(0)
        return self._value

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        await asyncio.sleep(0)
        return False


def _async_cm[T](value: T) -> AbstractAsyncContextManager[T]:
    return _ValueContext(value)


class _FakeBodyStream:
    def __init__(self, data: bytes):
        self._data = data

    async def __aenter__(self) -> _FakeBodyStream:
        await asyncio.sleep(0)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        await asyncio.sleep(0)
        return False

    async def read(self) -> bytes:
        await asyncio.sleep(0)
        return self._data


class _FakePaginator:
    def __init__(self, pages: list[dict[str, Any]]) -> None:
        self._pages: list[dict[str, Any]] = pages
        self.called_with: list[dict[str, Any]] = []

    def paginate(self, **kwargs: Any) -> _AsyncPageIterator:
        self.called_with.append(kwargs)

        return _AsyncPageIterator(self._pages)


class _AsyncPageIterator:
    def __init__(self, pages: list[dict[str, Any]]) -> None:
        self._pages: Iterator[dict[str, Any]] = iter(pages)

    def __aiter__(self) -> _AsyncPageIterator:
        return self

    async def __anext__(self) -> dict[str, Any]:
        await asyncio.sleep(0)
        try:
            return next(self._pages)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


@pytest.fixture
def s3_client_and_session(
    mocker: MockerFixture,
) -> tuple[S3Client, Mock]:
    session: Mock = mocker.Mock()
    mocker.patch("modservice.s3_client.aioboto3.Session", return_value=session)
    client = S3Client(
        access_key="access",
        secret_key="secret",
        endpoint_url="https://example.com",
        bucket_name="bucket",
        verify=True,
    )
    return client, session


def test_get_client_uses_session_client(
    s3_client_and_session: tuple[S3Client, Mock],
    mocker: MockerFixture,
) -> None:
    s3_client, session = s3_client_and_session
    underlying_client: Mock = mocker.Mock()
    session.client.return_value = _async_cm(underlying_client)

    context_manager: AbstractAsyncContextManager[Any] = s3_client.get_client()

    session.client.assert_called_once()
    assert session.client.call_args.args == ("s3",)
    assert session.client.call_args.kwargs == {
        "endpoint_url": "https://example.com",
        "aws_access_key_id": "access",
        "aws_secret_access_key": "secret",
        "config": s3_client.config,
        "verify": True,
        "region_name": "ru-central-1",
    }
    assert context_manager is session.client.return_value


@pytest.mark.asyncio
async def test_upload_file_puts_object(
    tmp_path: Path,
    s3_client_and_session: tuple[S3Client, Mock],
    mocker: MockerFixture,
) -> None:
    s3_client, _ = s3_client_and_session
    file_path = tmp_path / "payload.bin"
    payload = b"hello-world"
    file_path.write_bytes(payload)
    s3_key = "mods/payload.bin"

    storage_client: Mock = mocker.Mock()
    storage_client.put_object = AsyncMock(return_value=None)
    mocker.patch.object(
        s3_client, "get_client", return_value=_async_cm(storage_client)
    )

    result = await s3_client.upload_file(str(file_path), s3_key)

    assert result is True
    storage_client.put_object.assert_awaited_once_with(
        Bucket="bucket",
        Key=s3_key,
        Body=payload,
    )


@pytest.mark.asyncio
async def test_upload_file_returns_false_on_error(
    tmp_path: Path,
    s3_client_and_session: tuple[S3Client, Mock],
    mocker: MockerFixture,
) -> None:
    s3_client, _ = s3_client_and_session
    file_path = tmp_path / "payload.bin"
    file_path.write_bytes(b"boom")

    storage_client: Mock = mocker.Mock()
    storage_client.put_object = AsyncMock(side_effect=RuntimeError("boom"))
    mocker.patch.object(
        s3_client, "get_client", return_value=_async_cm(storage_client)
    )

    result = await s3_client.upload_file(str(file_path), "mods/payload.bin")

    assert result is False


@pytest.mark.asyncio
async def test_download_file_writes_to_disk(
    tmp_path: Path,
    s3_client_and_session: tuple[S3Client, Mock],
    mocker: MockerFixture,
) -> None:
    s3_client, _ = s3_client_and_session
    destination = tmp_path / "nested" / "file.bin"

    storage_client: Mock = mocker.Mock()
    storage_client.get_object = AsyncMock(
        return_value={"Body": _FakeBodyStream(b"downloaded")}
    )
    mocker.patch.object(
        s3_client, "get_client", return_value=_async_cm(storage_client)
    )

    result = await s3_client.download_file("mods/file.bin", str(destination))

    assert result is True
    assert destination.exists()
    assert destination.read_bytes() == b"downloaded"
    storage_client.get_object.assert_awaited_once_with(
        Bucket="bucket",
        Key="mods/file.bin",
    )


@pytest.mark.asyncio
async def test_generate_presigned_put_url_uses_client(
    s3_client_and_session: tuple[S3Client, Mock],
    mocker: MockerFixture,
) -> None:
    s3_client, _ = s3_client_and_session
    storage_client: Mock = mocker.Mock()
    storage_client.generate_presigned_url = AsyncMock(
        return_value="https://put-url"
    )
    mocker.patch.object(
        s3_client, "get_client", return_value=_async_cm(storage_client)
    )

    url = await s3_client.generate_presigned_put_url(
        "/mods/file.bin",
        expiration=600,
        content_type="application/zip",
    )

    assert url == "https://put-url"
    storage_client.generate_presigned_url.assert_awaited_once_with(
        "put_object",
        Params={
            "Bucket": "bucket",
            "Key": "mods/file.bin",
            "ContentType": "application/zip",
        },
        ExpiresIn=600,
    )


@pytest.mark.asyncio
async def test_generate_presigned_get_url_uses_client(
    s3_client_and_session: tuple[S3Client, Mock],
    mocker: MockerFixture,
) -> None:
    s3_client, _ = s3_client_and_session
    storage_client: Mock = mocker.Mock()
    storage_client.generate_presigned_url = AsyncMock(
        return_value="https://get-url"
    )
    mocker.patch.object(
        s3_client, "get_client", return_value=_async_cm(storage_client)
    )

    url = await s3_client.generate_presigned_get_url(
        "/mods/file.bin",
        expiration=1200,
    )

    assert url == "https://get-url"
    storage_client.generate_presigned_url.assert_awaited_once_with(
        "get_object",
        Params={
            "Bucket": "bucket",
            "Key": "mods/file.bin",
        },
        ExpiresIn=1200,
    )


@pytest.mark.asyncio
async def test_list_objects_collects_all_pages(
    s3_client_and_session: tuple[S3Client, Mock],
    mocker: MockerFixture,
) -> None:
    s3_client, _ = s3_client_and_session
    pages = [
        {
            "Contents": [
                {
                    "Key": "mods/1",
                    "Size": 10,
                    "LastModified": "ts1",
                    "ETag": "tag1",
                }
            ]
        },
        {
            "Contents": [
                {
                    "Key": "mods/2",
                    "Size": 20,
                    "LastModified": "ts2",
                    "ETag": "tag2",
                }
            ]
        },
    ]

    storage_client: Mock = mocker.Mock()
    paginator = _FakePaginator(pages)
    storage_client.get_paginator.return_value = paginator
    mocker.patch.object(
        s3_client, "get_client", return_value=_async_cm(storage_client)
    )

    result = await s3_client.list_objects("mods/")

    assert result == [
        {"key": "mods/1", "size": 10, "last_modified": "ts1", "etag": "tag1"},
        {"key": "mods/2", "size": 20, "last_modified": "ts2", "etag": "tag2"},
    ]
    storage_client.get_paginator.assert_called_once_with("list_objects_v2")
    assert paginator.called_with == [{"Bucket": "bucket", "Prefix": "mods/"}]


def test_time_format_formats_values(
    s3_client_and_session: tuple[S3Client, Mock],
) -> None:
    s3_client, _ = s3_client_and_session

    assert s3_client.time_format(3661) == "01h 01m 01s"
    assert s3_client.time_format(61) == "01m 01s"
    assert s3_client.time_format(5) == "05s"
    assert s3_client.time_format(0) == "-"
    assert s3_client.time_format(None) == "-"
