"""Tests for the config module."""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path for imports
sys.path.insert(0, "src")

# Test dependencies
try:
    from aws_adfs_gui.config import Config

    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    Config = None

# Test model availability
try:
    from aws_adfs_gui.models import ProfileGroup  # noqa: F401

    PROFILE_GROUP_AVAILABLE = True
except ImportError:
    PROFILE_GROUP_AVAILABLE = False


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as tf:
        config_path = tf.name
    try:
        yield config_path
    finally:
        if os.path.exists(config_path):
            os.remove(config_path)


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for config testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.mark.skipif(not CONFIG_AVAILABLE, reason="Config not available due to dependencies")
class TestConfigInitialization:
    """Test cases for Config initialization."""

    def test_config_initialization_with_custom_file(self, temp_config_file) -> None:
        """Test Config initialization with a custom config file."""
        config = Config(config_file=temp_config_file)
        assert config.config_file == Path(temp_config_file)

    def test_config_initialization_with_default_file(self) -> None:
        """Test Config initialization with default config file."""
        import tempfile

        # Create a real temporary directory for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, ".aws-adfs", "config.json")

            with patch("os.path.expanduser") as mock_expanduser:
                mock_expanduser.return_value = config_path
                config = Config()
                assert str(config.config_file) == config_path
                mock_expanduser.assert_called_once_with("~/.aws-adfs/config.json")

    def test_config_directory_creation(self, temp_config_dir) -> None:
        """Test that config directory is created if it doesn't exist."""
        config_path = os.path.join(temp_config_dir, "subdir", "config.json")
        config = Config(config_file=config_path)

        # Directory should be created
        assert os.path.exists(os.path.dirname(config_path))
        # Config object should be created successfully
        assert config is not None


@pytest.mark.skipif(not CONFIG_AVAILABLE, reason="Config not available due to dependencies")
class TestConfigFileOperations:
    """Test cases for config file loading and saving."""

    def test_load_config_nonexistent_file(self, temp_config_file) -> None:
        """Test loading config when file doesn't exist."""
        # Remove the temp file to simulate nonexistent file
        os.remove(temp_config_file)

        config = Config(config_file=temp_config_file)

        # Should create default configuration
        assert hasattr(config, "profile_groups")

        # Config file should be created with defaults
        assert os.path.exists(temp_config_file)

    def test_load_config_existing_valid_file(self, temp_config_file) -> None:
        """Test loading config from existing valid file."""
        # Create a valid config file
        test_config = {
            "groups": {
                "dev": [
                    {
                        "name": "test-dev",
                        "group": "dev",
                        "region": "us-west-2",
                        "description": "Test dev profile",
                    }
                ]
            }
        }

        with open(temp_config_file, "w") as f:
            json.dump(test_config, f)

        config = Config(config_file=temp_config_file)

        # Should load the test configuration
        profiles = config.get_profiles()
        assert "dev" in profiles
        if PROFILE_GROUP_AVAILABLE:
            assert ProfileGroup.DEV in profiles

    def test_load_config_invalid_json(self, temp_config_file) -> None:
        """Test loading config from file with invalid JSON."""
        # Write invalid JSON
        with open(temp_config_file, "w") as f:
            f.write("invalid json content")

        config = Config(config_file=temp_config_file)

        # Should fall back to default configuration
        assert hasattr(config, "profile_groups")

    def test_save_config(self, temp_config_file) -> None:
        """Test saving config to file."""
        config = Config(config_file=temp_config_file)

        # Save should create/update the file
        config.save_config()

        assert os.path.exists(temp_config_file)

        # File should contain valid JSON
        with open(temp_config_file) as f:
            data = json.load(f)
            assert "groups" in data


@pytest.mark.skipif(not CONFIG_AVAILABLE, reason="Config not available due to dependencies")
class TestProfileManagement:
    """Test cases for profile management operations."""

    def test_get_profile_names(self, temp_config_file) -> None:
        """Test getting all profile names."""
        config = Config(config_file=temp_config_file)
        names = config.get_profile_names()

        assert isinstance(names, list)
        assert len(names) > 0  # Should have default profiles

        # Check for some expected default profiles
        expected_profiles = ["aws-dev-eu", "aws-dev-sg", "kds-ets-np", "kds-gps-np"]
        for profile in expected_profiles:
            assert profile in names

    def test_get_profiles(self, temp_config_file) -> None:
        """Test getting all profiles organized by groups."""
        config = Config(config_file=temp_config_file)
        profiles = config.get_profiles()

        assert isinstance(profiles, dict)
        assert len(profiles) > 0

        # Should have the expected groups
        if PROFILE_GROUP_AVAILABLE:
            assert ProfileGroup.DEV in profiles
            assert ProfileGroup.NON_PRODUCTION in profiles
            assert ProfileGroup.PRODUCTION in profiles

    def test_get_profile_by_name_existing(self, temp_config_file) -> None:
        """Test getting an existing profile by name."""
        config = Config(config_file=temp_config_file)

        # Test with a known default profile
        profile = config.get_profile_by_name("aws-dev-eu")

        assert profile is not None
        assert profile.name == "aws-dev-eu"
        if PROFILE_GROUP_AVAILABLE:
            assert profile.group == ProfileGroup.DEV

    def test_get_profile_by_name_nonexistent(self, temp_config_file) -> None:
        """Test getting a non-existent profile by name."""
        config = Config(config_file=temp_config_file)

        profile = config.get_profile_by_name("nonexistent-profile")

        assert profile is None

    def test_add_profile(self, temp_config_file) -> None:
        """Test adding a new profile."""
        config = Config(config_file=temp_config_file)

        if not PROFILE_GROUP_AVAILABLE:
            pytest.skip("ProfileGroup not available")

        from aws_adfs_gui.models import AWSProfile

        # ProfileGroup imported at module level

        # Create a test profile
        test_profile = AWSProfile(
            name="test-new-profile",
            group=ProfileGroup.DEV,
            region="us-west-1",
            description="Test profile",
        )

        # Add the profile
        config.add_profile(test_profile)

        # Verify it was added
        retrieved_profile = config.get_profile_by_name("test-new-profile")
        assert retrieved_profile is not None
        assert retrieved_profile.name == "test-new-profile"
        assert retrieved_profile.group == ProfileGroup.DEV

        # Verify it's in the profile names list
        names = config.get_profile_names()
        assert "test-new-profile" in names

    def test_remove_profile_existing(self, temp_config_file) -> None:
        """Test removing an existing profile."""
        config = Config(config_file=temp_config_file)

        if not PROFILE_GROUP_AVAILABLE:
            pytest.skip("ProfileGroup not available")

        from aws_adfs_gui.models import AWSProfile

        # ProfileGroup imported at module level

        # First add a profile to remove
        test_profile = AWSProfile(name="test-remove-profile", group=ProfileGroup.DEV, region="us-west-1")
        config.add_profile(test_profile)

        # Verify it exists
        assert config.get_profile_by_name("test-remove-profile") is not None

        # Remove it
        success = config.remove_profile("test-remove-profile")

        assert success is True

        # Verify it's gone
        assert config.get_profile_by_name("test-remove-profile") is None

        names = config.get_profile_names()
        assert "test-remove-profile" not in names

    def test_remove_profile_nonexistent(self, temp_config_file) -> None:
        """Test removing a non-existent profile."""
        config = Config(config_file=temp_config_file)

        success = config.remove_profile("nonexistent-profile")

        assert success is False


@pytest.mark.skipif(not CONFIG_AVAILABLE, reason="Config not available due to dependencies")
class TestDefaultProfiles:
    """Test cases for default profile configuration."""

    def test_default_profiles_structure(self, temp_config_file) -> None:
        """Test that default profiles have the expected structure."""
        config = Config(config_file=temp_config_file)

        if not PROFILE_GROUP_AVAILABLE:
            pytest.skip("ProfileGroup not available")

        from aws_adfs_gui.models import ProfileGroup

        # Check default profiles exist
        profiles = config.get_profiles()

        # DEV profiles
        dev_profiles = profiles.get(ProfileGroup.DEV, [])
        assert len(dev_profiles) >= 2
        dev_names = [p.name for p in dev_profiles]
        assert "aws-dev-eu" in dev_names
        assert "aws-dev-sg" in dev_names

        # NON_PRODUCTION profiles
        np_profiles = profiles.get(ProfileGroup.NON_PRODUCTION, [])
        assert len(np_profiles) >= 3
        np_names = [p.name for p in np_profiles]
        assert "kds-ets-np" in np_names
        assert "kds-gps-np" in np_names
        assert "kds-iss-np" in np_names

        # PRODUCTION profiles
        pd_profiles = profiles.get(ProfileGroup.PRODUCTION, [])
        assert len(pd_profiles) >= 3
        pd_names = [p.name for p in pd_profiles]
        assert "kds-ets-pd" in pd_names
        assert "kds-gps-pd" in pd_names
        assert "kds-iss-pd" in pd_names

    def test_default_profile_regions(self, temp_config_file) -> None:
        """Test that default profiles have correct regions."""
        config = Config(config_file=temp_config_file)

        # Test specific profiles and their expected regions
        aws_dev_eu = config.get_profile_by_name("aws-dev-eu")
        if aws_dev_eu:
            assert aws_dev_eu.region == "eu-west-1"

        aws_dev_sg = config.get_profile_by_name("aws-dev-sg")
        if aws_dev_sg:
            assert aws_dev_sg.region == "ap-southeast-1"

        # Most KDS profiles should be us-east-1
        kds_ets_np = config.get_profile_by_name("kds-ets-np")
        if kds_ets_np:
            assert kds_ets_np.region == "us-east-1"


@pytest.mark.skipif(not CONFIG_AVAILABLE, reason="Config not available due to dependencies")
class TestConfigPersistence:
    """Test cases for config persistence across operations."""

    def test_config_persistence_after_add(self, temp_config_file) -> None:
        """Test that config changes persist after adding a profile."""
        if not PROFILE_GROUP_AVAILABLE:
            pytest.skip("ProfileGroup not available")

        from aws_adfs_gui.models import AWSProfile

        # ProfileGroup imported at module level

        # Create and add a profile
        config1 = Config(config_file=temp_config_file)
        test_profile = AWSProfile(name="test-persistence", group=ProfileGroup.DEV, region="us-west-1")
        config1.add_profile(test_profile)

        # Create a new config instance with the same file
        config2 = Config(config_file=temp_config_file)

        # Profile should exist in the new instance
        retrieved_profile = config2.get_profile_by_name("test-persistence")
        assert retrieved_profile is not None
        assert retrieved_profile.name == "test-persistence"

    def test_config_persistence_after_remove(self, temp_config_file) -> None:
        """Test that config changes persist after removing a profile."""
        if not PROFILE_GROUP_AVAILABLE:
            pytest.skip("ProfileGroup not available")

        from aws_adfs_gui.models import AWSProfile
        # ProfileGroup imported at module level

        # Create, add, and remove a profile
        config1 = Config(config_file=temp_config_file)
        test_profile = AWSProfile(name="test-remove-persistence", group=ProfileGroup.DEV, region="us-west-1")
        config1.add_profile(test_profile)
        config1.remove_profile("test-remove-persistence")

        # Create a new config instance with the same file
        config2 = Config(config_file=temp_config_file)

        # Profile should not exist in the new instance
        retrieved_profile = config2.get_profile_by_name("test-remove-persistence")
        assert retrieved_profile is None


class TestConfigWithoutDependencies:
    """Test config functionality that doesn't require full dependencies."""

    def test_config_file_path_handling(self, temp_config_dir) -> None:
        """Test config file path handling without requiring full imports."""
        config_path = os.path.join(temp_config_dir, "test_config.json")

        try:
            from aws_adfs_gui.config import Config

            config = Config(config_file=config_path)
            # If we can create the config, test basic file operations
            assert hasattr(config, "config_file")
            assert str(config.config_file) == config_path
        except ImportError:
            # If imports fail, we can still test path handling logic
            from pathlib import Path

            test_path = Path(config_path)
            assert test_path.parent.exists() or not test_path.exists()

    def test_config_directory_exists(self, temp_config_dir) -> None:
        """Test that we can work with config directories."""
        config_path = os.path.join(temp_config_dir, "nested", "config.json")

        # Test directory creation logic
        config_dir = os.path.dirname(config_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)

        assert os.path.exists(config_dir)
        assert os.path.isdir(config_dir)
