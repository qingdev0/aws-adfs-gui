"""FastAPI web application for AWS ADFS GUI."""

import json
from typing import List

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
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)  # type: ignore[misc]
async def get_index() -> HTMLResponse:
    """Serve the main HTML page."""
    return FileResponse("static/index.html")


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


@app.websocket("/ws/execute")  # type: ignore[misc]
async def websocket_execute(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time command execution."""
    await websocket.accept()

    try:
        while True:
            # Receive command request
            data = await websocket.receive_text()
            request_data = json.loads(data)
            request = CommandRequest(**request_data)

            # Execute command and stream results
            async for result in executor.execute_command(request):
                await websocket.send_text(result.model_dump_json())

            # Send completion signal
            await websocket.send_text(json.dumps({"type": "complete"}))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_text(json.dumps({"type": "error", "error": str(e)}))


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
