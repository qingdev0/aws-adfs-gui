"""Secure configuration management for AWS ADFS GUI application."""

import json
import os
import secrets
from base64 import b64encode
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pydantic import BaseModel, Field, SecretStr

from .models import ADFSCredentials, AWSProfile, ConnectionSettings, ProfileGroup, ProfileGroups


class SecureCredentials(BaseModel):
    """Secure credentials model for encrypted storage."""

    username: str = Field(..., description="ADFS username")
    adfs_host: str = Field(..., description="ADFS server hostname")
    certificate_path: str | None = Field(None, description="Path to certificate file")
    # Password is stored separately, encrypted


class SecureConfig(BaseModel):
    """Secure configuration model."""

    credentials: SecureCredentials | None = Field(None, description="ADFS credentials (password encrypted separately)")
    connection_settings: ConnectionSettings = Field(
        default_factory=ConnectionSettings, description="Connection settings"
    )
    profile_groups: ProfileGroups = Field(default_factory=ProfileGroups, description="Profile groups")
    ui_settings: dict[str, Any] = Field(default_factory=dict, description="UI settings")
    version: str = Field(default="1.0", description="Config version")


class SecureConfigManager:
    """Secure configuration manager with encryption support."""

    def __init__(self, config_dir: str | None = None):
        """Initialize secure configuration manager.

        Args:
            config_dir: Configuration directory path. If None, uses ~/.aws/gui/
        """
        if config_dir is None:
            config_dir = os.path.expanduser("~/.aws/gui")

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.config_file = self.config_dir / "config.json"
        self.key_file = self.config_dir / ".key"
        self.password_file = self.config_dir / ".credentials"

        # Initialize encryption key
        self._init_encryption_key()

        # Default profile configuration
        self.default_profiles = {
            ProfileGroup.DEV: [
                AWSProfile(
                    name="aws-dev-eu",
                    group=ProfileGroup.DEV,
                    region="eu-west-1",
                    description="Development EU",
                ),
                AWSProfile(
                    name="aws-dev-sg",
                    group=ProfileGroup.DEV,
                    region="ap-southeast-1",
                    description="Development SG",
                ),
            ],
            ProfileGroup.NON_PRODUCTION: [
                AWSProfile(
                    name="kds-ets-np",
                    group=ProfileGroup.NON_PRODUCTION,
                    region="us-east-1",
                    description="KDS ETS Non-Production",
                ),
                AWSProfile(
                    name="kds-gps-np",
                    group=ProfileGroup.NON_PRODUCTION,
                    region="us-east-1",
                    description="KDS GPS Non-Production",
                ),
                AWSProfile(
                    name="kds-iss-np",
                    group=ProfileGroup.NON_PRODUCTION,
                    region="us-east-1",
                    description="KDS ISS Non-Production",
                ),
            ],
            ProfileGroup.PRODUCTION: [
                AWSProfile(
                    name="kds-ets-pd",
                    group=ProfileGroup.PRODUCTION,
                    region="us-east-1",
                    description="KDS ETS Production",
                ),
                AWSProfile(
                    name="kds-gps-pd",
                    group=ProfileGroup.PRODUCTION,
                    region="us-east-1",
                    description="KDS GPS Production",
                ),
                AWSProfile(
                    name="kds-iss-pd",
                    group=ProfileGroup.PRODUCTION,
                    region="us-east-1",
                    description="KDS ISS Production",
                ),
            ],
        }

        # Load existing configuration
        self.config = self._load_config()

    def _init_encryption_key(self) -> None:
        """Initialize or load encryption key."""
        if self.key_file.exists():
            # Load existing key
            try:
                with open(self.key_file, "rb") as f:
                    key_data = f.read()
                self._fernet = Fernet(key_data)
            except Exception:
                # If key is corrupted, generate new one
                self._generate_new_key()
        else:
            # Generate new key
            self._generate_new_key()

    def _generate_new_key(self) -> None:
        """Generate a new encryption key."""
        # Generate a random salt
        salt = secrets.token_bytes(16)

        # Use a default password for key derivation (in production, this should be user-provided)
        # For now, we'll use a machine-specific identifier
        import platform

        machine_id = f"{platform.node()}-{platform.machine()}-{platform.system()}"

        # Derive key from machine ID and salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = b64encode(kdf.derive(machine_id.encode()))

        # Store key securely
        self._fernet = Fernet(key)

        # Save key to file with restricted permissions
        with open(self.key_file, "wb") as f:
            f.write(key)

        # Set restrictive permissions (only readable by owner)
        os.chmod(self.key_file, 0o600)

    def _load_config(self) -> SecureConfig:
        """Load configuration from disk."""
        if not self.config_file.exists():
            # Create default configuration
            config = SecureConfig()
            # Set default profile groups
            try:
                config.profile_groups = ProfileGroups(groups=self.default_profiles)
            except Exception:
                # If model creation fails, use empty groups
                config.profile_groups = ProfileGroups(groups={})

            self._save_config(config)
            return config

        try:
            with open(self.config_file) as f:
                data = json.load(f)

            # Load configuration
            config = SecureConfig(**data)

            # Migrate old configuration if needed
            config = self._migrate_config(config)

            return config
        except Exception as e:
            print(f"Error loading config: {e}")
            # Return default config on error
            return SecureConfig()

    def _migrate_config(self, config: SecureConfig) -> SecureConfig:
        """Migrate configuration from older versions."""
        # Check if we need to migrate from old location
        old_config_path = Path(os.path.expanduser("~/.aws-adfs/config.json"))

        if old_config_path.exists() and not config.credentials:
            try:
                # Load old configuration
                with open(old_config_path) as f:
                    old_data = json.load(f)

                # Migrate profile groups if not already set
                if "groups" in old_data and not config.profile_groups.groups:
                    config.profile_groups = ProfileGroups(**old_data)

                print(f"Migrated configuration from {old_config_path}")
            except Exception as e:
                print(f"Error migrating old config: {e}")

        return config

    def _save_config(self, config: SecureConfig) -> None:
        """Save configuration to disk."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(config.model_dump(), f, indent=2)

            # Set restrictive permissions
            os.chmod(self.config_file, 0o600)
        except Exception as e:
            print(f"Error saving config: {e}")

    def save_credentials(self, credentials: ADFSCredentials) -> bool:
        """Save ADFS credentials securely.

        Args:
            credentials: ADFS credentials to save

        Returns:
            True if saved successfully
        """
        try:
            # Create secure credentials (without password)
            secure_creds = SecureCredentials(
                username=credentials.username,
                adfs_host=credentials.adfs_host,
                certificate_path=credentials.certificate_path,
            )

            # Encrypt password separately
            password_bytes = credentials.password.get_secret_value().encode("utf-8")
            encrypted_password = self._fernet.encrypt(password_bytes)

            # Save password to separate file
            with open(self.password_file, "wb") as f:
                f.write(encrypted_password)

            # Set restrictive permissions
            os.chmod(self.password_file, 0o600)

            # Update configuration
            self.config.credentials = secure_creds
            self._save_config(self.config)

            return True
        except Exception as e:
            print(f"Error saving credentials: {e}")
            return False

    def load_credentials(self) -> ADFSCredentials | None:
        """Load ADFS credentials securely.

        Returns:
            ADFS credentials if available, None otherwise
        """
        if not self.config.credentials or not self.password_file.exists():
            return None

        try:
            # Load encrypted password
            with open(self.password_file, "rb") as f:
                encrypted_password = f.read()

            # Decrypt password
            password_bytes = self._fernet.decrypt(encrypted_password)
            password = password_bytes.decode("utf-8")

            # Create credentials object
            return ADFSCredentials(
                username=self.config.credentials.username,
                password=SecretStr(password),
                adfs_host=self.config.credentials.adfs_host,
                certificate_path=self.config.credentials.certificate_path,
            )
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return None

    def delete_credentials(self) -> bool:
        """Delete stored credentials.

        Returns:
            True if deleted successfully
        """
        try:
            # Remove password file
            if self.password_file.exists():
                self.password_file.unlink()

            # Remove credentials from config
            self.config.credentials = None
            self._save_config(self.config)

            return True
        except Exception as e:
            print(f"Error deleting credentials: {e}")
            return False

    def save_connection_settings(self, settings: ConnectionSettings) -> bool:
        """Save connection settings.

        Args:
            settings: Connection settings to save

        Returns:
            True if saved successfully
        """
        try:
            self.config.connection_settings = settings
            self._save_config(self.config)
            return True
        except Exception as e:
            print(f"Error saving connection settings: {e}")
            return False

    def get_connection_settings(self) -> ConnectionSettings:
        """Get connection settings.

        Returns:
            Connection settings
        """
        return self.config.connection_settings

    def save_ui_settings(self, settings: dict[str, Any]) -> bool:
        """Save UI settings.

        Args:
            settings: UI settings to save

        Returns:
            True if saved successfully
        """
        try:
            self.config.ui_settings.update(settings)
            self._save_config(self.config)
            return True
        except Exception as e:
            print(f"Error saving UI settings: {e}")
            return False

    def get_ui_settings(self) -> dict[str, Any]:
        """Get UI settings.

        Returns:
            UI settings dictionary
        """
        return self.config.ui_settings

    def get_profile_groups(self) -> ProfileGroups:
        """Get profile groups.

        Returns:
            Profile groups
        """
        return self.config.profile_groups

    def has_credentials(self) -> bool:
        """Check if credentials are stored.

        Returns:
            True if credentials are stored
        """
        return self.config.credentials is not None and self.password_file.exists()

    def test_credentials(self) -> bool:
        """Test if stored credentials can be decrypted.

        Returns:
            True if credentials can be loaded successfully
        """
        try:
            credentials = self.load_credentials()
            return credentials is not None
        except Exception:
            return False

    def get_config_info(self) -> dict[str, Any]:
        """Get configuration information.

        Returns:
            Configuration information dictionary
        """
        return {
            "config_dir": str(self.config_dir),
            "has_credentials": self.has_credentials(),
            "credentials_valid": self.test_credentials(),
            "version": self.config.version,
            "profile_count": sum(len(profiles) for profiles in self.config.profile_groups.groups.values()),
        }


# Global secure configuration manager
secure_config_manager = SecureConfigManager()
