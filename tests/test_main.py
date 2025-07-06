"""Tests for the main module."""

import pytest
from aws_adfs.main import hello


class TestHello:
    """Test cases for the hello function."""

    def test_hello_without_name(self) -> None:
        """Test hello function without providing a name."""
        result = hello()
        assert result == "Hello, World!"

    def test_hello_with_name(self) -> None:
        """Test hello function with a specific name."""
        result = hello("Alice")
        assert result == "Hello, Alice!"

    def test_hello_with_empty_string(self) -> None:
        """Test hello function with an empty string."""
        result = hello("")
        assert result == "Hello, !"

    def test_hello_with_none_explicitly(self) -> None:
        """Test hello function with None explicitly passed."""
        result = hello(None)
        assert result == "Hello, World!"

    @pytest.mark.parametrize(  # type: ignore[misc]
        "name,expected",
        [
            ("Bob", "Hello, Bob!"),
            ("Charlie", "Hello, Charlie!"),
            ("David", "Hello, David!"),
        ],
    )
    def test_hello_with_various_names(self, name: str, expected: str) -> None:
        """Test hello function with various names using parametrize."""
        result = hello(name)
        assert result == expected
