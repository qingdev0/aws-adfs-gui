"""FastAPI web application for AWS ADFS GUI."""

import json
import os

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .adfs_auth import authenticator
from .aws_credentials import command_builder, credentials_manager
from .command_executor import executor
from .config import config
from .models import (
    ADFSCredentials,
    AuthenticationRequest,
    AWSProfile,
    CommandRequest,
    CommandResult,
    ConnectionSettings,
    ExportRequest,
)

app = FastAPI(
    title="AWS ADFS GUI",
    description="Web-based GUI for executing AWS commands across multiple profiles",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for the frontend
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections and profile states."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []
        self.connected_profiles: set[str] = set()
        self.profile_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        # Remove from profile connections
        for connections in self.profile_connections.values():
            if websocket in connections:
                connections.remove(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            # Connection might be closed
            self.disconnect(websocket)

    async def broadcast(self, message: dict) -> None:
        """Broadcast a message to all connected WebSockets."""
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                # Connection might be closed
                self.disconnect(connection)

    async def connect_profile(self, profile: str, websocket: WebSocket, credentials: dict | None = None) -> None:
        """Connect a profile and notify the client."""
        if profile not in self.profile_connections:
            self.profile_connections[profile] = set()

        self.profile_connections[profile].add(websocket)

        # Send connecting status
        await self.send_personal_message(
            {"type": "connection_status", "profile": profile, "status": "connecting"},
            websocket,
        )

        try:
            # Check if profile is valid
            if profile not in config.get_profile_names():
                await self.send_personal_message(
                    {
                        "type": "connection_status",
                        "profile": profile,
                        "status": "disconnected",
                        "message": f"Profile '{profile}' not found in configuration",
                    },
                    websocket,
                )
                return

            # Check if already authenticated
            if authenticator.is_authenticated(profile):
                self.connected_profiles.add(profile)
                await self.send_personal_message(
                    {
                        "type": "connection_status",
                        "profile": profile,
                        "status": "connected",
                        "message": f"Profile '{profile}' already authenticated",
                    },
                    websocket,
                )
                return

            # If credentials provided, attempt authentication
            if credentials:
                try:
                    adfs_creds = ADFSCredentials(
                        username=credentials.get("username", ""),
                        password=credentials.get("password", ""),
                        adfs_host=credentials.get("adfs_host", ""),
                        certificate_path=credentials.get("certificate_path"),
                    )

                    settings = ConnectionSettings(
                        timeout=credentials.get("timeout", 30),
                        retries=credentials.get("retries", 3),
                        no_sspi=credentials.get("no_sspi", True),
                        env_mode=credentials.get("env_mode", True),
                    )

                    auth_request = AuthenticationRequest(profile=profile, credentials=adfs_creds, settings=settings)

                    # Perform authentication
                    success, message = await authenticator.authenticate(auth_request)

                    if success:
                        self.connected_profiles.add(profile)
                        await self.send_personal_message(
                            {
                                "type": "connection_status",
                                "profile": profile,
                                "status": "connected",
                                "message": message,
                            },
                            websocket,
                        )
                    else:
                        await self.send_personal_message(
                            {
                                "type": "connection_status",
                                "profile": profile,
                                "status": "disconnected",
                                "message": message,
                            },
                            websocket,
                        )

                except Exception as e:
                    await self.send_personal_message(
                        {
                            "type": "connection_status",
                            "profile": profile,
                            "status": "disconnected",
                            "message": f"Authentication error: {str(e)}",
                        },
                        websocket,
                    )
            else:
                # No credentials provided - request them
                await self.send_personal_message(
                    {
                        "type": "connection_status",
                        "profile": profile,
                        "status": "disconnected",
                        "message": "Credentials required. Please configure ADFS settings first.",
                    },
                    websocket,
                )

        except Exception as e:
            await self.send_personal_message(
                {
                    "type": "connection_status",
                    "profile": profile,
                    "status": "disconnected",
                    "message": f"Connection error: {str(e)}",
                },
                websocket,
            )

    async def disconnect_profile(self, profile: str, websocket: WebSocket | None = None) -> None:
        """Disconnect a profile and notify clients."""
        if profile in self.connected_profiles:
            self.connected_profiles.remove(profile)

        # Remove WebSocket from profile connections
        if websocket and profile in self.profile_connections:
            self.profile_connections[profile].discard(websocket)

        # Notify all connections about disconnection
        await self.broadcast(
            {
                "type": "connection_status",
                "profile": profile,
                "status": "disconnected",
                "message": f"Profile '{profile}' disconnected",
            }
        )

        # Logout the profile
        authenticator.logout(profile)

    def disconnect_all(self) -> None:
        """Disconnect all profiles and clear connections."""
        self.connected_profiles.clear()
        self.profile_connections.clear()
        authenticator.logout_all()


manager = ConnectionManager()


@app.get("/")
async def get_index() -> FileResponse:
    """Serve the main application page."""
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "static")
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/api/profiles")
async def get_profiles() -> dict:
    """Get all AWS profiles organized by groups."""
    return config.get_profiles()


@app.get("/api/profiles/names")
async def get_profile_names() -> list:
    """Get all profile names as a flat list."""
    return config.get_profile_names()


@app.post("/api/profiles")
async def add_profile(profile: AWSProfile) -> dict:
    """Add a new AWS profile."""
    config.add_profile(profile)
    return {"message": "Profile added successfully"}


@app.delete("/api/profiles/{profile_name}")
async def remove_profile(profile_name: str) -> dict:
    """Remove an AWS profile."""
    if config.remove_profile(profile_name):
        return {"message": "Profile removed successfully"}
    else:
        raise HTTPException(status_code=404, detail="Profile not found")


@app.get("/api/history")
async def get_command_history() -> list:
    """Get command execution history."""
    return executor.get_command_history()


@app.delete("/api/history")
async def clear_command_history() -> dict:
    """Clear command execution history."""
    executor.clear_history()
    return {"message": "Command history cleared"}


@app.post("/api/auth/test")
async def test_credentials(credentials: ADFSCredentials) -> dict:
    """Test ADFS credentials without authenticating a specific profile."""
    try:
        success, message = await authenticator.test_credentials(credentials)
        return {"success": success, "message": message}
    except Exception as e:
        return {"success": False, "message": f"Test failed: {str(e)}"}


@app.post("/api/auth/login")
async def login_profile(request: AuthenticationRequest) -> dict:
    """Authenticate a specific profile with ADFS."""
    try:
        success, message = await authenticator.authenticate(request)
        return {"success": success, "message": message, "profile": request.profile}
    except Exception as e:
        return {
            "success": False,
            "message": f"Login failed: {str(e)}",
            "profile": request.profile,
        }


@app.post("/api/auth/logout/{profile}")
async def logout_profile(profile: str) -> dict:
    """Logout a specific profile."""
    try:
        authenticator.logout(profile)
        await manager.disconnect_profile(profile)
        return {"success": True, "message": f"Profile '{profile}' logged out"}
    except Exception as e:
        return {"success": False, "message": f"Logout failed: {str(e)}"}


@app.post("/api/auth/logout-all")
async def logout_all_profiles() -> dict:
    """Logout all profiles."""
    try:
        manager.disconnect_all()
        return {"success": True, "message": "All profiles logged out"}
    except Exception as e:
        return {"success": False, "message": f"Logout all failed: {str(e)}"}


@app.get("/api/auth/status")
async def get_auth_status() -> dict:
    """Get authentication status for all profiles."""
    profile_names = config.get_profile_names()
    status = {}

    for profile in profile_names:
        status[profile] = {
            "authenticated": authenticator.is_authenticated(profile),
            "connected": profile in manager.connected_profiles,
        }

    return {"profiles": status, "connected_count": len(manager.connected_profiles)}


# New credential status endpoints
@app.get("/api/credentials/status")
async def get_credentials_status() -> dict:
    """Get AWS credentials status for all profiles."""
    try:
        return credentials_manager.get_all_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get credentials status: {str(e)}")


@app.get("/api/credentials/status/{profile_name}")
async def get_profile_credentials_status(profile_name: str) -> dict:
    """Get AWS credentials status for a specific profile."""
    try:
        return credentials_manager.get_profile_status(profile_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status for {profile_name}: {str(e)}")


@app.post("/api/credentials/validate")
async def validate_all_credentials() -> dict:
    """Validate AWS credentials for all configured profiles."""
    try:
        # Get all profiles from config
        all_profiles = []
        for group_profiles in config.get_profiles().values():
            all_profiles.extend(group_profiles)

        # Validate all profiles
        status_results = await credentials_manager.validate_all_profiles(all_profiles)

        return {"status": "completed", "profiles": status_results, "summary": credentials_manager.get_status_summary()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@app.post("/api/credentials/validate/{profile_name}")
async def validate_profile_credentials(profile_name: str) -> dict:
    """Validate AWS credentials for a specific profile."""
    try:
        profile = config.get_profile_by_name(profile_name)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile '{profile_name}' not found")

        results = await credentials_manager.validate_all_profiles([profile])
        return results.get(profile_name, {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed for {profile_name}: {str(e)}")


@app.get("/api/credentials/summary")
async def get_credentials_summary() -> dict:
    """Get a summary of credentials status across all profiles."""
    try:
        summary = credentials_manager.get_status_summary()
        return {
            "summary": summary,
            "total_profiles": sum(summary.values()),
            "last_updated": credentials_manager.profile_status.get("last_global_update", None),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@app.post("/api/commands/build-aws-adfs")
async def build_aws_adfs_command(profile_name: str, adfs_host: str, options: dict | None = None) -> dict:
    """Build a flexible aws-adfs command with custom options."""
    try:
        command_options = options or {}
        cmd = command_builder.build_aws_adfs_command(profile_name, adfs_host, **command_options)
        return {"command": cmd, "command_string": " ".join(cmd), "profile": profile_name, "options": command_options}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Command building failed: {str(e)}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Enhanced WebSocket endpoint for real-time communication."""
    await manager.connect(websocket)

    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")

            if message_type == "connect_profile":
                profile = message.get("profile")
                credentials = message.get("credentials")
                if profile:
                    await manager.connect_profile(profile, websocket, credentials)

            elif message_type == "disconnect_profile":
                profile = message.get("profile")
                if profile:
                    await manager.disconnect_profile(profile, websocket)

            elif message_type == "execute_command":
                # Handle command execution
                command = message.get("command")
                profiles = message.get("profiles", [])

                if command and profiles:
                    # Create command request
                    command_request = CommandRequest(
                        command=command,
                        profiles=profiles,
                        timeout=message.get("timeout", 30),
                    )

                    # Execute command for all selected profiles
                    for profile in profiles:
                        if profile in manager.connected_profiles:
                            try:
                                result = await executor.execute_command(command_request)
                                # Send result back to client
                                await manager.send_personal_message(
                                    {
                                        "type": "command_result",
                                        "profile": profile,
                                        "result": result.model_dump(),
                                    },
                                    websocket,
                                )
                            except Exception as e:
                                await manager.send_personal_message(
                                    {
                                        "type": "command_error",
                                        "profile": profile,
                                        "error": str(e),
                                    },
                                    websocket,
                                )
                        else:
                            await manager.send_personal_message(
                                {
                                    "type": "command_error",
                                    "profile": profile,
                                    "error": f"Profile '{profile}' not connected",
                                },
                                websocket,
                            )

            elif message_type == "validate_credentials":
                # Handle credential validation request
                try:
                    profiles = message.get("profiles", [])
                    if profiles:
                        # Validate specific profiles
                        profile_objects = [
                            config.get_profile_by_name(p) for p in profiles if config.get_profile_by_name(p)
                        ]
                        results = await credentials_manager.validate_all_profiles(profile_objects)
                    else:
                        # Validate all profiles
                        all_profiles = []
                        for group_profiles in config.get_profiles().values():
                            all_profiles.extend(group_profiles)
                        results = await credentials_manager.validate_all_profiles(all_profiles)

                    await manager.send_personal_message(
                        {
                            "type": "credentials_validation_result",
                            "results": results,
                            "summary": credentials_manager.get_status_summary(),
                        },
                        websocket,
                    )
                except Exception as e:
                    await manager.send_personal_message(
                        {"type": "credentials_validation_error", "error": str(e)},
                        websocket,
                    )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.post("/api/export")
async def export_results(export_request: ExportRequest, results: list[CommandResult]) -> dict:
    """Export command results in the specified format."""
    try:
        # This is a placeholder for export functionality
        # In a real implementation, you would process the results
        # and return the exported data in the requested format

        exported_data = {
            "timestamp": export_request.timestamp,
            "format": export_request.format,
            "include_metadata": export_request.include_metadata,
            "results_count": len(results),
            "results": [result.model_dump() for result in results],
        }

        return {"success": True, "data": exported_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


def run_app(host: str = "127.0.0.1", port: int = 8000, reload: bool = True) -> None:
    """Run the FastAPI application."""
    uvicorn.run("aws_adfs_gui.web_app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    run_app()
