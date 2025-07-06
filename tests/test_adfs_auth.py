"""Tests for the ADFS authentication module."""

import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, "src")

# Test availability of ADFS authenticator
try:
    from aws_adfs_gui.adfs_auth import ADFSAuthenticator

    ADFS_AUTH_AVAILABLE = True
except ImportError:
    ADFS_AUTH_AVAILABLE = False


class TestADFSAuthenticatorBasic:
    """Test basic ADFSAuthenticator functionality."""

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    def test_adfs_authenticator_initialization(self) -> None:
        """Test ADFSAuthenticator initialization."""
        authenticator = ADFSAuthenticator()

        assert hasattr(authenticator, "authenticated_profiles")
        assert isinstance(authenticator.authenticated_profiles, dict)
        assert len(authenticator.authenticated_profiles) == 0

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    def test_is_authenticated_empty(self) -> None:
        """Test is_authenticated when no profiles are authenticated."""
        authenticator = ADFSAuthenticator()

        result = authenticator.is_authenticated("test-profile")

        assert result is False

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    def test_is_authenticated_true(self) -> None:
        """Test is_authenticated when profile is authenticated."""
        authenticator = ADFSAuthenticator()
        authenticator.authenticated_profiles["test-profile"] = True

        result = authenticator.is_authenticated("test-profile")

        assert result is True

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    def test_is_authenticated_false(self) -> None:
        """Test is_authenticated when profile authentication failed."""
        authenticator = ADFSAuthenticator()
        authenticator.authenticated_profiles["test-profile"] = False

        result = authenticator.is_authenticated("test-profile")

        assert result is False

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    def test_logout_single_profile(self) -> None:
        """Test logging out a single profile."""
        authenticator = ADFSAuthenticator()
        authenticator.authenticated_profiles["test-profile"] = True

        authenticator.logout("test-profile")

        assert "test-profile" not in authenticator.authenticated_profiles

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    def test_logout_nonexistent_profile(self) -> None:
        """Test logging out a profile that doesn't exist."""
        authenticator = ADFSAuthenticator()

        # Should not raise an error
        authenticator.logout("nonexistent-profile")

        assert len(authenticator.authenticated_profiles) == 0

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    def test_logout_all(self) -> None:
        """Test logging out all profiles."""
        authenticator = ADFSAuthenticator()
        authenticator.authenticated_profiles.update({"profile1": True, "profile2": False, "profile3": True})

        authenticator.logout_all()

        assert len(authenticator.authenticated_profiles) == 0


class TestADFSCommandBuilding:
    """Test ADFS command building functionality."""

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    def test_build_command_basic(self) -> None:
        """Test building basic ADFS command."""
        authenticator = ADFSAuthenticator()

        # Create mock request
        mock_credentials = Mock()
        mock_credentials.adfs_host = "adfs.example.com"

        mock_settings = Mock()
        mock_settings.env_mode = True
        mock_settings.no_sspi = True

        mock_request = Mock()
        mock_request.profile = "test-profile"
        mock_request.credentials = mock_credentials
        mock_request.settings = mock_settings

        cmd = authenticator._build_command(mock_request)

        # Check that basic components are present
        assert "aws-adfs" in cmd
        assert "login" in cmd
        assert "--profile=test-profile" in cmd
        assert "--adfs-host=adfs.example.com" in cmd

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    def test_build_command_with_flags(self) -> None:
        """Test building ADFS command with optional flags."""
        authenticator = ADFSAuthenticator()

        # Create mock request with all flags
        mock_credentials = Mock()
        mock_credentials.adfs_host = "adfs.example.com"

        mock_settings = Mock()
        mock_settings.env_mode = True
        mock_settings.no_sspi = True

        mock_request = Mock()
        mock_request.profile = "test-profile"
        mock_request.credentials = mock_credentials
        mock_request.settings = mock_settings

        cmd = authenticator._build_command(mock_request)

        # Should include optional flags
        assert "--env" in cmd
        assert "--no-sspi" in cmd

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    def test_build_command_without_flags(self) -> None:
        """Test building ADFS command without optional flags."""
        authenticator = ADFSAuthenticator()

        # Create mock request without optional flags
        mock_credentials = Mock()
        mock_credentials.adfs_host = "adfs.example.com"

        mock_settings = Mock()
        mock_settings.env_mode = False
        mock_settings.no_sspi = False

        mock_request = Mock()
        mock_request.profile = "test-profile"
        mock_request.credentials = mock_credentials
        mock_request.settings = mock_settings

        cmd = authenticator._build_command(mock_request)

        # Should not include optional flags
        assert "--env" not in cmd
        assert "--no-sspi" not in cmd


class TestADFSErrorParsing:
    """Test ADFS error message parsing functionality."""

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    def test_parse_error_empty_output(self) -> None:
        """Test parsing empty error output."""
        authenticator = ADFSAuthenticator()

        result = authenticator._parse_error_message("")

        assert result == "Unknown error occurred"

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    def test_parse_error_invalid_credentials(self) -> None:
        """Test parsing invalid credentials error."""
        authenticator = ADFSAuthenticator()

        error_output = "Error: Invalid username or password"
        result = authenticator._parse_error_message(error_output)

        assert "Invalid username or password" in result
        assert "check your credentials" in result

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    def test_parse_error_connection_refused(self) -> None:
        """Test parsing connection refused error."""
        authenticator = ADFSAuthenticator()

        error_output = "Error: Connection refused to adfs.example.com"
        result = authenticator._parse_error_message(error_output)

        assert "Cannot connect to ADFS server" in result
        assert "network connection" in result

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    def test_parse_error_ssl_certificate(self) -> None:
        """Test parsing SSL certificate error."""
        authenticator = ADFSAuthenticator()

        error_output = "Error: SSL certificate verification failed"
        result = authenticator._parse_error_message(error_output)

        assert "SSL certificate error" in result

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    def test_parse_error_timeout(self) -> None:
        """Test parsing timeout error."""
        authenticator = ADFSAuthenticator()

        error_output = "Error: Connection timeout after 30 seconds"
        result = authenticator._parse_error_message(error_output)

        assert "Connection timeout" in result

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    def test_parse_error_command_not_found(self) -> None:
        """Test parsing command not found error."""
        authenticator = ADFSAuthenticator()

        error_output = "bash: aws-adfs: command not found"
        result = authenticator._parse_error_message(error_output)

        assert "aws-adfs command not found" in result
        assert "pip install aws-adfs" in result

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    def test_parse_error_unknown(self) -> None:
        """Test parsing unknown error."""
        authenticator = ADFSAuthenticator()

        error_output = "Some unexpected error occurred\nWith multiple lines"
        result = authenticator._parse_error_message(error_output)

        # Should return the first line for unknown errors
        assert "Some unexpected error occurred" in result


class TestADFSAuthenticationFlow:
    """Test ADFS authentication flow with mocks."""

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    @pytest.mark.skip(reason="Async tests not supported in current environment")
    @patch("aws_adfs_gui.adfs_auth.asyncio.create_subprocess_exec")
    async def test_execute_command_success(self, mock_subprocess) -> None:
        """Test successful command execution."""
        authenticator = ADFSAuthenticator()

        # Mock successful process
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"Success output", b""))
        mock_subprocess.return_value = mock_process

        cmd = ["aws-adfs", "login", "--profile=test"]
        env = {"username": "testuser", "password": "testpass"}
        timeout = 30

        with patch("aws_adfs_gui.adfs_auth.asyncio.wait_for") as mock_wait_for:
            mock_wait_for.return_value = (b"Success output", b"")

            success, output = await authenticator._execute_command(cmd, env, timeout)

        assert success is True
        assert "Success output" in output

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    @pytest.mark.skip(reason="Async tests not supported in current environment")
    @patch("aws_adfs_gui.adfs_auth.asyncio.create_subprocess_exec")
    async def test_execute_command_failure(self, mock_subprocess) -> None:
        """Test failed command execution."""
        authenticator = ADFSAuthenticator()

        # Mock failed process
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b"Error output", b""))
        mock_subprocess.return_value = mock_process

        cmd = ["aws-adfs", "login", "--profile=test"]
        env = {"username": "testuser", "password": "testpass"}
        timeout = 30

        with patch("aws_adfs_gui.adfs_auth.asyncio.wait_for") as mock_wait_for:
            mock_wait_for.return_value = (b"Error output", b"")

            success, output = await authenticator._execute_command(cmd, env, timeout)

        assert success is False
        assert "Error output" in output

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    @pytest.mark.skip(reason="Async tests not supported in current environment")
    @patch("aws_adfs_gui.adfs_auth.asyncio.create_subprocess_exec")
    async def test_execute_command_timeout(self, mock_subprocess) -> None:
        """Test command execution timeout."""
        authenticator = ADFSAuthenticator()

        # Mock process that times out
        mock_process = Mock()
        mock_process.kill = Mock()
        mock_process.wait = AsyncMock()
        mock_subprocess.return_value = mock_process

        cmd = ["aws-adfs", "login", "--profile=test"]
        env = {"username": "testuser", "password": "testpass"}
        timeout = 30

        with patch("aws_adfs_gui.adfs_auth.asyncio.wait_for") as mock_wait_for:
            mock_wait_for.side_effect = TimeoutError()

            success, output = await authenticator._execute_command(cmd, env, timeout)

        assert success is False
        assert "timed out after 30 seconds" in output
        mock_process.kill.assert_called_once()

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    @pytest.mark.skip(reason="Async tests not supported in current environment")
    @patch("aws_adfs_gui.adfs_auth.asyncio.create_subprocess_exec")
    async def test_execute_command_file_not_found(self, mock_subprocess) -> None:
        """Test command execution when aws-adfs is not found."""
        authenticator = ADFSAuthenticator()

        # Mock FileNotFoundError
        mock_subprocess.side_effect = FileNotFoundError()

        cmd = ["aws-adfs", "login", "--profile=test"]
        env = {"username": "testuser", "password": "testpass"}
        timeout = 30

        success, output = await authenticator._execute_command(cmd, env, timeout)

        assert success is False
        assert "aws-adfs command not found" in output
        assert "pip install aws-adfs" in output


class TestADFSAuthenticationState:
    """Test ADFS authentication state management."""

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    def test_authentication_state_workflow(self) -> None:
        """Test complete authentication state workflow."""
        authenticator = ADFSAuthenticator()

        profile = "test-profile"

        # Initially not authenticated
        assert authenticator.is_authenticated(profile) is False

        # Simulate successful authentication
        authenticator.authenticated_profiles[profile] = True
        assert authenticator.is_authenticated(profile) is True

        # Logout
        authenticator.logout(profile)
        assert authenticator.is_authenticated(profile) is False

    @pytest.mark.skipif(not ADFS_AUTH_AVAILABLE, reason="ADFSAuthenticator not available")
    def test_multiple_profiles_state(self) -> None:
        """Test managing multiple profile authentication states."""
        authenticator = ADFSAuthenticator()

        profiles = ["profile1", "profile2", "profile3"]

        # Authenticate first two profiles
        authenticator.authenticated_profiles["profile1"] = True
        authenticator.authenticated_profiles["profile2"] = True
        authenticator.authenticated_profiles["profile3"] = False

        assert authenticator.is_authenticated("profile1") is True
        assert authenticator.is_authenticated("profile2") is True
        assert authenticator.is_authenticated("profile3") is False

        # Logout all
        authenticator.logout_all()

        for profile in profiles:
            assert authenticator.is_authenticated(profile) is False


class TestADFSIntegration:
    """Test ADFS integration scenarios."""

    def test_error_message_categorization(self) -> None:
        """Test categorizing different types of error messages."""
        if not ADFS_AUTH_AVAILABLE:
            pytest.skip("ADFSAuthenticator not available")

        authenticator = ADFSAuthenticator()

        # Test different error categories
        error_categories = {
            "Invalid username or password": "credentials",
            "Connection refused": "network",
            "SSL certificate": "certificate",
            "Connection timeout": "timeout",
            "command not found": "installation",
            "Permission denied": "permissions",
            "Unknown error": "generic",
        }

        for error_text, _category in error_categories.items():
            result = authenticator._parse_error_message(error_text)
            assert len(result) > 0
            assert isinstance(result, str)

    def test_command_structure_validation(self) -> None:
        """Test that command structure is valid."""
        if not ADFS_AUTH_AVAILABLE:
            pytest.skip("ADFSAuthenticator not available")

        authenticator = ADFSAuthenticator()

        # Mock minimal request
        mock_request = Mock()
        mock_request.profile = "test-profile"
        mock_request.credentials = Mock()
        mock_request.credentials.adfs_host = "adfs.example.com"
        mock_request.settings = Mock()
        mock_request.settings.env_mode = False
        mock_request.settings.no_sspi = False

        cmd = authenticator._build_command(mock_request)

        # Validate command structure
        assert isinstance(cmd, list)
        assert len(cmd) >= 4  # Minimum: aws-adfs, login, --profile, --adfs-host
        assert cmd[0] == "aws-adfs"
        assert cmd[1] == "login"

        # Check that profile and host are properly formatted
        profile_found = any("--profile=" in arg for arg in cmd)
        host_found = any("--adfs-host=" in arg for arg in cmd)

        assert profile_found
        assert host_found
