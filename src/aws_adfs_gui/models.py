"""Data models for AWS ADFS GUI application."""

from enum import Enum

from pydantic import BaseModel, Field, SecretStr


class ProfileGroup(str, Enum):
    """AWS profile groups."""

    DEV = "dev"
    NON_PRODUCTION = "np"
    PRODUCTION = "pd"


class AWSProfile(BaseModel):
    """AWS profile configuration."""

    name: str = Field(..., description="Profile name")
    group: ProfileGroup = Field(..., description="Profile group")
    region: str = Field(default="us-east-1", description="AWS region")
    description: str | None = Field(None, description="Profile description")


class CommandRequest(BaseModel):
    """Request to execute a command across profiles."""

    command: str = Field(..., description="Command to execute")
    profiles: list[str] = Field(..., description="List of profile names to execute on")
    timeout: int = Field(default=300, description="Command timeout in seconds")


class CommandResult(BaseModel):
    """Result of a command execution."""

    profile: str = Field(..., description="Profile name")
    success: bool = Field(..., description="Whether command succeeded")
    output: str = Field(default="", description="Command output")
    error: str | None = Field(None, description="Error message if failed")
    duration: float = Field(..., description="Execution time in seconds")


class CommandHistory(BaseModel):
    """Command history entry."""

    id: str = Field(..., description="Unique command ID")
    command: str = Field(..., description="Command that was executed")
    timestamp: str = Field(..., description="When command was executed")
    profiles: list[str] = Field(..., description="Profiles it was executed on")
    success_count: int = Field(..., description="Number of successful executions")
    total_count: int = Field(..., description="Total number of executions")


class ProfileGroups(BaseModel):
    """Configuration for profile groups."""

    groups: dict[ProfileGroup, list[AWSProfile]] = Field(
        default_factory=dict, description="Profiles organized by groups"
    )


class ExportRequest(BaseModel):
    """Request to export command results."""

    format: str = Field(default="json", description="Export format (json, csv, txt)")
    include_timestamps: bool = Field(default=True, description="Include timestamps in export")


class ADFSCredentials(BaseModel):
    """ADFS authentication credentials."""

    username: str = Field(..., description="ADFS username")
    password: SecretStr = Field(..., description="ADFS password")
    adfs_host: str = Field(..., description="ADFS server hostname")
    certificate_path: str | None = Field(None, description="Path to certificate file")


class ConnectionSettings(BaseModel):
    """Connection settings for ADFS authentication."""

    timeout: int = Field(default=30, description="Connection timeout in seconds")
    retries: int = Field(default=3, description="Number of retry attempts")
    no_sspi: bool = Field(default=True, description="Disable SSPI authentication")
    env_mode: bool = Field(default=True, description="Use environment variable mode")


class AuthenticationRequest(BaseModel):
    """Request to authenticate with ADFS."""

    profile: str = Field(..., description="AWS profile name")
    credentials: ADFSCredentials = Field(..., description="ADFS credentials")
    settings: ConnectionSettings = Field(default_factory=ConnectionSettings, description="Connection settings")


class ConfigSaveRequest(BaseModel):
    """Request to save configuration."""

    credentials: ADFSCredentials | None = Field(None, description="ADFS credentials to save")
    connection_settings: ConnectionSettings | None = Field(None, description="Connection settings to save")
    ui_settings: dict[str, str | int | bool] | None = Field(None, description="UI settings to save")
    save_credentials: bool = Field(default=False, description="Whether to save credentials")


class ConfigResponse(BaseModel):
    """Response containing configuration data."""

    has_credentials: bool = Field(..., description="Whether credentials are stored")
    credentials_valid: bool = Field(..., description="Whether stored credentials are valid")
    connection_settings: ConnectionSettings = Field(..., description="Connection settings")
    ui_settings: dict[str, str | int | bool] = Field(..., description="UI settings")
    config_info: dict[str, str | int | bool] = Field(..., description="Configuration information")


class CredentialsTestRequest(BaseModel):
    """Request to test ADFS credentials."""

    username: str = Field(..., description="ADFS username")
    password: str = Field(..., description="ADFS password")
    adfs_host: str = Field(..., description="ADFS server hostname")


class CredentialsTestResponse(BaseModel):
    """Response from credentials test."""

    success: bool = Field(..., description="Whether test succeeded")
    message: str = Field(..., description="Test result message")
