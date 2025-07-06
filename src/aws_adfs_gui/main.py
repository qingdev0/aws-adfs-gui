"""Main entry point for AWS ADFS GUI application."""

import sys

import uvicorn

from .web_app import app


def main() -> None:
    """Main entry point for the CLI."""
    if len(sys.argv) < 2:
        print("Usage: python -m aws_adfs_gui.main <command>")
        print("Commands:")
        print("  web    Start the web application")
        sys.exit(1)

    command = sys.argv[1]

    if command == "web":
        start_web_server()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


def start_web_server() -> None:
    """Start the web server."""
    print("Starting AWS ADFS GUI web application...")
    print("Usage: python -m aws_adfs_gui.main web")

    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error starting web server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
