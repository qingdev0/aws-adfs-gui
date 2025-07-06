"""ADFS authentication service for AWS ADFS GUI."""

import asyncio
import os
from typing import Dict, List, Tuple

from .models import ADFSCredentials, AuthenticationRequest, ConnectionSettings


class ADFSAuthenticator:
    """Handles ADFS authentication using aws-adfs command."""

    def __init__(self) -> None:
        self.authenticated_profiles: Dict[str, bool] = {}

    async def authenticate(self, request: AuthenticationRequest) -> Tuple[bool, str]:
        """
        Authenticate with ADFS for a specific profile.

        Args:
            request: Authentication request containing credentials and settings

        Returns:
            Tuple of (success, message)
        """
        try:
            # Prepare environment variables
            env = os.environ.copy()
            env["username"] = request.credentials.username
            env["password"] = request.credentials.password.get_secret_value()

            # Build aws-adfs command
            cmd = self._build_command(request)

            # Execute the command
            success, output = await self._execute_command(
                cmd, env, request.settings.timeout
            )

            if success:
                self.authenticated_profiles[request.profile] = True
                return True, f"Successfully authenticated profile '{request.profile}'"
            else:
                self.authenticated_profiles[request.profile] = False
                # Parse and return detailed error message
                error_msg = self._parse_error_message(output)
                return (
                    False,
                    f"Authentication failed for profile '{request.profile}': {error_msg}",
                )

        except Exception as e:
            self.authenticated_profiles[request.profile] = False
            return (
                False,
                f"Authentication error for profile '{request.profile}': {str(e)}",
            )

    def _build_command(self, request: AuthenticationRequest) -> List[str]:
        """Build the aws-adfs command with appropriate flags."""
        cmd = [
            "aws-adfs",
            "login",
            f"--profile={request.profile}",
            f"--adfs-host={request.credentials.adfs_host}",
        ]

        if request.settings.env_mode:
            cmd.append("--env")

        if request.settings.no_sspi:
            cmd.append("--no-sspi")

        return cmd

    async def _execute_command(
        self, cmd: List[str], env: Dict[str, str], timeout: int
    ) -> Tuple[bool, str]:
        """
        Execute the aws-adfs command asynchronously.

        Args:
            cmd: Command to execute
            env: Environment variables
            timeout: Command timeout in seconds

        Returns:
            Tuple of (success, output)
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                stdin=asyncio.subprocess.PIPE,
            )

            # Wait for completion with timeout
            try:
                stdout, _ = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
                output = stdout.decode("utf-8") if stdout else ""

                # Check return code
                if process.returncode == 0:
                    return True, output
                else:
                    return False, output

            except asyncio.TimeoutError:
                # Kill the process if it times out
                process.kill()
                await process.wait()
                return False, f"Authentication timed out after {timeout} seconds"

        except FileNotFoundError:
            return (
                False,
                "aws-adfs command not found. Please install aws-adfs: pip install aws-adfs",
            )
        except Exception as e:
            return False, f"Command execution error: {str(e)}"

    def _parse_error_message(self, output: str) -> str:
        """Parse error output and return user-friendly error message."""
        if not output:
            return "Unknown error occurred"

        output_lower = output.lower()

        # Common error patterns and user-friendly messages
        if (
            "invalid username or password" in output_lower
            or "authentication failed" in output_lower
        ):
            return "Invalid username or password. Please check your credentials."
        elif (
            "connection refused" in output_lower or "unable to connect" in output_lower
        ):
            return "Cannot connect to ADFS server. Please check the hostname and network connection."
        elif "ssl" in output_lower and (
            "certificate" in output_lower or "verify" in output_lower
        ):
            return "SSL certificate error. Please check your certificate file or disable SSL verification."
        elif "timeout" in output_lower:
            return "Connection timeout. Please check your network connection and ADFS server availability."
        elif "command not found" in output_lower or "aws-adfs" in output_lower:
            return "aws-adfs command not found. Please install aws-adfs: pip install aws-adfs"
        elif "permission denied" in output_lower:
            return "Permission denied. Please check your system permissions."
        elif "network is unreachable" in output_lower:
            return "Network is unreachable. Please check your internet connection."
        elif "name or service not known" in output_lower:
            return (
                "Cannot resolve ADFS server hostname. Please check the server address."
            )
        else:
            # Return the first line of the error for debugging, but cleaned up
            first_line = output.split("\n")[0].strip()
            return first_line if first_line else "Unknown authentication error"

    def is_authenticated(self, profile: str) -> bool:
        """Check if a profile is currently authenticated."""
        return self.authenticated_profiles.get(profile, False)

    def logout(self, profile: str) -> None:
        """Mark a profile as logged out."""
        if profile in self.authenticated_profiles:
            del self.authenticated_profiles[profile]

    def logout_all(self) -> None:
        """Mark all profiles as logged out."""
        self.authenticated_profiles.clear()

    async def test_credentials(self, credentials: ADFSCredentials) -> Tuple[bool, str]:
        """
        Test ADFS credentials without authenticating a specific profile.

        Args:
            credentials: ADFS credentials to test

        Returns:
            Tuple of (success, message)
        """
        try:
            # Use a temporary profile name for testing
            test_request = AuthenticationRequest(
                profile="test-connection",
                credentials=credentials,
                settings=ConnectionSettings(timeout=10),
            )

            success, message = await self.authenticate(test_request)

            # Clean up test profile
            if "test-connection" in self.authenticated_profiles:
                del self.authenticated_profiles["test-connection"]

            return success, message

        except Exception as e:
            return False, f"Credential test failed: {str(e)}"


# Global authenticator instance
authenticator = ADFSAuthenticator()
