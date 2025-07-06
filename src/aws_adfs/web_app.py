"""FastAPI web application for AWS ADFS GUI."""

import asyncio
import json
import os
from typing import Dict, List, Set

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .command_executor import executor
from .config import config
from .models import (
    AWSProfile,
    CommandRequest,
    CommandResult,
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
        self.active_connections: List[WebSocket] = []
        self.connected_profiles: Set[str] = set()
        self.profile_connections: Dict[str, Set[WebSocket]] = {}

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

    async def connect_profile(self, profile: str, websocket: WebSocket) -> None:
        """Connect a profile and notify the client."""
        if profile not in self.profile_connections:
            self.profile_connections[profile] = set()

        self.profile_connections[profile].add(websocket)

        # Simulate connection process
        await self.send_personal_message(
            {"type": "connection_status", "profile": profile, "status": "connecting"},
            websocket,
        )

        # Simulate connection delay
        await asyncio.sleep(1)

        # Check if profile is valid (basic validation)
        if profile in config.get_profile_names():
            self.connected_profiles.add(profile)
            await self.send_personal_message(
                {
                    "type": "connection_status",
                    "profile": profile,
                    "status": "connected",
                },
                websocket,
            )
        else:
            await self.send_personal_message(
                {
                    "type": "connection_status",
                    "profile": profile,
                    "status": "disconnected",
                },
                websocket,
            )

    async def disconnect_profile(self, profile: str, websocket: WebSocket) -> None:
        """Disconnect a profile and notify the client."""
        if profile in self.profile_connections:
            self.profile_connections[profile].discard(websocket)
            if not self.profile_connections[profile]:
                del self.profile_connections[profile]
                self.connected_profiles.discard(profile)

        await self.send_personal_message(
            {"type": "connection_status", "profile": profile, "status": "disconnected"},
            websocket,
        )


manager = ConnectionManager()


@app.get("/", response_class=HTMLResponse)  # type: ignore[misc]
async def get_index() -> HTMLResponse:
    """Serve the main HTML page."""
    html_path = os.path.join(static_dir, "index.html")
    return FileResponse(html_path)


@app.get("/api/profiles")  # type: ignore[misc]
async def get_profiles() -> dict:
    """Get all AWS profiles organized by groups."""
    return config.get_profiles()


@app.get("/api/profiles/names")  # type: ignore[misc]
async def get_profile_names() -> list:
    """Get all profile names as a flat list."""
    return config.get_profile_names()


@app.post("/api/profiles")  # type: ignore[misc]
async def add_profile(profile: AWSProfile) -> dict:
    """Add a new AWS profile."""
    config.add_profile(profile)
    return {"message": "Profile added successfully"}


@app.delete("/api/profiles/{profile_name}")  # type: ignore[misc]
async def remove_profile(profile_name: str) -> dict:
    """Remove an AWS profile."""
    if config.remove_profile(profile_name):
        return {"message": "Profile removed successfully"}
    else:
        raise HTTPException(status_code=404, detail="Profile not found")


@app.get("/api/history")  # type: ignore[misc]
async def get_command_history() -> list:
    """Get command history."""
    return executor.get_command_history()


@app.delete("/api/history")  # type: ignore[misc]
async def clear_command_history() -> dict:
    """Clear command history."""
    executor.clear_history()
    return {"message": "History cleared successfully"}


@app.websocket("/ws")  # type: ignore[misc]
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
                if profile:
                    await manager.connect_profile(profile, websocket)

            elif message_type == "disconnect_profile":
                profile = message.get("profile")
                if profile:
                    await manager.disconnect_profile(profile, websocket)

            elif message_type == "execute_command":
                profile = message.get("profile")
                command = message.get("command")

                if profile and command:
                    # Create command request
                    request = CommandRequest(
                        command=command, profiles=[profile], timeout=300
                    )

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
        await manager.send_personal_message(
            {"type": "error", "message": str(e)}, websocket
        )
        manager.disconnect(websocket)


@app.post("/api/export")  # type: ignore[misc]
async def export_results(
    export_request: ExportRequest, results: List[CommandResult]
) -> dict:
    """Export command results in various formats."""
    if export_request.format == "json":
        return {"format": "json", "data": [result.model_dump() for result in results]}
    elif export_request.format == "csv":
        # Convert to CSV format
        csv_lines = ["profile,success,output,error,duration"]
        for result in results:
            output = result.output.replace('"', '""') if result.output else ""
            error = result.error.replace('"', '""') if result.error else ""
            csv_lines.append(
                f'"{result.profile}","{result.success}","{output}","{error}",{result.duration}'
            )
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
    uvicorn.run("aws_adfs.web_app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    run_app()
