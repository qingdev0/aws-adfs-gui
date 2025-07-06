"""AWS credentials management and validation for AWS ADFS GUI."""

import asyncio
import configparser
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import AWSProfile


class CredentialStatus:
    """Represents the status of AWS credentials for a profile."""

    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    MISSING = "missing"
    UNKNOWN = "unknown"

    # Status display configuration
    STATUS_CONFIG = {
        VALID: {
            "label": "Active",
            "color": "#28a745",  # Green
            "icon": "fas fa-check-circle",
            "priority": 1,
        },
        EXPIRED: {
            "label": "Expired",
            "color": "#ffc107",  # Yellow
            "icon": "fas fa-clock",
            "priority": 2,
        },
        INVALID: {
            "label": "Invalid",
            "color": "#dc3545",  # Red
            "icon": "fas fa-exclamation-triangle",
            "priority": 3,
        },
        MISSING: {
            "label": "Not Configured",
            "color": "#6c757d",  # Gray
            "icon": "fas fa-question-circle",
            "priority": 4,
        },
        UNKNOWN: {
            "label": "Checking...",
            "color": "#17a2b8",  # Blue
            "icon": "fas fa-spinner fa-spin",
            "priority": 5,
        },
    }


class AWSCredentialsManager:
    """Manages AWS credentials validation and status detection."""

    def __init__(self):
        self.aws_dir = Path.home() / ".aws"
        self.credentials_file = self.aws_dir / "credentials"
        self.config_file = self.aws_dir / "config"
        self.profile_status: dict[str, dict[str, Any]] = {}

    async def validate_all_profiles(self, profiles: list[AWSProfile]) -> dict[str, dict[str, Any]]:
        """
        Validate credentials for all profiles concurrently.

        Args:
            profiles: List of AWS profiles to validate

        Returns:
            Dictionary mapping profile names to status information
        """
        # Run validations concurrently for better performance
        tasks = [self._validate_profile_credentials(profile.name) for profile in profiles]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for profile, result in zip(profiles, results, strict=False):
            if isinstance(result, Exception):
                self.profile_status[profile.name] = {
                    "status": CredentialStatus.UNKNOWN,
                    "message": f"Validation error: {str(result)}",
                    "last_checked": datetime.now(UTC).isoformat(),
                    "profile_info": profile,
                    **CredentialStatus.STATUS_CONFIG[CredentialStatus.UNKNOWN],
                }
            else:
                self.profile_status[profile.name] = result

        return self.profile_status

    async def _validate_profile_credentials(self, profile_name: str) -> dict[str, Any]:
        """
        Validate credentials for a specific profile.

        Args:
            profile_name: Name of the AWS profile to validate

        Returns:
            Dictionary with validation results
        """
        try:
            # Check if profile exists in AWS config files
            if not self._profile_exists_in_config(profile_name):
                return self._create_status_result(
                    CredentialStatus.MISSING, f"Profile '{profile_name}' not found in ~/.aws configuration"
                )

            # Test credentials with a simple AWS STS call
            success, output, error = await self._test_aws_credentials(profile_name)

            if success:
                # Parse AWS STS output for additional info
                expiration_info = self._parse_credentials_info(output)
                return self._create_status_result(
                    CredentialStatus.VALID, f"Credentials active for {profile_name}", extra_info=expiration_info
                )
            else:
                # Determine specific error type
                if "ExpiredToken" in error or "TokenRefreshRequired" in error:
                    return self._create_status_result(
                        CredentialStatus.EXPIRED,
                        f"Credentials expired for {profile_name}. Please refresh with aws-adfs.",
                    )
                elif "InvalidUserID.NotFound" in error or "AccessDenied" in error:
                    return self._create_status_result(
                        CredentialStatus.INVALID, f"Invalid credentials for {profile_name}. Please re-authenticate."
                    )
                else:
                    return self._create_status_result(
                        CredentialStatus.INVALID, f"Credential validation failed for {profile_name}: {error}"
                    )

        except Exception as e:
            return self._create_status_result(
                CredentialStatus.UNKNOWN, f"Validation error for {profile_name}: {str(e)}"
            )

    def _profile_exists_in_config(self, profile_name: str) -> bool:
        """Check if profile exists in AWS config files."""
        # Check credentials file
        if self.credentials_file.exists():
            credentials_config = configparser.ConfigParser()
            credentials_config.read(self.credentials_file)
            if profile_name in credentials_config.sections():
                return True

        # Check config file
        if self.config_file.exists():
            config = configparser.ConfigParser()
            config.read(self.config_file)

            # Check for profile section (could be 'profile name' or just 'name')
            if profile_name in config.sections():
                return True
            if f"profile {profile_name}" in config.sections():
                return True

        return False

    async def _test_aws_credentials(self, profile_name: str) -> tuple[bool, str, str]:
        """
        Test AWS credentials by calling AWS STS get-caller-identity.

        Args:
            profile_name: AWS profile name to test

        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            # Use AWS CLI to test credentials with timeout
            cmd = ["aws", "sts", "get-caller-identity", "--profile", profile_name, "--output", "json"]

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=os.environ.copy()
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=10.0,  # 10 second timeout
                )

                stdout_str = stdout.decode("utf-8") if stdout else ""
                stderr_str = stderr.decode("utf-8") if stderr else ""

                return (process.returncode == 0, stdout_str, stderr_str)

            except TimeoutError:
                process.kill()
                await process.wait()
                return (False, "", "AWS CLI call timed out")

        except FileNotFoundError:
            return (False, "", "AWS CLI not found. Please install: pip install awscli")
        except Exception as e:
            return (False, "", f"AWS CLI execution error: {str(e)}")

    def _parse_credentials_info(self, aws_output: str) -> dict[str, Any]:
        """Parse AWS STS output for credential information."""
        try:
            data = json.loads(aws_output)
            return {
                "account_id": data.get("Account"),
                "user_id": data.get("UserId"),
                "arn": data.get("Arn"),
                "last_validated": datetime.now(UTC).isoformat(),
            }
        except (json.JSONDecodeError, KeyError):
            return {"last_validated": datetime.now(UTC).isoformat()}

    def _create_status_result(
        self, status: str, message: str, extra_info: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Create a standardized status result dictionary."""
        result = {
            "status": status,
            "message": message,
            "last_checked": datetime.now(UTC).isoformat(),
            **CredentialStatus.STATUS_CONFIG[status],
        }

        if extra_info:
            result.update(extra_info)

        return result

    def get_profile_status(self, profile_name: str) -> dict[str, Any]:
        """Get the current status of a specific profile."""
        return self.profile_status.get(
            profile_name,
            {
                "status": CredentialStatus.UNKNOWN,
                "message": "Status not checked yet",
                **CredentialStatus.STATUS_CONFIG[CredentialStatus.UNKNOWN],
            },
        )

    def get_all_status(self) -> dict[str, dict[str, Any]]:
        """Get status for all profiles."""
        return self.profile_status.copy()

    def get_status_summary(self) -> dict[str, int]:
        """Get a summary count of profiles by status."""
        summary = {}
        for status_info in self.profile_status.values():
            status = status_info.get("status", CredentialStatus.UNKNOWN)
            summary[status] = summary.get(status, 0) + 1
        return summary


class FlexibleCommandBuilder:
    """Builds flexible AWS commands with customizable options."""

    def __init__(self):
        self.default_aws_adfs_options = {
            "env_mode": True,
            "no_sspi": True,
            "region": None,
            "output_format": None,
            "duration": None,
            "assertion_duration": None,
        }

    def build_aws_adfs_command(self, profile_name: str, adfs_host: str, **options: Any) -> list[str]:
        """
        Build flexible aws-adfs login command.

        Args:
            profile_name: AWS profile name
            adfs_host: ADFS server hostname
            **options: Additional command options

        Returns:
            List of command arguments
        """
        cmd = ["aws-adfs", "login"]

        # Required parameters
        cmd.extend([f"--profile={profile_name}"])
        cmd.extend([f"--adfs-host={adfs_host}"])

        # Apply options with defaults
        merged_options = {**self.default_aws_adfs_options, **options}

        # Add optional flags
        if merged_options.get("env_mode", True):
            cmd.append("--env")

        if merged_options.get("no_sspi", True):
            cmd.append("--no-sspi")

        if merged_options.get("region"):
            cmd.extend([f"--region={merged_options['region']}"])

        if merged_options.get("output_format"):
            cmd.extend([f"--output-format={merged_options['output_format']}"])

        if merged_options.get("duration"):
            cmd.extend([f"--duration={merged_options['duration']}"])

        if merged_options.get("assertion_duration"):
            cmd.extend([f"--assertion-duration={merged_options['assertion_duration']}"])

        # Add any custom arguments
        if merged_options.get("custom_args"):
            cmd.extend(merged_options["custom_args"])

        return cmd

    def build_aws_cli_command(self, base_command: str, profile_name: str, **options: Any) -> list[str]:
        """
        Build AWS CLI command with flexible options.

        Args:
            base_command: Base AWS CLI command (e.g., "s3 ls")
            profile_name: AWS profile name
            **options: Additional AWS CLI options

        Returns:
            List of command arguments
        """
        cmd = ["aws"] + base_command.split()

        # Add profile
        cmd.extend(["--profile", profile_name])

        # Add optional parameters
        if options.get("region"):
            cmd.extend(["--region", options["region"]])

        if options.get("output"):
            cmd.extend(["--output", options["output"]])

        if options.get("endpoint_url"):
            cmd.extend(["--endpoint-url", options["endpoint_url"]])

        # Add any additional arguments
        if options.get("extra_args"):
            cmd.extend(options["extra_args"])

        return cmd


# Global instances
credentials_manager = AWSCredentialsManager()
command_builder = FlexibleCommandBuilder()
