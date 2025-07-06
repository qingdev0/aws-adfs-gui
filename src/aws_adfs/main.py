"""Main module for AWS ADFS integration."""

import sys

from .web_app import run_app


def hello(name: str | None = None) -> str:
    """Return a greeting message.

    Args:
        name: Optional name to greet. If None, uses "World".

    Returns:
        A greeting message.
    """
    if name is None:
        name = "World"
    return f"Hello, {name}!"


def main() -> None:
    """Main entry point for the application."""
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        # Run the web application
        print("Starting AWS ADFS GUI web application...")
        print("Open your browser to: http://127.0.0.1:8000")
        run_app()
    else:
        # Default behavior
        print(hello())
        print("\nTo start the web GUI, run: python -m aws_adfs.main web")


if __name__ == "__main__":
    main()
