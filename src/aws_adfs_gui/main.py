"""Main module for AWS ADFS integration."""

import sys


def hello(name: str | None = None) -> str:
    """Say hello to someone.

    Args:
        name: The name of the person to greet. If None, greets the world.

    Returns:
        A greeting message.
    """
    if name:
        return f"Hello, {name}!"
    return "Hello, World!"


def main() -> None:
    """Main entry point for the application."""
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        try:
            from .web_app import app
        except ImportError as e:
            print(f"Web dependencies not available: {e}")
            print("Install with: uv add 'fastapi' 'uvicorn[standard]'")
            return

        import uvicorn

        print("Starting AWS ADFS GUI web application...")
        print("Usage: python -m aws_adfs_gui.main web")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        print(hello())
        print("Available commands:")
        print("  web    Start the web interface")


if __name__ == "__main__":
    main()
