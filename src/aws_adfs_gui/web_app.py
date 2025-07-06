"""FastAPI web application for AWS ADFS GUI."""

import json
import os

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .adfs_auth import authenticator
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
        """Disconnect a profile and notify the client."""
        if profile in self.profile_connections:
            if websocket:
                self.profile_connections[profile].discard(websocket)
                if not self.profile_connections[profile]:
                    del self.profile_connections[profile]
                    self.connected_profiles.discard(profile)

                await self.send_personal_message(
                    {
                        "type": "connection_status",
                        "profile": profile,
                        "status": "disconnected",
                    },
                    websocket,
                )
            else:
                # Disconnect all websockets for this profile
                for ws in self.profile_connections[profile].copy():
                    await self.send_personal_message(
                        {
                            "type": "connection_status",
                            "profile": profile,
                            "status": "disconnected",
                        },
                        ws,
                    )
                del self.profile_connections[profile]
                self.connected_profiles.discard(profile)

    def disconnect_all(self) -> None:
        """Disconnect all profiles."""
        self.profile_connections.clear()
        self.connected_profiles.clear()


manager = ConnectionManager()


@app.get("/")
async def get_index() -> FileResponse:
    """Serve the main HTML page."""
    html_path = os.path.join(static_dir, "index.html")
    return FileResponse(html_path)


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
    """Get command history."""
    return executor.get_command_history()


@app.delete("/api/history")
async def clear_command_history() -> dict:
    """Clear command history."""
    executor.clear_history()
    return {"message": "History cleared successfully"}


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
    """Log out a specific profile."""
    try:
        authenticator.logout(profile)
        await manager.disconnect_profile(profile)
        return {
            "success": True,
            "message": f"Profile '{profile}' logged out successfully",
        }
    except Exception as e:
        return {"success": False, "message": f"Logout failed: {str(e)}"}


@app.post("/api/auth/logout-all")
async def logout_all_profiles() -> dict:
    """Log out all profiles."""
    try:
        authenticator.logout_all()
        manager.disconnect_all()
        return {"success": True, "message": "All profiles logged out successfully"}
    except Exception as e:
        return {"success": False, "message": f"Logout failed: {str(e)}"}


@app.get("/api/auth/status")
async def get_auth_status() -> dict:
    """Get authentication status for all profiles."""
    try:
        profile_names = config.get_profile_names()
        status = {}
        for profile in profile_names:
            status[profile] = {
                "authenticated": authenticator.is_authenticated(profile),
                "connected": profile in manager.connected_profiles,
            }
        return {"success": True, "profiles": status}
    except Exception as e:
        return {"success": False, "message": f"Status check failed: {str(e)}"}


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
                profile = message.get("profile")
                command = message.get("command")

                if profile and command:
                    # Create command request
                    request = CommandRequest(command=command, profiles=[profile], timeout=300)

                    # Send command start notification
                    await manager.send_personal_message(
                        {
                            "type": "command_output",
                            "profile": profile,
                            "output": f"$ {command}",
                            "is_error": False,
                        },
                        websocket,
                    )

                    # Execute command and stream results
                    try:
                        async for result in executor.execute_command(request):
                            if result.profile == profile:
                                # Send output
                                if result.output:
                                    await manager.send_personal_message(
                                        {
                                            "type": "command_output",
                                            "profile": profile,
                                            "output": result.output,
                                            "is_error": False,
                                        },
                                        websocket,
                                    )

                                # Send error if any
                                if result.error:
                                    await manager.send_personal_message(
                                        {
                                            "type": "command_output",
                                            "profile": profile,
                                            "output": result.error,
                                            "is_error": True,
                                        },
                                        websocket,
                                    )

                                # Send completion
                                await manager.send_personal_message(
                                    {
                                        "type": "command_complete",
                                        "profile": profile,
                                        "success": result.success,
                                        "duration": result.duration,
                                    },
                                    websocket,
                                )

                    except Exception as e:
                        await manager.send_personal_message(
                            {
                                "type": "command_output",
                                "profile": profile,
                                "output": f"Error: {str(e)}",
                                "is_error": True,
                            },
                            websocket,
                        )

                        await manager.send_personal_message(
                            {
                                "type": "command_complete",
                                "profile": profile,
                                "success": False,
                                "duration": 0,
                            },
                            websocket,
                        )

            else:
                await manager.send_personal_message(
                    {
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                    },
                    websocket,
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        await manager.send_personal_message({"type": "error", "message": str(e)}, websocket)
        manager.disconnect(websocket)


@app.post("/api/export")
async def export_results(export_request: ExportRequest, results: list[CommandResult]) -> dict:
    """Export command results in various formats."""
    if export_request.format == "json":
        return {"format": "json", "data": [result.model_dump() for result in results]}
    elif export_request.format == "csv":
        # Convert to CSV format
        csv_lines = ["profile,success,output,error,duration"]
        for result in results:
            output = result.output.replace('"', '""') if result.output else ""
            error = result.error.replace('"', '""') if result.error else ""
            csv_lines.append(f'"{result.profile}","{result.success}","{output}","{error}",{result.duration}')
        return {"format": "csv", "data": "\n".join(csv_lines)}
    elif export_request.format == "txt":
        # Convert to plain text format
        text_lines = []
        for result in results:
            text_lines.append(f"Profile: {result.profile}")
            text_lines.append(f"Success: {result.success}")
            text_lines.append(f"Duration: {result.duration:.2f}s")
            if result.output:
                text_lines.append(f"Output:\n{result.output}")
            if result.error:
                text_lines.append(f"Error:\n{result.error}")
            text_lines.append("-" * 50)

        return {"format": "txt", "data": "\n".join(text_lines)}
    else:
        raise HTTPException(status_code=400, detail="Unsupported export format")


def run_app(host: str = "127.0.0.1", port: int = 8000, reload: bool = True) -> None:
    """Run the FastAPI application."""
    uvicorn.run("src.aws_adfs_gui.web_app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    run_app()
