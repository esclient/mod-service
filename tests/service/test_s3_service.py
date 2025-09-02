from unittest.mock import MagicMock

import pytest

from modservice.s3_client import S3Client
from modservice.service.s3_service import S3Service


class TestS3Service:
    @pytest.fixture
    def mock_s3_client(self) -> MagicMock:
        client = MagicMock(spec=S3Client)
        client.generate_presigned_put_url = MagicMock()
        client.generate_presigned_get_url = MagicMock()
        client.upload_file = MagicMock()
        client.download_file = MagicMock()
        client.list_objects = MagicMock()
        return client

    @pytest.fixture
    def s3_service(self, mock_s3_client: MagicMock) -> S3Service:
        return S3Service(mock_s3_client)

    def test_generate_s3_key_basic(self, s3_service: S3Service) -> None:
        """Тест генерации базового S3 ключа"""
        author_id = 123
        filename = "test_mod.zip"

        s3_key = s3_service.generate_s3_key(author_id, filename)

        assert s3_key.startswith(f"{author_id}/")
        assert s3_key.endswith("_test_mod.zip")
        assert "_" in s3_key  # Должен содержать timestamp

    def test_generate_s3_key_with_mod_title(
        self, s3_service: S3Service
    ) -> None:
        """Тест генерации S3 ключа с заголовком мода"""
        author_id = 456
        filename = "awesome_mod.rar"
        mod_title = "Awesome Mod v2.0"

        s3_key = s3_service.generate_s3_key(author_id, filename, mod_title)

        assert s3_key.startswith(f"{author_id}/")
        assert s3_key.endswith("_Awesome_Mod_v2.0.rar")
        assert "_" in s3_key

    def test_generate_s3_key_special_characters(
        self, s3_service: S3Service
    ) -> None:
        """Тест очистки специальных символов в S3 ключе"""
        author_id = 789
        filename = "test@mod#.zip"
        mod_title = "Test@Mod# v1.0!"

        s3_key = s3_service.generate_s3_key(author_id, filename, mod_title)

        assert s3_key.startswith(f"{author_id}/")
        assert s3_key.endswith("_TestMod_v1.0.zip")
        assert "@" not in s3_key
        assert "#" not in s3_key
        assert "!" not in s3_key

    def test_generate_s3_key_unique(self, s3_service: S3Service) -> None:
        """Тест уникальности генерируемых S3 ключей"""
        author_id = 123
        filename = "test.zip"

        # Тест на уникальность по author_id и filename
        key1 = s3_service.generate_s3_key(author_id, filename)
        key2 = s3_service.generate_s3_key(author_id + 1, filename)
        key3 = s3_service.generate_s3_key(author_id, "different.zip")

        assert key1 != key2  # Разные author_id
        assert key1 != key3  # Разные filename
        assert key2 != key3  # Разные комбинации

    def test_generate_upload_url(
        self, s3_service: S3Service, mock_s3_client: MagicMock
    ) -> None:
        """Тест генерации URL для загрузки с автогенерацией ключа"""
        author_id = 123
        filename = "test_mod.zip"
        mod_title = "Test Mod"
        expiration = 7200
        content_type = "application/zip"

        expected_presigned_url = "https://example.com/presigned-url"
        mock_s3_client.generate_presigned_put_url.return_value = (
            expected_presigned_url
        )

        s3_key, presigned_url = s3_service.generate_upload_url(
            author_id, filename, mod_title, expiration, content_type
        )

        assert s3_key.startswith(f"{author_id}/")
        assert s3_key.endswith("_Test_Mod.zip")
        assert presigned_url == expected_presigned_url

        # Проверяем вызов generate_presigned_put_url
        mock_s3_client.generate_presigned_put_url.assert_called_once_with(
            s3_key=s3_key,
            expiration=expiration,
            content_type=content_type,
        )

    def test_generate_upload_url_for_key(
        self, s3_service: S3Service, mock_s3_client: MagicMock
    ) -> None:
        """Тест генерации URL для загрузки по существующему ключу"""
        s3_key = "123/456"  # формат author_id/mod_id
        expiration = 7200
        content_type = "application/zip"

        expected_presigned_url = "https://example.com/presigned-url"
        mock_s3_client.generate_presigned_put_url.return_value = (
            expected_presigned_url
        )

        presigned_url = s3_service.generate_upload_url_for_key(
            s3_key, expiration, content_type
        )

        assert presigned_url == expected_presigned_url

        # Проверяем вызов generate_presigned_put_url
        mock_s3_client.generate_presigned_put_url.assert_called_once_with(
            s3_key=s3_key,
            expiration=expiration,
            content_type=content_type,
        )

    def test_generate_download_url(
        self, s3_service: S3Service, mock_s3_client: MagicMock
    ) -> None:
        """Тест генерации URL для скачивания"""
        s3_key = "123/456"
        expiration = 3600

        expected_presigned_url = "https://example.com/download-url"
        mock_s3_client.generate_presigned_get_url.return_value = (
            expected_presigned_url
        )

        presigned_url = s3_service.generate_download_url(s3_key, expiration)

        assert presigned_url == expected_presigned_url

        # Проверяем вызов generate_presigned_get_url
        mock_s3_client.generate_presigned_get_url.assert_called_once_with(
            s3_key=s3_key,
            expiration=expiration,
        )

    def test_upload_file(
        self, s3_service: S3Service, mock_s3_client: MagicMock
    ) -> None:
        """Тест загрузки файла"""
        file_path = "/path/to/file.zip"
        s3_key = "123/456"

        mock_s3_client.upload_file.return_value = True

        result = s3_service.upload_file(file_path, s3_key)

        assert result is True
        mock_s3_client.upload_file.assert_called_once_with(file_path, s3_key)

    def test_download_file(
        self, s3_service: S3Service, mock_s3_client: MagicMock
    ) -> None:
        """Тест скачивания файла"""
        s3_key = "123/456"
        local_path = "/path/to/download.zip"

        mock_s3_client.download_file.return_value = True

        result = s3_service.download_file(s3_key, local_path)

        assert result is True
        mock_s3_client.download_file.assert_called_once_with(
            s3_key, local_path
        )

    def test_list_files(
        self, s3_service: S3Service, mock_s3_client: MagicMock
    ) -> None:
        """Тест получения списка файлов"""
        prefix = "123/"
        expected_files = [
            {"key": "123/456", "size": 1024},
            {"key": "123/789", "size": 2048},
        ]

        mock_s3_client.list_objects.return_value = expected_files

        result = s3_service.list_files(prefix)

        assert result == expected_files
        mock_s3_client.list_objects.assert_called_once_with(prefix)

    def test_generate_upload_url_auto_content_type(
        self, s3_service: S3Service, mock_s3_client: MagicMock
    ) -> None:
        """Тест автоопределения content-type"""
        author_id = 123
        filename = "archive.7z"

        expected_presigned_url = "https://example.com/presigned-url"
        mock_s3_client.generate_presigned_put_url.return_value = (
            expected_presigned_url
        )

        s3_key, presigned_url = s3_service.generate_upload_url(
            author_id, filename
        )

        # Проверяем, что content_type был автоматически определен
        mock_s3_client.generate_presigned_put_url.assert_called_once()
        args, kwargs = mock_s3_client.generate_presigned_put_url.call_args

        assert kwargs["s3_key"].startswith(f"{author_id}/")
        assert kwargs["expiration"] == 3600  # Значение по умолчанию
        # content_type может быть None или автоопределен

    def test_get_file_info_from_s3_key_mod_id_format(
        self, s3_service: S3Service
    ) -> None:
        """Тест парсинга S3 ключа в формате author_id/mod_id"""
        s3_key = "123/456"

        info = s3_service.get_file_info_from_s3_key(s3_key)

        assert info["author_id"] == 123
        assert info["mod_id"] == 456
        assert info["full_s3_key"] == s3_key

    def test_get_file_info_from_s3_key_timestamp_format(
        self, s3_service: S3Service
    ) -> None:
        """Тест парсинга S3 ключа в формате author_id/timestamp_filename"""
        s3_key = "123/20231201_120000_Test_Mod.zip"

        info = s3_service.get_file_info_from_s3_key(s3_key)

        assert info["author_id"] == 123
        assert info["timestamp"] == "20231201_120000"
        assert info["filename"] == "Test_Mod.zip"
        assert info["full_s3_key"] == s3_key

    def test_get_file_info_from_s3_key_invalid(
        self, s3_service: S3Service
    ) -> None:
        """Тест обработки невалидного S3-ключа"""
        s3_key = "invalid_key_format"

        info = s3_service.get_file_info_from_s3_key(s3_key)

        assert "error" in info
        assert info["full_s3_key"] == s3_key

    def test_get_file_info_from_s3_key_malformed(
        self, s3_service: S3Service
    ) -> None:
        """Тест обработки S3 ключа с некорректным author_id"""
        s3_key = "abc/not_a_number/file.zip"  # author_id не число

        info = s3_service.get_file_info_from_s3_key(s3_key)

        assert "error" in info
        assert info["full_s3_key"] == s3_key

    def test_sanitize_filename(self, s3_service: S3Service) -> None:
        """Тест очистки имени файла"""
        unsafe_filename = "test<>:|?*file.zip"

        safe_filename = s3_service._sanitize_filename(unsafe_filename)

        assert safe_filename == "test______file.zip"
        assert all(
            char not in safe_filename
            for char in ["<", ">", ":", "|", "?", "*"]
        )

    def test_sanitize_title(self, s3_service: S3Service) -> None:
        """Тест очистки заголовка мода"""
        unsafe_title = "My Awesome Mod! v2.0 @#$%"

        safe_title = s3_service._sanitize_title(unsafe_title)

        assert safe_title == "My_Awesome_Mod_v2.0"
        assert " " not in safe_title
        assert all(
            char not in safe_title for char in ["!", "@", "#", "$", "%"]
        )
