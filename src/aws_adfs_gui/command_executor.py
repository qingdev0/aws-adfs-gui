"""Command execution engine for AWS CLI commands across multiple profiles."""

import asyncio
import shlex
import subprocess
import time
from collections.abc import AsyncGenerator
from typing import Any

from .models import AWSProfile, CommandResult, ExecutionStatus


class CommandExecutor:
    """Executes AWS CLI commands across multiple profiles."""

    def __init__(self, timeout: int = 30):
        """Initialize the command executor.

        Args:
            timeout: Command timeout in seconds
        """
        self.timeout = timeout

    async def execute_command(
        self,
        command: str,
        profiles: list[AWSProfile],
        stop_on_error: bool = True,
    ) -> AsyncGenerator[CommandResult, None]:
        """Execute command across multiple profiles.

        Args:
            command: AWS CLI command to execute
            profiles: List of AWS profiles to execute command on
            stop_on_error: Whether to stop execution on first error

        Yields:
            CommandResult for each profile
        """
        if not profiles:
            return

        # Parse and validate command
        try:
            parsed_cmd = self._parse_command(command)
        except ValueError as e:
            for profile in profiles:
                yield CommandResult(
                    profile=profile.name,
                    command=command,
                    status=ExecutionStatus.ERROR,
                    output="",
                    error=f"Invalid command: {e}",
                    duration=0.0,
                )
            return

        # Execute commands
        execution_params = {"command": command, "parsed_cmd": parsed_cmd, "stop_on_error": stop_on_error}

        for profile in profiles:
            result = await self._execute_single_command(profile, execution_params)
            yield result

            # Stop on error if configured
            if stop_on_error and result.status == ExecutionStatus.ERROR:
                # Return error results for remaining profiles
                for remaining_profile in profiles[profiles.index(profile) + 1 :]:
                    yield CommandResult(
                        profile=remaining_profile.name,
                        command=command,
                        status=ExecutionStatus.SKIPPED,
                        output="",
                        error="Skipped due to previous error",
                        duration=0.0,
                    )
                break

    def _parse_command(self, command: str) -> list[str]:
        """Parse and validate AWS command.

        Args:
            command: Raw command string

        Returns:
            Parsed command tokens

        Raises:
            ValueError: If command is invalid
        """
        if not command.strip():
            raise ValueError("Command cannot be empty")

        # Parse command using shell lexer
        try:
            tokens = shlex.split(command)
        except ValueError as e:
            raise ValueError(f"Invalid command syntax: {e}") from e

        # Basic validation
        if not tokens:
            raise ValueError("Command cannot be empty")

        # Ensure AWS command
        if tokens[0] != "aws":
            tokens.insert(0, "aws")

        return tokens

    async def _execute_single_command(self, profile: AWSProfile, params: dict[str, Any]) -> CommandResult:
        """Execute command for a single profile.

        Args:
            profile: AWS profile to use
            params: Execution parameters

        Returns:
            Command execution result
        """
        start_time = time.time()
        cmd_tokens = params["parsed_cmd"].copy()

        # Add profile to command
        if "--profile" not in cmd_tokens:
            cmd_tokens.extend(["--profile", profile.name])

        # Add region if specified
        if profile.region and "--region" not in cmd_tokens:
            cmd_tokens.extend(["--region", profile.region])

        try:
            # Execute command
            process = await asyncio.create_subprocess_exec(
                *cmd_tokens,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=None,  # Use current environment
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)
            except TimeoutError:
                process.kill()
                await process.wait()
                duration = time.time() - start_time
                return CommandResult(
                    profile=profile.name,
                    command=params["command"],
                    status=ExecutionStatus.ERROR,
                    output="",
                    error=f"Command timed out after {self.timeout} seconds",
                    duration=duration,
                )

            duration = time.time() - start_time

            # Decode output
            output_str = stdout.decode("utf-8") if stdout else ""
            error_str = stderr.decode("utf-8") if stderr else ""

            # Determine status
            if process.returncode == 0:
                status = ExecutionStatus.SUCCESS
            else:
                status = ExecutionStatus.ERROR

            return CommandResult(
                profile=profile.name,
                command=params["command"],
                status=status,
                output=output_str,
                error=error_str,
                duration=duration,
            )

        except (OSError, subprocess.SubprocessError) as e:
            duration = time.time() - start_time
            return CommandResult(
                profile=profile.name,
                command=params["command"],
                status=ExecutionStatus.ERROR,
                output="",
                error=f"Failed to execute command: {e}",
                duration=duration,
            )

    def validate_profiles(self, profiles: list[AWSProfile]) -> list[str]:
        """Validate that profiles exist and are accessible.

        Args:
            profiles: List of profiles to validate

        Returns:
            List of error messages (empty if all valid)
        """
        errors = []

        for profile in profiles:
            if not profile.name:
                errors.append("Profile name cannot be empty")
                continue

            # Try to get caller identity to validate profile
            try:
                result = subprocess.run(
                    ["aws", "sts", "get-caller-identity", "--profile", profile.name],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )

                if result.returncode != 0:
                    errors.append(f"Profile '{profile.name}' is not valid: {result.stderr.strip()}")

            except (subprocess.TimeoutExpired, OSError) as e:
                errors.append(f"Profile '{profile.name}' validation failed: {e}")

        return errors


# Global instance for compatibility
executor = CommandExecutor()
