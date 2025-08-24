from unittest.mock import MagicMock

import pytest

from modservice.repository.repository import ModRepository
from modservice.service.s3_service import S3Service
from modservice.service.service import ModService


class TestModService:
    @pytest.fixture
    def mock_repo(self):
        return MagicMock(spec=ModRepository)

    @pytest.fixture
    def mock_s3_service(self):
        return MagicMock(spec=S3Service)

    @pytest.fixture
    def mod_service(self, mock_repo, mock_s3_service):
        return ModService(mock_repo, mock_s3_service)

    def test_generate_s3_key(self, mod_service, mock_s3_service):
        """Тест генерации S3-ключа через ModService"""
        author_id = 123
        filename = "test_mod.zip"
        mod_title = "Test Mod"
        expected_key = "mods/123/20231201_120000_Test_Mod.zip"

        mock_s3_service.generate_s3_key.return_value = expected_key

        result = mod_service.generate_s3_key(author_id, filename, mod_title)

        assert result == expected_key
        mock_s3_service.generate_s3_key.assert_called_once_with(
            author_id, filename, mod_title
        )

    def test_generate_upload_url(self, mod_service, mock_s3_service):
        """Тест генерации presigned URL через ModService"""
        author_id = 456
        filename = "awesome_mod.rar"
        mod_title = "Awesome Mod"
        expiration = 7200
        content_type = "application/x-rar-compressed"

        expected_s3_key = "mods/456/20231201_130000_Awesome_Mod.rar"
        expected_url = "https://example.com/presigned-url"

        mock_s3_service.generate_upload_url.return_value = (
            expected_s3_key,
            expected_url,
        )

        s3_key, presigned_url = mod_service.generate_upload_url(
            author_id, filename, mod_title, expiration, content_type
        )

        assert s3_key == expected_s3_key
        assert presigned_url == expected_url

        mock_s3_service.generate_upload_url.assert_called_once_with(
            author_id, filename, mod_title, expiration, content_type
        )

    def test_get_file_info_from_s3_key(self, mod_service, mock_s3_service):
        """Тест извлечения информации из S3-ключа через ModService"""
        s3_key = "mods/789/20231201_140000_Test_File.zip"
        expected_info = {
            "author_id": 789,
            "timestamp": "20231201_140000",
            "filename": "Test_File.zip",
            "full_s3_key": s3_key,
        }

        mock_s3_service.get_file_info_from_s3_key.return_value = expected_info

        result = mod_service.get_file_info_from_s3_key(s3_key)

        assert result == expected_info
        mock_s3_service.get_file_info_from_s3_key.assert_called_once_with(
            s3_key
        )

    def test_create_mod_delegates_to_repository(self, mod_service, mock_repo):
        """Тест, что create_mod делегирует вызов в репозиторий"""
        mod_title = "Test Mod"
        author_id = 123
        filename = "test.zip"
        description = "Test description"

        expected_result = (1, "test_s3_key", "test_upload_url")

        # Мокаем функцию create_mod из модуля create_mod
        with pytest.MonkeyPatch().context() as m:
            m.setattr(
                "modservice.service.service._create_mod",
                lambda *args: expected_result,
            )

            result = mod_service.create_mod(
                mod_title, author_id, filename, description
            )

            assert result == expected_result
