"""Configuration management for AWS ADFS GUI application."""

import json
import os
from pathlib import Path

from .models import AWSProfile, ProfileGroup, ProfileGroups


class Config:
    """Application configuration manager."""

    def __init__(self, config_file: str | None = None):
        """Initialize configuration.

        Args:
            config_file: Path to configuration file. If None, uses default location.
        """
        if config_file is None:
            config_file = os.path.expanduser("~/.aws-adfs/config.json")

        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        # Default profile configuration based on user requirements
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

        self.load_config()

    def load_config(self) -> None:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    data = json.load(f)
                    self.profile_groups = ProfileGroups(**data)
            except (json.JSONDecodeError, KeyError):
                self.profile_groups = ProfileGroups(groups=self.default_profiles)
        else:
            self.profile_groups = ProfileGroups(groups=self.default_profiles)
            self.save_config()

    def save_config(self) -> None:
        """Save configuration to file."""
        with open(self.config_file, "w") as f:
            json.dump(self.profile_groups.model_dump(), f, indent=2)

    def get_profiles(self) -> dict[ProfileGroup, list[AWSProfile]]:
        """Get all profiles organized by groups."""
        return self.profile_groups.groups

    def get_profile_names(self) -> list[str]:
        """Get all profile names as a flat list."""
        names = []
        for profiles in self.profile_groups.groups.values():
            names.extend([profile.name for profile in profiles])
        return names

    def get_profile_by_name(self, name: str) -> AWSProfile | None:
        """Get a specific profile by name."""
        for profiles in self.profile_groups.groups.values():
            for profile in profiles:
                if profile.name == name:
                    return profile
        return None

    def add_profile(self, profile: AWSProfile) -> None:
        """Add a new profile."""
        if profile.group not in self.profile_groups.groups:
            self.profile_groups.groups[profile.group] = []
        self.profile_groups.groups[profile.group].append(profile)
        self.save_config()

    def remove_profile(self, name: str) -> bool:
        """Remove a profile by name."""
        for group in self.profile_groups.groups:
            profiles = self.profile_groups.groups[group]
            for i, profile in enumerate(profiles):
                if profile.name == name:
                    profiles.pop(i)
                    self.save_config()
                    return True
        return False


# Global configuration instance
config = Config()
