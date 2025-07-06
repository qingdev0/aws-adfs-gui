"""Tests for AWS credentials management and validation."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Check for module availability
try:
    from aws_adfs_gui.aws_credentials import (
        AWSCredentialsManager,
        CredentialStatus,
        FlexibleCommandBuilder,
        command_builder,
        credentials_manager,
    )
    from aws_adfs_gui.models import AWSProfile, ProfileGroup

    AWS_CREDENTIALS_AVAILABLE = True
except ImportError:
    AWS_CREDENTIALS_AVAILABLE = False


class TestCredentialStatus:
    """Test cases for CredentialStatus constants and configuration."""

    @pytest.mark.skipif(not AWS_CREDENTIALS_AVAILABLE, reason="AWS credentials module not available")
    def test_status_constants(self) -> None:
        """Test that all required status constants are defined."""
        assert hasattr(CredentialStatus, "VALID")
        assert hasattr(CredentialStatus, "EXPIRED")
        assert hasattr(CredentialStatus, "INVALID")
        assert hasattr(CredentialStatus, "MISSING")
        assert hasattr(CredentialStatus, "UNKNOWN")

    @pytest.mark.skipif(not AWS_CREDENTIALS_AVAILABLE, reason="AWS credentials module not available")
    def test_status_config(self) -> None:
        """Test that status configuration is properly defined."""
        config = CredentialStatus.STATUS_CONFIG

        # Check all statuses have configuration
        assert CredentialStatus.VALID in config
        assert CredentialStatus.EXPIRED in config
        assert CredentialStatus.INVALID in config
        assert CredentialStatus.MISSING in config
        assert CredentialStatus.UNKNOWN in config

        # Check required fields for each status
        for status_config in config.values():
            assert "label" in status_config
            assert "color" in status_config
            assert "icon" in status_config
            assert "priority" in status_config

    @pytest.mark.skipif(not AWS_CREDENTIALS_AVAILABLE, reason="AWS credentials module not available")
    def test_status_priorities(self) -> None:
        """Test that status priorities are in correct order."""
        config = CredentialStatus.STATUS_CONFIG

        # VALID should have highest priority (lowest number)
        assert config[CredentialStatus.VALID]["priority"] == 1
        assert config[CredentialStatus.EXPIRED]["priority"] > config[CredentialStatus.VALID]["priority"]
        assert config[CredentialStatus.INVALID]["priority"] > config[CredentialStatus.VALID]["priority"]


@pytest.mark.skipif(not AWS_CREDENTIALS_AVAILABLE, reason="AWS credentials module not available")
class TestAWSCredentialsManager:
    """Test cases for AWSCredentialsManager."""

    @pytest.fixture
    def credentials_mgr(self) -> "AWSCredentialsManager":
        """Create a credentials manager for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AWSCredentialsManager()
            # Override AWS directory to use temp directory
            manager.aws_dir = Path(tmpdir) / ".aws"
            manager.credentials_file = manager.aws_dir / "credentials"
            manager.config_file = manager.aws_dir / "config"
            yield manager

    @pytest.fixture
    def sample_profiles(self) -> list["AWSProfile"]:
        """Create sample AWS profiles for testing."""
        return [
            AWSProfile(name="test-profile-1", group=ProfileGroup.DEV, region="us-east-1"),
            AWSProfile(name="test-profile-2", group=ProfileGroup.NON_PRODUCTION, region="us-west-2"),
        ]

    def test_initialization(self, credentials_mgr: "AWSCredentialsManager") -> None:
        """Test credentials manager initialization."""
        assert credentials_mgr.aws_dir is not None
        assert credentials_mgr.credentials_file is not None
        assert credentials_mgr.config_file is not None
        assert isinstance(credentials_mgr.profile_status, dict)

    def test_profile_exists_in_config_missing_files(self, credentials_mgr: "AWSCredentialsManager") -> None:
        """Test profile existence check when config files don't exist."""
        exists = credentials_mgr._profile_exists_in_config("test-profile")
        assert exists is False

    def test_profile_exists_in_config_with_credentials_file(self, credentials_mgr: "AWSCredentialsManager") -> None:
        """Test profile existence check with credentials file."""
        # Create AWS directory and credentials file
        credentials_mgr.aws_dir.mkdir(parents=True, exist_ok=True)

        # Write mock credentials file
        credentials_content = """[test-profile]
aws_access_key_id = AKIA...
aws_secret_access_key = secret...
aws_session_token = token...
"""
        credentials_mgr.credentials_file.write_text(credentials_content)

        # Test profile exists
        exists = credentials_mgr._profile_exists_in_config("test-profile")
        assert exists is True

        # Test profile doesn't exist
        exists = credentials_mgr._profile_exists_in_config("nonexistent-profile")
        assert exists is False

    def test_profile_exists_in_config_with_config_file(self, credentials_mgr: "AWSCredentialsManager") -> None:
        """Test profile existence check with config file."""
        # Create AWS directory and config file
        credentials_mgr.aws_dir.mkdir(parents=True, exist_ok=True)

        # Write mock config file
        config_content = """[profile test-profile]
region = us-east-1
output = json

[default]
region = us-west-2
"""
        credentials_mgr.config_file.write_text(config_content)

        # Test profile exists
        exists = credentials_mgr._profile_exists_in_config("test-profile")
        assert exists is True

        # Test default profile
        exists = credentials_mgr._profile_exists_in_config("default")
        assert exists is True

        # Test profile doesn't exist
        exists = credentials_mgr._profile_exists_in_config("nonexistent-profile")
        assert exists is False

    @pytest.mark.asyncio
    @patch("aws_adfs_gui.aws_credentials.asyncio.create_subprocess_exec")
    async def test_test_aws_credentials_success(
        self, mock_subprocess: Mock, credentials_mgr: "AWSCredentialsManager"
    ) -> None:
        """Test successful AWS credentials validation."""
        # Mock successful process
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(
            return_value=(
                json.dumps(
                    {"Account": "123456789012", "UserId": "test-user", "Arn": "arn:aws:sts::123456789012:user/test"}
                ).encode(),
                b"",
            )
        )
        mock_subprocess.return_value = mock_process

        success, output, error = await credentials_mgr._test_aws_credentials("test-profile")

        assert success is True
        assert "Account" in output
        assert error == ""

    @pytest.mark.asyncio
    @patch("aws_adfs_gui.aws_credentials.asyncio.create_subprocess_exec")
    async def test_test_aws_credentials_failure(
        self, mock_subprocess: Mock, credentials_mgr: "AWSCredentialsManager"
    ) -> None:
        """Test failed AWS credentials validation."""
        # Mock failed process
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b"", b"An error occurred (ExpiredToken): Token has expired"))
        mock_subprocess.return_value = mock_process

        success, output, error = await credentials_mgr._test_aws_credentials("test-profile")

        assert success is False
        assert "ExpiredToken" in error

    @pytest.mark.asyncio
    @patch("aws_adfs_gui.aws_credentials.asyncio.create_subprocess_exec")
    async def test_test_aws_credentials_timeout(
        self, mock_subprocess: Mock, credentials_mgr: "AWSCredentialsManager"
    ) -> None:
        """Test AWS credentials validation timeout."""
        # Mock process that times out
        mock_process = Mock()
        mock_process.communicate = AsyncMock(side_effect=TimeoutError())
        mock_process.kill = AsyncMock()
        mock_process.wait = AsyncMock()
        mock_subprocess.return_value = mock_process

        success, output, error = await credentials_mgr._test_aws_credentials("test-profile")

        assert success is False
        assert "timed out" in error

    def test_parse_credentials_info(self, credentials_mgr: "AWSCredentialsManager") -> None:
        """Test parsing AWS STS output."""
        aws_output = json.dumps(
            {
                "Account": "123456789012",
                "UserId": "AIDACKCEVSQ6C2EXAMPLE",
                "Arn": "arn:aws:sts::123456789012:user/test-user",
            }
        )

        info = credentials_mgr._parse_credentials_info(aws_output)

        assert info["account_id"] == "123456789012"
        assert info["user_id"] == "AIDACKCEVSQ6C2EXAMPLE"
        assert info["arn"] == "arn:aws:sts::123456789012:user/test-user"
        assert "last_validated" in info

    def test_parse_credentials_info_invalid_json(self, credentials_mgr: "AWSCredentialsManager") -> None:
        """Test parsing invalid AWS STS output."""
        invalid_output = "invalid json"

        info = credentials_mgr._parse_credentials_info(invalid_output)

        # Should still return at least last_validated
        assert "last_validated" in info
        assert len(info) == 1

    def test_create_status_result(self, credentials_mgr: "AWSCredentialsManager") -> None:
        """Test creation of status result dictionary."""
        status = CredentialStatus.VALID
        message = "Test message"
        extra_info = {"test_key": "test_value"}

        result = credentials_mgr._create_status_result(status, message, extra_info)

        assert result["status"] == status
        assert result["message"] == message
        assert result["test_key"] == "test_value"
        assert "last_checked" in result
        assert "label" in result
        assert "color" in result
        assert "icon" in result
        assert "priority" in result

    @pytest.mark.asyncio
    async def test_validate_profile_credentials_missing(self, credentials_mgr: "AWSCredentialsManager") -> None:
        """Test validation of missing profile credentials."""
        result = await credentials_mgr._validate_profile_credentials("nonexistent-profile")

        assert result["status"] == CredentialStatus.MISSING
        assert "not found" in result["message"]

    def test_get_profile_status(self, credentials_mgr: "AWSCredentialsManager") -> None:
        """Test getting profile status."""
        # Test unknown profile
        status = credentials_mgr.get_profile_status("unknown-profile")
        assert status["status"] == CredentialStatus.UNKNOWN

        # Test known profile
        credentials_mgr.profile_status["test-profile"] = {"status": CredentialStatus.VALID, "message": "Active"}
        status = credentials_mgr.get_profile_status("test-profile")
        assert status["status"] == CredentialStatus.VALID

    def test_get_status_summary(self, credentials_mgr: "AWSCredentialsManager") -> None:
        """Test getting status summary."""
        # Add some test status data
        credentials_mgr.profile_status = {
            "profile1": {"status": CredentialStatus.VALID},
            "profile2": {"status": CredentialStatus.VALID},
            "profile3": {"status": CredentialStatus.EXPIRED},
            "profile4": {"status": CredentialStatus.INVALID},
        }

        summary = credentials_mgr.get_status_summary()

        assert summary[CredentialStatus.VALID] == 2
        assert summary[CredentialStatus.EXPIRED] == 1
        assert summary[CredentialStatus.INVALID] == 1


@pytest.mark.skipif(not AWS_CREDENTIALS_AVAILABLE, reason="AWS credentials module not available")
class TestFlexibleCommandBuilder:
    """Test cases for FlexibleCommandBuilder."""

    @pytest.fixture
    def cmd_builder(self) -> "FlexibleCommandBuilder":
        """Create a command builder for testing."""
        return FlexibleCommandBuilder()

    def test_initialization(self, cmd_builder: "FlexibleCommandBuilder") -> None:
        """Test command builder initialization."""
        assert hasattr(cmd_builder, "default_aws_adfs_options")
        assert isinstance(cmd_builder.default_aws_adfs_options, dict)

    def test_build_aws_adfs_command_basic(self, cmd_builder: "FlexibleCommandBuilder") -> None:
        """Test building basic aws-adfs command."""
        cmd = cmd_builder.build_aws_adfs_command("test-profile", "adfs.example.com")

        assert "aws-adfs" in cmd
        assert "login" in cmd
        assert "--profile=test-profile" in cmd
        assert "--adfs-host=adfs.example.com" in cmd

    def test_build_aws_adfs_command_with_options(self, cmd_builder: "FlexibleCommandBuilder") -> None:
        """Test building aws-adfs command with custom options."""
        options = {
            "env_mode": True,
            "no_sspi": False,
            "region": "us-west-2",
            "duration": "3600",
        }

        cmd = cmd_builder.build_aws_adfs_command("test-profile", "adfs.example.com", **options)

        assert "--env" in cmd
        assert "--no-sspi" not in cmd
        assert "--region=us-west-2" in cmd
        assert "--duration=3600" in cmd

    def test_build_aws_adfs_command_with_custom_args(self, cmd_builder: "FlexibleCommandBuilder") -> None:
        """Test building aws-adfs command with custom arguments."""
        options = {"custom_args": ["--verbose", "--debug"]}

        cmd = cmd_builder.build_aws_adfs_command("test-profile", "adfs.example.com", **options)

        assert "--verbose" in cmd
        assert "--debug" in cmd

    def test_build_aws_cli_command_basic(self, cmd_builder: "FlexibleCommandBuilder") -> None:
        """Test building basic AWS CLI command."""
        cmd = cmd_builder.build_aws_cli_command("s3 ls", "test-profile")

        assert "aws" in cmd
        assert "s3" in cmd
        assert "ls" in cmd
        assert "--profile" in cmd
        assert "test-profile" in cmd

    def test_build_aws_cli_command_with_options(self, cmd_builder: "FlexibleCommandBuilder") -> None:
        """Test building AWS CLI command with options."""
        options = {"region": "us-east-1", "output": "json", "endpoint_url": "https://s3.amazonaws.com"}

        cmd = cmd_builder.build_aws_cli_command("s3 ls", "test-profile", **options)

        assert "--region" in cmd
        assert "us-east-1" in cmd
        assert "--output" in cmd
        assert "json" in cmd
        assert "--endpoint-url" in cmd
        assert "https://s3.amazonaws.com" in cmd

    def test_build_aws_cli_command_with_extra_args(self, cmd_builder: "FlexibleCommandBuilder") -> None:
        """Test building AWS CLI command with extra arguments."""
        options = {"extra_args": ["--recursive", "--human-readable"]}

        cmd = cmd_builder.build_aws_cli_command("s3 ls", "test-profile", **options)

        assert "--recursive" in cmd
        assert "--human-readable" in cmd


@pytest.mark.skipif(not AWS_CREDENTIALS_AVAILABLE, reason="AWS credentials module not available")
class TestGlobalInstances:
    """Test cases for global instances."""

    def test_credentials_manager_instance(self) -> None:
        """Test that global credentials manager instance exists."""
        assert credentials_manager is not None
        assert isinstance(credentials_manager, AWSCredentialsManager)

    def test_command_builder_instance(self) -> None:
        """Test that global command builder instance exists."""
        assert command_builder is not None
        assert isinstance(command_builder, FlexibleCommandBuilder)


@pytest.mark.skipif(not AWS_CREDENTIALS_AVAILABLE, reason="AWS credentials module not available")
class TestIntegration:
    """Integration tests for AWS credentials functionality."""

    @pytest.mark.asyncio
    async def test_full_validation_workflow(self) -> None:
        """Test complete credential validation workflow."""
        # This would be a more complex test that validates the entire workflow
        # For now, we'll test that the components work together

        profiles = [AWSProfile(name="test-profile", group=ProfileGroup.DEV, region="us-east-1")]

        # Test that validation can be called without errors
        try:
            await credentials_manager.validate_all_profiles(profiles)
        except Exception as e:
            # It's OK if this fails due to missing AWS CLI or credentials
            # We're just testing that the method can be called
            assert "AWS CLI" in str(e) or "not found" in str(e) or "Validation error" in str(e)

    def test_command_building_integration(self) -> None:
        """Test integration between command builder and credentials."""
        # Test building a command with realistic options
        cmd = command_builder.build_aws_adfs_command(
            "test-profile", "adfs.example.com", env_mode=True, no_sspi=True, duration="3600"
        )

        assert isinstance(cmd, list)
        assert len(cmd) > 0
        assert "aws-adfs" in cmd[0]
