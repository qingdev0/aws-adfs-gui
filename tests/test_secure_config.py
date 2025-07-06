"""Tests for the secure configuration module."""

import tempfile

import pytest
from aws_adfs_gui.models import ADFSCredentials, ConnectionSettings
from aws_adfs_gui.secure_config import SecureConfig, SecureConfigManager, SecureCredentials
from pydantic import SecretStr


class TestSecureCredentials:
    """Test secure credentials model."""

    def test_secure_credentials_creation(self):
        """Test creating secure credentials."""
        creds = SecureCredentials(username="test.user@company.com", adfs_host="adfs.company.com")
        assert creds.username == "test.user@company.com"
        assert creds.adfs_host == "adfs.company.com"
        assert creds.certificate_path is None

    def test_secure_credentials_with_certificate(self):
        """Test creating secure credentials with certificate path."""
        creds = SecureCredentials(
            username="test.user@company.com", adfs_host="adfs.company.com", certificate_path="/path/to/cert.pem"
        )
        assert creds.certificate_path == "/path/to/cert.pem"


class TestSecureConfig:
    """Test secure configuration model."""

    def test_secure_config_defaults(self):
        """Test secure config with default values."""
        config = SecureConfig()
        assert config.credentials is None
        assert config.connection_settings.timeout == 30
        assert config.connection_settings.retries == 3
        assert config.ui_settings == {}
        assert config.version == "1.0"

    def test_secure_config_with_values(self):
        """Test secure config with provided values."""
        settings = ConnectionSettings(timeout=60, retries=5)
        config = SecureConfig(connection_settings=settings, ui_settings={"theme": "dark"}, version="2.0")
        assert config.connection_settings.timeout == 60
        assert config.connection_settings.retries == 5
        assert config.ui_settings["theme"] == "dark"
        assert config.version == "2.0"


class TestSecureConfigManager:
    """Test secure configuration manager."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary configuration directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create a config manager with temporary directory."""
        return SecureConfigManager(config_dir=temp_config_dir)

    def test_config_manager_initialization(self, config_manager):
        """Test config manager initialization."""
        assert config_manager.config_dir.exists()
        assert config_manager.config_file.exists()
        assert config_manager.key_file.exists()

    def test_save_and_load_credentials(self, config_manager):
        """Test saving and loading credentials."""
        credentials = ADFSCredentials(
            username="test.user@company.com", password=SecretStr("test-password-123"), adfs_host="adfs.company.com"
        )

        # Save credentials
        success = config_manager.save_credentials(credentials)
        assert success is True

        # Load credentials
        loaded_creds = config_manager.load_credentials()
        assert loaded_creds is not None
        assert loaded_creds.username == "test.user@company.com"
        assert loaded_creds.password.get_secret_value() == "test-password-123"
        assert loaded_creds.adfs_host == "adfs.company.com"

    def test_delete_credentials(self, config_manager):
        """Test deleting credentials."""
        credentials = ADFSCredentials(
            username="test.user@company.com", password=SecretStr("test-password-123"), adfs_host="adfs.company.com"
        )

        # Save credentials
        config_manager.save_credentials(credentials)
        assert config_manager.has_credentials() is True

        # Delete credentials
        success = config_manager.delete_credentials()
        assert success is True
        assert config_manager.has_credentials() is False

    def test_connection_settings(self, config_manager):
        """Test saving and loading connection settings."""
        settings = ConnectionSettings(timeout=60, retries=5, no_sspi=False, env_mode=False)

        # Save settings
        success = config_manager.save_connection_settings(settings)
        assert success is True

        # Load settings
        loaded_settings = config_manager.get_connection_settings()
        assert loaded_settings.timeout == 60
        assert loaded_settings.retries == 5
        assert loaded_settings.no_sspi is False
        assert loaded_settings.env_mode is False

    def test_ui_settings(self, config_manager):
        """Test saving and loading UI settings."""
        ui_settings = {"theme": "dark", "export_format": "csv", "include_timestamps": False}

        # Save settings
        success = config_manager.save_ui_settings(ui_settings)
        assert success is True

        # Load settings
        loaded_settings = config_manager.get_ui_settings()
        assert loaded_settings["theme"] == "dark"
        assert loaded_settings["export_format"] == "csv"
        assert loaded_settings["include_timestamps"] is False

    def test_config_info(self, config_manager):
        """Test getting configuration information."""
        info = config_manager.get_config_info()
        assert "config_dir" in info
        assert "has_credentials" in info
        assert "credentials_valid" in info
        assert "version" in info
        assert "profile_count" in info

    def test_credentials_encryption(self, config_manager):
        """Test that credentials are properly encrypted."""
        credentials = ADFSCredentials(
            username="test.user@company.com", password=SecretStr("test-password-123"), adfs_host="adfs.company.com"
        )

        # Save credentials
        config_manager.save_credentials(credentials)

        # Check that password file contains encrypted data
        assert config_manager.password_file.exists()

        # Raw file content should not contain the plain password
        with open(config_manager.password_file, "rb") as f:
            encrypted_content = f.read()

        assert b"test-password-123" not in encrypted_content
        assert len(encrypted_content) > 0

    def test_config_file_permissions(self, config_manager):
        """Test that config files have proper permissions."""
        credentials = ADFSCredentials(
            username="test.user@company.com", password=SecretStr("test-password-123"), adfs_host="adfs.company.com"
        )

        # Save credentials
        config_manager.save_credentials(credentials)

        # Check file permissions (should be 600)
        import stat

        config_stat = config_manager.config_file.stat()
        config_mode = stat.filemode(config_stat.st_mode)
        assert config_mode == "-rw-------"

        key_stat = config_manager.key_file.stat()
        key_mode = stat.filemode(key_stat.st_mode)
        assert key_mode == "-rw-------"

        password_stat = config_manager.password_file.stat()
        password_mode = stat.filemode(password_stat.st_mode)
        assert password_mode == "-rw-------"
