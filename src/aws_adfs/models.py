"""Data models for AWS ADFS GUI application."""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


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
    description: Optional[str] = Field(None, description="Profile description")


class CommandRequest(BaseModel):
    """Request to execute a command across profiles."""

    command: str = Field(..., description="Command to execute")
    profiles: List[str] = Field(..., description="List of profile names to execute on")
    timeout: int = Field(default=300, description="Command timeout in seconds")


class CommandResult(BaseModel):
    """Result of a command execution."""

    profile: str = Field(..., description="Profile name")
    success: bool = Field(..., description="Whether command succeeded")
    output: str = Field(default="", description="Command output")
    error: Optional[str] = Field(None, description="Error message if failed")
    duration: float = Field(..., description="Execution time in seconds")


class CommandHistory(BaseModel):
    """Command history entry."""

    id: str = Field(..., description="Unique command ID")
    command: str = Field(..., description="Command that was executed")
    timestamp: str = Field(..., description="When command was executed")
    profiles: List[str] = Field(..., description="Profiles it was executed on")
    success_count: int = Field(..., description="Number of successful executions")
    total_count: int = Field(..., description="Total number of executions")


class ProfileGroups(BaseModel):
    """Configuration for profile groups."""

    groups: Dict[ProfileGroup, List[AWSProfile]] = Field(
        default_factory=dict, description="Profiles organized by groups"
    )


class ExportRequest(BaseModel):
    """Request to export command results."""

    format: str = Field(default="json", description="Export format (json, csv, txt)")
    include_timestamps: bool = Field(
        default=True, description="Include timestamps in export"
    )
