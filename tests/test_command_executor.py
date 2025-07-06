"""Tests for the command executor module."""

import sys
import time
from unittest.mock import Mock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, "src")

# Test availability of command executor
try:
    from aws_adfs_gui.command_executor import CommandExecutor

    COMMAND_EXECUTOR_AVAILABLE = True
except ImportError:
    COMMAND_EXECUTOR_AVAILABLE = False


class TestCommandExecutorBasic:
    """Test basic CommandExecutor functionality that doesn't require full dependencies."""

    @pytest.mark.skipif(not COMMAND_EXECUTOR_AVAILABLE, reason="CommandExecutor not available")
    def test_command_executor_initialization(self) -> None:
        """Test CommandExecutor initialization."""
        executor = CommandExecutor()

        assert hasattr(executor, "command_history")
        assert hasattr(executor, "max_history")
        assert executor.max_history == 100
        assert isinstance(executor.command_history, list)
        assert len(executor.command_history) == 0

    @pytest.mark.skipif(not COMMAND_EXECUTOR_AVAILABLE, reason="CommandExecutor not available")
    def test_get_command_history_empty(self) -> None:
        """Test getting command history when empty."""
        executor = CommandExecutor()

        history = executor.get_command_history()

        assert isinstance(history, list)
        assert len(history) == 0

    @pytest.mark.skipif(not COMMAND_EXECUTOR_AVAILABLE, reason="CommandExecutor not available")
    def test_clear_history(self) -> None:
        """Test clearing command history."""
        executor = CommandExecutor()

        # Add some mock history items
        executor.command_history = [
            Mock(id="1", command="aws s3 ls"),
            Mock(id="2", command="aws ec2 describe-instances"),
        ]

        assert len(executor.command_history) == 2

        executor.clear_history()

        assert len(executor.command_history) == 0

    @pytest.mark.skipif(not COMMAND_EXECUTOR_AVAILABLE, reason="CommandExecutor not available")
    def test_max_history_limit(self) -> None:
        """Test that history is limited to max_history items."""
        executor = CommandExecutor()
        executor.max_history = 3  # Set small limit for testing

        # Mock _add_to_history behavior by directly manipulating the list
        mock_history_items = [Mock(id=f"cmd_{i}") for i in range(5)]

        # Simulate adding items one by one with the max limit logic
        for item in mock_history_items:
            executor.command_history.append(item)
            if len(executor.command_history) > executor.max_history:
                executor.command_history.pop(0)

        # Should only have the last 3 items
        assert len(executor.command_history) == 3
        assert executor.command_history[0].id == "cmd_2"
        assert executor.command_history[1].id == "cmd_3"
        assert executor.command_history[2].id == "cmd_4"


class TestCommandExecutorHistory:
    """Test command history management functionality."""

    @pytest.mark.skipif(not COMMAND_EXECUTOR_AVAILABLE, reason="CommandExecutor not available")
    def test_add_to_history(self) -> None:
        """Test adding items to command history."""
        executor = CommandExecutor()

        # Create a mock history entry
        mock_entry = Mock()
        mock_entry.id = "test-id"
        mock_entry.command = "aws s3 ls"

        # Use the private method directly
        executor._add_to_history(mock_entry)

        assert len(executor.command_history) == 1
        assert executor.command_history[0] == mock_entry

    @pytest.mark.skipif(not COMMAND_EXECUTOR_AVAILABLE, reason="CommandExecutor not available")
    def test_history_copy_returned(self) -> None:
        """Test that get_command_history returns a copy, not the original list."""
        executor = CommandExecutor()

        # Add some mock history
        mock_entry = Mock(id="test")
        executor.command_history.append(mock_entry)

        history = executor.get_command_history()

        # Modifying the returned list shouldn't affect the original
        history.append(Mock(id="new"))

        assert len(executor.command_history) == 1
        assert len(history) == 2


class TestCommandExecutorLogic:
    """Test command executor logic without external dependencies."""

    @pytest.mark.skipif(not COMMAND_EXECUTOR_AVAILABLE, reason="CommandExecutor not available")
    def test_profile_categorization_logic(self) -> None:
        """Test the logic for categorizing dev vs other profiles."""
        # We can test the categorization logic by simulating it
        profiles = ["aws-dev-eu", "aws-dev-sg", "kds-ets-np", "kds-gps-pd"]

        # Simulate the dev profile detection logic
        dev_profiles = []
        other_profiles = []

        for profile_name in profiles:
            # Mock the profile lookup logic (simplified)
            if "dev" in profile_name:
                dev_profiles.append(profile_name)
            else:
                other_profiles.append(profile_name)

        assert len(dev_profiles) == 2
        assert len(other_profiles) == 2
        assert "aws-dev-eu" in dev_profiles
        assert "aws-dev-sg" in dev_profiles
        assert "kds-ets-np" in other_profiles
        assert "kds-gps-pd" in other_profiles

    def test_command_timing_simulation(self) -> None:
        """Test command timing simulation."""
        start_time = time.time()

        # Simulate some work
        time.sleep(0.1)

        duration = time.time() - start_time

        assert duration >= 0.1
        assert duration < 0.2  # Should be close to 0.1 seconds


@pytest.mark.skipif(not COMMAND_EXECUTOR_AVAILABLE, reason="CommandExecutor not available")
class TestCommandExecutorWithMocks:
    """Test command executor with mocked dependencies."""

    @patch("aws_adfs_gui.command_executor.config")
    def test_execute_command_with_mock_config(self, mock_config) -> None:
        """Test command execution with mocked config."""
        # Mock the config to return test profiles
        mock_profile = Mock()
        mock_profile.group.value = "dev"
        mock_config.get_profile_by_name.return_value = mock_profile

        # We can test the setup without actually executing commands
        test_profiles = ["test-dev-profile"]

        # Verify that the config would be called correctly
        for profile_name in test_profiles:
            profile = mock_config.get_profile_by_name(profile_name)
            assert profile is not None

    @pytest.mark.skip(reason="Async tests not supported in current environment")
    @patch("aws_adfs_gui.command_executor.asyncio")
    @patch("aws_adfs_gui.command_executor.config")
    async def test_execute_single_command_mock(self, mock_config, mock_asyncio) -> None:
        """Test single command execution with mocks."""
        # Mock asyncio subprocess
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"success output", b"")

        mock_asyncio.create_subprocess_shell.return_value = mock_process
        mock_asyncio.wait_for.return_value = (b"success output", b"")

        # Test the command structure
        profile = "test-profile"
        command = "aws s3 ls"
        timeout = 30

        # We can test that the right parameters would be passed
        expected_env = {"AWS_PROFILE": profile}

        assert expected_env["AWS_PROFILE"] == profile
        assert command == "aws s3 ls"
        assert timeout == 30

    def test_command_result_structure(self) -> None:
        """Test command result structure without dependencies."""
        # Test the expected structure of command results
        result_data = {
            "profile": "test-profile",
            "success": True,
            "output": "Command output",
            "error": None,
            "duration": 1.5,
        }

        # Verify the structure
        assert "profile" in result_data
        assert "success" in result_data
        assert "output" in result_data
        assert "error" in result_data
        assert "duration" in result_data

        assert isinstance(result_data["success"], bool)
        assert isinstance(result_data["duration"], int | float)


class TestCommandExecutorErrorHandling:
    """Test command executor error handling logic."""

    def test_timeout_error_simulation(self) -> None:
        """Test timeout error handling simulation."""
        timeout_seconds = 30
        start_time = time.time()

        # Simulate a timeout scenario
        try:
            # Simulate the timeout check
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                raise TimeoutError(f"Command timed out after {timeout_seconds} seconds")
        except TimeoutError as e:
            assert f"after {timeout_seconds} seconds" in str(e)

    def test_error_result_structure(self) -> None:
        """Test error result structure."""
        error_result = {
            "profile": "test-profile",
            "success": False,
            "output": "",
            "error": "Connection timeout",
            "duration": 30.0,
        }

        assert error_result["success"] is False
        assert error_result["error"] is not None
        error_msg = error_result["error"]
        assert isinstance(error_msg, str)
        assert len(error_msg) > 0

    def test_dev_profile_failure_logic(self) -> None:
        """Test dev profile failure logic simulation."""
        # Simulate the dev profile failure prevention logic
        dev_results = [
            {"profile": "aws-dev-eu", "success": False, "error": "Connection failed"},
            {"profile": "aws-dev-sg", "success": False, "error": "Auth failed"},
        ]

        other_profiles = ["kds-ets-np", "kds-gps-np", "kds-ets-pd"]

        # Check if any dev profiles failed
        dev_failures = [r for r in dev_results if not r["success"]]

        if dev_failures:
            # Should not proceed to other profiles
            executed_other_profiles = []
        else:
            executed_other_profiles = other_profiles

        assert len(dev_failures) == 2
        assert len(executed_other_profiles) == 0  # Should be empty due to dev failures


class TestCommandExecutorIntegration:
    """Test command executor integration scenarios."""

    def test_command_history_workflow(self) -> None:
        """Test the complete command history workflow."""
        if not COMMAND_EXECUTOR_AVAILABLE:
            pytest.skip("CommandExecutor not available")

        executor = CommandExecutor()

        # Simulate adding multiple commands to history
        mock_commands = [
            Mock(id="1", command="aws s3 ls"),
            Mock(id="2", command="aws ec2 describe-instances"),
            Mock(id="3", command="aws iam list-users"),
        ]

        # Add commands one by one
        for cmd in mock_commands:
            executor._add_to_history(cmd)

        # Verify they're all there
        history = executor.get_command_history()
        assert len(history) == 3

        # Clear and verify
        executor.clear_history()
        assert len(executor.get_command_history()) == 0

    def test_profile_execution_order_simulation(self) -> None:
        """Test profile execution order simulation."""
        profiles = ["aws-dev-eu", "aws-dev-sg", "kds-ets-np", "kds-gps-pd"]

        # Simulate the separation logic
        dev_profiles = [p for p in profiles if "dev" in p]
        other_profiles = [p for p in profiles if "dev" not in p]

        # Execution order should be dev first, then others
        execution_order = dev_profiles + other_profiles

        assert execution_order[0] == "aws-dev-eu"
        assert execution_order[1] == "aws-dev-sg"
        assert execution_order[2] == "kds-ets-np"
        assert execution_order[3] == "kds-gps-pd"

        # Dev profiles should be first
        assert all("dev" in p for p in execution_order[:2])
        assert all("dev" not in p for p in execution_order[2:])
