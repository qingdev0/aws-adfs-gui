"""Secure configuration management with encryption support."""

import json
import os
import platform
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet
from pydantic import BaseModel, Field, SecretStr

from .models import AWSProfile, ProfileGroup


class SecureCredentials(BaseModel):
    """Secure credentials model with encryption."""

    username: str = Field(..., description="ADFS username")
    password: SecretStr = Field(..., description="ADFS password")
    domain: str = Field(..., description="ADFS domain")
    adfs_url: str = Field(..., description="ADFS URL")
    certificate_path: str | None = Field(None, description="Path to certificate file")


class SecureConfig(BaseModel):
    """Secure configuration model."""

    profiles: dict[ProfileGroup, list[AWSProfile]] = Field(default_factory=dict)
    credentials: SecureCredentials | None = Field(None, description="Encrypted credentials")
    default_command: str = Field(default="aws s3 ls")
    max_history: int = Field(default=100, ge=1, le=1000)
    timeout: int = Field(default=30, ge=1, le=300)
    default_region: str = Field(default="us-east-1")


class SecureConfigManager:
    """Manages secure configuration with encryption."""

    def __init__(self, config_dir: Path | None = None):
        self.config_dir = config_dir or Path.home() / ".aws" / "gui"
        self.config_file = self.config_dir / "secure_config.json"
        self.key_file = self.config_dir / "encryption.key"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Initialize default profiles
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

        # Initialize encryption
        self._fernet: Fernet | None = None
        self._ensure_encryption_key()

    def _ensure_encryption_key(self) -> None:
        """Ensure encryption key exists."""
        if not self.key_file.exists():
            self._generate_encryption_key()
        self._fernet = Fernet(self._load_encryption_key())

    def _generate_encryption_key(self) -> None:
        """Generate a new encryption key."""
        key = Fernet.generate_key()
        try:
            with open(self.key_file, "wb") as f:
                f.write(key)

            # Set secure permissions on Unix-like systems
            if platform.system() != "Windows":
                os.chmod(self.key_file, 0o600)
        except OSError as e:
            raise RuntimeError(f"Failed to generate encryption key: {e}") from e

    def _load_encryption_key(self) -> bytes:
        """Load encryption key from file."""
        try:
            with open(self.key_file, "rb") as f:
                return f.read()
        except OSError as e:
            raise RuntimeError(f"Failed to load encryption key: {e}") from e

    def _encrypt_data(self, data: str) -> str:
        """Encrypt data using Fernet."""
        if self._fernet is None:
            raise RuntimeError("Encryption not initialized")

        try:
            encrypted = self._fernet.encrypt(data.encode())
            return encrypted.decode()
        except Exception as e:
            raise RuntimeError(f"Failed to encrypt data: {e}") from e

    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data using Fernet."""
        if self._fernet is None:
            raise RuntimeError("Encryption not initialized")

        try:
            decrypted = self._fernet.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            raise RuntimeError(f"Failed to decrypt data: {e}") from e

    def save_config(self, config: SecureConfig) -> None:
        """Save secure configuration to file."""
        try:
            # Prepare data for serialization
            data = {
                "profiles": self._serialize_profiles(config.profiles),
                "default_command": config.default_command,
                "max_history": config.max_history,
                "timeout": config.timeout,
                "default_region": config.default_region,
            }

            # Encrypt credentials if present
            if config.credentials:
                credentials_data = {
                    "username": config.credentials.username,
                    "password": config.credentials.password.get_secret_value(),
                    "domain": config.credentials.domain,
                    "adfs_url": config.credentials.adfs_url,
                    "certificate_path": config.credentials.certificate_path,
                }
                data["credentials"] = self._encrypt_data(json.dumps(credentials_data))

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            raise RuntimeError(f"Failed to save secure config: {e}") from e

    def load_config(self) -> SecureConfig:
        """Load secure configuration from file."""
        if not self.config_file.exists():
            return self._create_default_config()

        try:
            with open(self.config_file, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Error loading secure config: {e}")
            return self._create_default_config()

        # Deserialize profiles
        profiles = self._deserialize_profiles(data.get("profiles", {}))

        # Decrypt credentials if present
        credentials = None
        if "credentials" in data:
            try:
                credentials_data = json.loads(self._decrypt_data(data["credentials"]))
                credentials = SecureCredentials(
                    username=credentials_data["username"],
                    password=SecretStr(credentials_data["password"]),
                    domain=credentials_data["domain"],
                    adfs_url=credentials_data["adfs_url"],
                    certificate_path=credentials_data.get("certificate_path"),
                )
            except Exception as e:
                print(f"Error decrypting credentials: {e}")

        return SecureConfig(
            profiles=profiles,
            credentials=credentials,
            default_command=data.get("default_command", "aws s3 ls"),
            max_history=data.get("max_history", 100),
            timeout=data.get("timeout", 30),
            default_region=data.get("default_region", "us-east-1"),
        )

    def _serialize_profiles(self, profiles: dict[ProfileGroup, list[AWSProfile]]) -> dict[str, list[dict]]:
        """Serialize profiles for JSON storage."""
        result = {}
        for group, profile_list in profiles.items():
            result[group.value] = [profile.model_dump() for profile in profile_list]
        return result

    def _deserialize_profiles(self, profiles_data: dict[str, list[dict]]) -> dict[ProfileGroup, list[AWSProfile]]:
        """Deserialize profiles from JSON data."""
        result = {}
        for group_str, profile_list in profiles_data.items():
            try:
                group = ProfileGroup(group_str)
                result[group] = [AWSProfile(**profile) for profile in profile_list]
            except ValueError as e:
                print(f"Error deserializing profile group {group_str}: {e}")
        return result

    def _create_default_config(self) -> SecureConfig:
        """Create default secure configuration."""
        config = SecureConfig(profiles=self.default_profiles.copy())
        self.save_config(config)
        return config

    def save_credentials(self, credentials: SecureCredentials) -> None:
        """Save encrypted credentials."""
        config = self.load_config()
        config.credentials = credentials
        self.save_config(config)

    def load_credentials(self) -> SecureCredentials | None:
        """Load decrypted credentials."""
        config = self.load_config()
        return config.credentials

    def has_credentials(self) -> bool:
        """Check if credentials are stored."""
        config = self.load_config()
        return config.credentials is not None

    def clear_credentials(self) -> None:
        """Clear stored credentials."""
        config = self.load_config()
        config.credentials = None
        self.save_config(config)

    def get_profiles_by_group(self, group: ProfileGroup) -> list[AWSProfile]:
        """Get profiles for a specific group."""
        config = self.load_config()
        return config.profiles.get(group, [])

    def get_all_profiles(self) -> list[AWSProfile]:
        """Get all profiles."""
        config = self.load_config()
        all_profiles = []
        for profile_list in config.profiles.values():
            all_profiles.extend(profile_list)
        return all_profiles

    def update_profiles(self, profiles: dict[ProfileGroup, list[AWSProfile]]) -> None:
        """Update profiles in configuration."""
        config = self.load_config()
        config.profiles = profiles
        self.save_config(config)

    def get_config_summary(self) -> dict[str, Any]:
        """Get configuration summary for display."""
        config = self.load_config()

        # Get available profile groups
        profile_groups = [group.value for group in ProfileGroup]

        return {
            "total_profiles": len(self.get_all_profiles()),
            "profile_groups": profile_groups,
            "has_credentials": config.credentials is not None,
            "default_command": config.default_command,
            "timeout": config.timeout,
            "max_history": config.max_history,
        }


# Global instance for compatibility
secure_config_manager = SecureConfigManager()
