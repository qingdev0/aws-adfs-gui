"""Configuration management for AWS ADFS GUI."""

import json
from pathlib import Path

from pydantic import BaseModel, Field

from .models import AWSProfile, ProfileGroup


class ConfigModel(BaseModel):
    """Configuration model for the application."""

    profiles: dict[ProfileGroup, list[AWSProfile]] = Field(default_factory=dict)
    default_command: str = Field(default="aws s3 ls")
    max_history: int = Field(default=100, ge=1, le=1000)
    timeout: int = Field(default=30, ge=1, le=300)
    default_region: str = Field(default="us-east-1")


class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_dir: Path | None = None):
        self.config_dir = config_dir or Path.home() / ".aws" / "gui"
        self.config_file = self.config_dir / "config.json"
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

    def load_config(self) -> ConfigModel:
        """Load configuration from file."""
        if not self.config_file.exists():
            return self._create_default_config()

        try:
            with open(self.config_file, encoding="utf-8") as f:
                data = json.load(f)

            # Convert profile groups from strings to enums
            profiles = {}
            for group_str, profile_list in data.get("profiles", {}).items():
                group = ProfileGroup(group_str)
                profiles[group] = [AWSProfile(**profile) for profile in profile_list]

            return ConfigModel(
                profiles=profiles,
                default_command=data.get("default_command", "aws s3 ls"),
                max_history=data.get("max_history", 100),
                timeout=data.get("timeout", 30),
                default_region=data.get("default_region", "us-east-1"),
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error loading config: {e}")
            return self._create_default_config()

    def save_config(self, config: ConfigModel) -> None:
        """Save configuration to file."""
        # Convert profile groups to strings for JSON serialization
        profiles_dict = {}
        for group, profile_list in config.profiles.items():
            profiles_dict[group.value] = [profile.model_dump() for profile in profile_list]

        data = {
            "profiles": profiles_dict,
            "default_command": config.default_command,
            "max_history": config.max_history,
            "timeout": config.timeout,
            "default_region": config.default_region,
        }

        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _create_default_config(self) -> ConfigModel:
        """Create default configuration."""
        config = ConfigModel(profiles=self.default_profiles.copy())
        self.save_config(config)
        return config

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


# Global instance for compatibility
config = ConfigManager()
