"""Command execution engine for AWS ADFS GUI application."""

import asyncio
import os
import time
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime

from .config import config
from .models import CommandHistory, CommandRequest, CommandResult


class CommandExecutor:
    """Executes commands across multiple AWS profiles."""

    def __init__(self) -> None:
        """Initialize the command executor."""
        self.command_history: list[CommandHistory] = []
        self.max_history = 100

    async def execute_command(self, request: CommandRequest) -> AsyncGenerator[CommandResult, None]:
        """Execute a command across multiple profiles with smart error handling.

        Args:
            request: Command execution request

        Yields:
            CommandResult for each profile as they complete
        """
        command_id = str(uuid.uuid4())
        start_time = datetime.now()

        # Separate dev profiles from others for smart error handling
        dev_profiles = []
        other_profiles = []

        for profile_name in request.profiles:
            profile = config.get_profile_by_name(profile_name)
            if profile and profile.group.value == "dev":
                dev_profiles.append(profile_name)
            else:
                other_profiles.append(profile_name)

        # Execute dev profiles first
        dev_results = []
        if dev_profiles:
            dev_tasks = [
                self._execute_single_command(profile, request.command, request.timeout) for profile in dev_profiles
            ]

            for result in asyncio.as_completed(dev_tasks):
                result_obj = await result
                dev_results.append(result_obj)
                yield result_obj

        # Check if any dev profiles failed immediately
        dev_failures = [r for r in dev_results if not r.success]

        # If dev profiles failed, don't proceed to other profiles
        if dev_failures:
            # Create history entry
            history_entry = CommandHistory(
                id=command_id,
                command=request.command,
                timestamp=start_time.isoformat(),
                profiles=request.profiles,
                success_count=len(dev_results) - len(dev_failures),
                total_count=len(request.profiles),
            )
            self._add_to_history(history_entry)
            return

        # Execute other profiles
        if other_profiles:
            other_tasks = [
                self._execute_single_command(profile, request.command, request.timeout) for profile in other_profiles
            ]

            for result in asyncio.as_completed(other_tasks):
                result_obj = await result
                yield result_obj

        # Create history entry
        all_results = dev_results + [r async for r in self.execute_command(request)]
        success_count = len([r for r in all_results if r.success])

        history_entry = CommandHistory(
            id=command_id,
            command=request.command,
            timestamp=start_time.isoformat(),
            profiles=request.profiles,
            success_count=success_count,
            total_count=len(request.profiles),
        )
        self._add_to_history(history_entry)

    async def _execute_single_command(self, profile: str, command: str, timeout: int) -> CommandResult:
        """Execute a single command for a specific profile.

        Args:
            profile: AWS profile name
            command: Command to execute
            timeout: Command timeout in seconds

        Returns:
            CommandResult with execution details
        """
        start_time = time.time()

        try:
            # Set AWS profile environment variable
            env = os.environ.copy()
            env["AWS_PROFILE"] = profile

            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

            duration = time.time() - start_time

            if process.returncode == 0:
                return CommandResult(
                    profile=profile,
                    success=True,
                    output=stdout.decode("utf-8", errors="replace"),
                    error=None,
                    duration=duration,
                )
            else:
                return CommandResult(
                    profile=profile,
                    success=False,
                    output=stdout.decode("utf-8", errors="replace"),
                    error=stderr.decode("utf-8", errors="replace"),
                    duration=duration,
                )

        except TimeoutError:
            duration = time.time() - start_time
            return CommandResult(
                profile=profile,
                success=False,
                error=f"Command timed out after {timeout} seconds",
                duration=duration,
            )
        except Exception as e:
            duration = time.time() - start_time
            return CommandResult(profile=profile, success=False, error=str(e), duration=duration)

    def _add_to_history(self, entry: CommandHistory) -> None:
        """Add command to history, maintaining max size."""
        self.command_history.append(entry)
        if len(self.command_history) > self.max_history:
            self.command_history.pop(0)

    def get_command_history(self) -> list[CommandHistory]:
        """Get command history."""
        return self.command_history.copy()

    def clear_history(self) -> None:
        """Clear command history."""
        self.command_history.clear()


# Global command executor instance
executor = CommandExecutor()
