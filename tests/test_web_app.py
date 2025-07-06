"""Tests for the web application."""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from src.aws_adfs.config import Config
from src.aws_adfs.models import AWSProfile, ProfileGroup
from src.aws_adfs.web_app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def temp_config():
    """Create a temporary config file for isolated config tests."""
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        config_path = tf.name
    try:
        yield Config(config_file=config_path)
    finally:
        if os.path.exists(config_path):
            os.remove(config_path)


class TestWebApp:
    """Test cases for the web application."""

    def test_get_profiles(self, client):
        """Test getting AWS profiles."""
        response = client.get("/api/profiles")
        assert response.status_code == 200
        data = response.json()
        assert "dev" in data
        assert "np" in data
        assert "pd" in data

    def test_get_profile_names(self, client):
        """Test getting profile names."""
        response = client.get("/api/profiles/names")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_add_profile(self, client):
        """Test adding a new profile."""
        profile_data = {
            "name": "test-profile",
            "group": "dev",
            "region": "us-west-2",
            "description": "Test profile",
        }
        response = client.post("/api/profiles", json=profile_data)
        assert response.status_code == 200
        assert response.json()["message"] == "Profile added successfully"

    def test_remove_profile(self, client):
        """Test removing a profile."""
        # First add a profile
        profile_data = {"name": "temp-profile", "group": "dev", "region": "us-west-2"}
        client.post("/api/profiles", json=profile_data)

        # Then remove it
        response = client.delete("/api/profiles/temp-profile")
        assert response.status_code == 200
        assert response.json()["message"] == "Profile removed successfully"

    def test_remove_nonexistent_profile(self, client):
        """Test removing a profile that doesn't exist."""
        response = client.delete("/api/profiles/nonexistent-profile")
        assert response.status_code == 404

    def test_get_command_history(self, client):
        """Test getting command history."""
        response = client.get("/api/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_clear_command_history(self, client):
        """Test clearing command history."""
        response = client.delete("/api/history")
        assert response.status_code == 200
        assert response.json()["message"] == "History cleared successfully"


class TestConfig:
    """Test cases for configuration management."""

    def test_get_profiles(self, temp_config):
        """Test getting profiles from config."""
        profiles = temp_config.get_profiles()
        assert isinstance(profiles, dict)
        assert "dev" in profiles
        assert "np" in profiles
        assert "pd" in profiles

    def test_get_profile_names(self, temp_config):
        """Test getting profile names from config."""
        names = temp_config.get_profile_names()
        assert isinstance(names, list)
        assert len(names) > 0

    def test_get_profile_by_name(self, temp_config):
        """Test getting a specific profile by name."""
        # Test with existing profile
        profile = temp_config.get_profile_by_name("aws-dev-eu")
        assert profile is not None
        assert profile.name == "aws-dev-eu"
        assert profile.group == ProfileGroup.DEV

        # Test with non-existent profile
        profile = temp_config.get_profile_by_name("nonexistent-profile")
        assert profile is None

    def test_add_and_remove_profile(self, temp_config):
        """Test adding and removing a profile."""
        # Add a test profile
        test_profile = AWSProfile(name="test-profile", group=ProfileGroup.DEV, region="us-west-2")
        temp_config.add_profile(test_profile)

        # Verify it was added
        profile = temp_config.get_profile_by_name("test-profile")
        assert profile is not None
        assert profile.name == "test-profile"

        # Remove it
        success = temp_config.remove_profile("test-profile")
        assert success is True

        # Verify it was removed
        profile = temp_config.get_profile_by_name("test-profile")
        assert profile is None
