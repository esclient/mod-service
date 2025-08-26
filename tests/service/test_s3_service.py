from unittest.mock import MagicMock

import pytest

from modservice.s3_client import S3Client
from modservice.service.s3_service import S3Service


class TestS3Service:
    @pytest.fixture
    def mock_s3_client(self) -> MagicMock:
        client = MagicMock(spec=S3Client)
        client.generate_presigned_put_url = MagicMock()
        return client

    @pytest.fixture
    def s3_service(self, mock_s3_client: MagicMock) -> S3Service:
        return S3Service(mock_s3_client)

    def test_generate_s3_key_basic(self, s3_service: S3Service) -> None:
        author_id = 123
        filename = "test_mod.zip"

        s3_key = s3_service.generate_s3_key(author_id, filename)

        assert s3_key.startswith(f"{author_id}/")
        assert s3_key.endswith("_test_mod.zip")
        assert "_" in s3_key  # Должен содержать timestamp

    def test_generate_s3_key_with_mod_title(
        self, s3_service: S3Service
    ) -> None:
        author_id = 456
        filename = "awesome_mod.rar"
        mod_title = "Awesome Mod v2.0"

        s3_key = s3_service.generate_s3_key(author_id, filename, mod_title)

        assert s3_key.startswith(f"{author_id}/")
        assert s3_key.endswith("_Awesome_Mod_v2_0.rar")
        assert "_" in s3_key

    def test_generate_s3_key_special_characters(
        self, s3_service: S3Service
    ) -> None:
        author_id = 789
        filename = "test@mod#.zip"
        mod_title = "Test@Mod# v1.0!"

        s3_key = s3_service.generate_s3_key(author_id, filename, mod_title)

        assert s3_key.startswith(f"{author_id}/")
        assert s3_key.endswith("_TestMod_v1_0.zip")
        assert "@" not in s3_key
        assert "#" not in s3_key
        assert "!" not in s3_key

    def test_generate_s3_key_unique(self, s3_service: S3Service) -> None:
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
        author_id = 123
        filename = "test_mod.zip"
        mod_title = "Test Mod"
        expiration = 7200
        content_type = "application/zip"

        # Настраиваем mock
        expected_s3_key = "123/20231201_120000_Test_Mod.zip"
        expected_presigned_url = "https://example.com/presigned-url"

        # Мокаем generate_s3_key через patch
        with pytest.MonkeyPatch().context() as m:
            mock_generate_s3_key = MagicMock(return_value=expected_s3_key)
            m.setattr(s3_service, "generate_s3_key", mock_generate_s3_key)
            mock_s3_client.generate_presigned_put_url.return_value = (
                expected_presigned_url
            )

            s3_key, presigned_url = s3_service.generate_upload_url(
                author_id, filename, mod_title, expiration, content_type
            )

            assert s3_key == expected_s3_key
            assert presigned_url == expected_presigned_url

            # Проверяем вызов generate_presigned_put_url
            mock_s3_client.generate_presigned_put_url.assert_called_once_with(
                s3_key=expected_s3_key,
                expiration=expiration,
                content_type=content_type,
            )

    def test_generate_upload_url_auto_content_type(
        self, s3_service: S3Service, mock_s3_client: MagicMock
    ) -> None:
        author_id = 123
        filename = "archive.7z"

        expected_s3_key = "123/20231201_120000_archive.7z"
        expected_presigned_url = "https://example.com/presigned-url"

        # Мокаем generate_s3_key через patch
        with pytest.MonkeyPatch().context() as m:
            mock_generate_s3_key = MagicMock(return_value=expected_s3_key)
            m.setattr(s3_service, "generate_s3_key", mock_generate_s3_key)
            mock_s3_client.generate_presigned_put_url.return_value = (
                expected_presigned_url
            )

            s3_key, presigned_url = s3_service.generate_upload_url(
                author_id, filename
            )

            # Проверяем, что content_type был автоматически определен
            mock_s3_client.generate_presigned_put_url.assert_called_once_with(
                s3_key=expected_s3_key,
                expiration=3600,  # Значение по умолчанию
                content_type="application/x-7z-compressed",
            )

    def test_get_file_info_from_s3_key_valid(
        self, s3_service: S3Service
    ) -> None:
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
        s3_key = "abc/not_a_number/file.zip"  # author_id не число

        info = s3_service.get_file_info_from_s3_key(s3_key)

        assert "error" in info
        assert info["full_s3_key"] == s3_key
