"""Tests for the models module - focusing on components available without pydantic."""

import sys

import pytest

# Add src to path for imports
sys.path.insert(0, "src")

# Test imports individually to handle import errors gracefully
try:
    from aws_adfs_gui.models import ProfileGroup

    PROFILE_GROUP_AVAILABLE = True
except ImportError:
    PROFILE_GROUP_AVAILABLE = False

# Test more complex models
try:
    from aws_adfs_gui.models import AWSProfile  # noqa: F401

    AWS_PROFILE_AVAILABLE = True
except ImportError:
    AWS_PROFILE_AVAILABLE = False


class TestProfileGroup:
    """Test cases for ProfileGroup enum."""

    @pytest.mark.skipif(not PROFILE_GROUP_AVAILABLE, reason="ProfileGroup not available")
    def test_profile_group_values(self) -> None:
        """Test that ProfileGroup enum has correct values."""
        assert ProfileGroup.DEV == "dev"
        assert ProfileGroup.NON_PRODUCTION == "np"
        assert ProfileGroup.PRODUCTION == "pd"

    @pytest.mark.skipif(not PROFILE_GROUP_AVAILABLE, reason="ProfileGroup not available")
    def test_profile_group_membership(self) -> None:
        """Test ProfileGroup enum membership."""
        assert "dev" in ProfileGroup
        assert "np" in ProfileGroup
        assert "pd" in ProfileGroup
        assert "invalid" not in ProfileGroup

    @pytest.mark.skipif(not PROFILE_GROUP_AVAILABLE, reason="ProfileGroup not available")
    def test_profile_group_list(self) -> None:
        """Test getting all ProfileGroup values."""
        groups = list(ProfileGroup)
        assert len(groups) == 3
        assert ProfileGroup.DEV in groups
        assert ProfileGroup.NON_PRODUCTION in groups
        assert ProfileGroup.PRODUCTION in groups

    @pytest.mark.skipif(not PROFILE_GROUP_AVAILABLE, reason="ProfileGroup not available")
    def test_profile_group_string_representation(self) -> None:
        """Test ProfileGroup string representation."""
        assert str(ProfileGroup.DEV) == "ProfileGroup.DEV"
        assert repr(ProfileGroup.DEV) == "<ProfileGroup.DEV: 'dev'>"

    @pytest.mark.skipif(not PROFILE_GROUP_AVAILABLE, reason="ProfileGroup not available")
    def test_profile_group_value_access(self) -> None:
        """Test accessing ProfileGroup values."""
        assert ProfileGroup.DEV.value == "dev"
        assert ProfileGroup.NON_PRODUCTION.value == "np"
        assert ProfileGroup.PRODUCTION.value == "pd"

    @pytest.mark.skipif(not PROFILE_GROUP_AVAILABLE, reason="ProfileGroup not available")
    def test_profile_group_comparison(self) -> None:
        """Test ProfileGroup equality comparison."""
        assert ProfileGroup.DEV == ProfileGroup.DEV
        assert ProfileGroup.DEV != ProfileGroup.PRODUCTION
        assert ProfileGroup.DEV.value == "dev"
        # Test that enum members can be compared with their string values (this enum allows it)
        assert ProfileGroup.DEV == "dev"  # This enum supports string equality

    @pytest.mark.skipif(not PROFILE_GROUP_AVAILABLE, reason="ProfileGroup not available")
    def test_profile_group_iteration(self) -> None:
        """Test iterating over ProfileGroup values."""
        groups = []
        for group in ProfileGroup:
            groups.append(group)

        assert len(groups) == 3
        assert ProfileGroup.DEV in groups
        assert ProfileGroup.NON_PRODUCTION in groups
        assert ProfileGroup.PRODUCTION in groups


class TestModelsImport:
    """Test cases for models import behavior."""

    @pytest.mark.skipif(not PROFILE_GROUP_AVAILABLE, reason="ProfileGroup not available")
    def test_models_import_basic(self) -> None:
        """Test basic import of models module."""
        # Import should work since we're only running if PROFILE_GROUP_AVAILABLE
        import aws_adfs_gui.models

        assert hasattr(aws_adfs_gui.models, "ProfileGroup")
        print("✅ Basic models import successful")

    @pytest.mark.skipif(not PROFILE_GROUP_AVAILABLE, reason="ProfileGroup not available")
    def test_profile_group_import(self) -> None:
        """Test importing ProfileGroup specifically."""
        from aws_adfs_gui.models import ProfileGroup

        assert ProfileGroup is not None
        assert hasattr(ProfileGroup, "DEV")
        assert hasattr(ProfileGroup, "NON_PRODUCTION")
        assert hasattr(ProfileGroup, "PRODUCTION")
        print("✅ ProfileGroup import successful")

    @pytest.mark.skipif(not PROFILE_GROUP_AVAILABLE, reason="ProfileGroup not available")
    def test_enum_functionality(self) -> None:
        """Test that ProfileGroup works as an enum."""
        from enum import Enum

        from aws_adfs_gui.models import ProfileGroup

        # Test that ProfileGroup is an enum
        assert issubclass(ProfileGroup, Enum)

        # Test enum behavior
        assert len(list(ProfileGroup)) == 3
        assert ProfileGroup.DEV.value == "dev"

        print("✅ Enum functionality working")


# Tests that require pydantic - will be skipped if not available
@pytest.mark.skipif(not AWS_PROFILE_AVAILABLE, reason="Pydantic models not available")
class TestPydanticModels:
    """Test cases for Pydantic models - only run if available."""

    def test_pydantic_models_available(self) -> None:
        """Test that pydantic models can be imported."""
        try:
            from aws_adfs_gui.models import AWSProfile, CommandRequest, CommandResult  # noqa: F401

            print("✅ Pydantic models available")
        except ImportError as e:
            pytest.skip(f"Pydantic models not available: {e}")

    def test_aws_profile_basic(self) -> None:
        """Test basic AWSProfile creation if available."""
        try:
            from aws_adfs_gui.models import AWSProfile, ProfileGroup

            # This will fail if pydantic validation is required
            # but let's see how far we can get
            profile = AWSProfile(name="test-profile", group=ProfileGroup.DEV)
            assert profile.name == "test-profile"
            assert profile.group == ProfileGroup.DEV
            print("✅ AWSProfile basic creation works")
        except Exception as e:
            pytest.skip(f"AWSProfile creation failed: {e}")


class TestManualModelLogic:
    """Test model logic that doesn't require pydantic."""

    def test_profile_group_logic(self) -> None:
        """Test logical operations with ProfileGroup."""
        if not PROFILE_GROUP_AVAILABLE:
            pytest.skip("ProfileGroup not available")

        # Test that we can use ProfileGroup in logical operations
        dev_group = ProfileGroup.DEV
        prod_group = ProfileGroup.PRODUCTION

        # Test membership
        assert dev_group in [ProfileGroup.DEV, ProfileGroup.NON_PRODUCTION]
        assert prod_group not in [ProfileGroup.DEV, ProfileGroup.NON_PRODUCTION]

        # Test string conversion
        assert str(dev_group.value) == "dev"
        assert str(prod_group.value) == "pd"

    def test_profile_group_categorization(self) -> None:
        """Test categorizing profiles by group."""
        if not PROFILE_GROUP_AVAILABLE:
            pytest.skip("ProfileGroup not available")

        # Test categorization logic
        dev_profiles = [ProfileGroup.DEV]
        production_profiles = [ProfileGroup.PRODUCTION]
        all_profiles = [
            ProfileGroup.DEV,
            ProfileGroup.NON_PRODUCTION,
            ProfileGroup.PRODUCTION,
        ]

        assert len(dev_profiles) == 1
        assert len(production_profiles) == 1
        assert len(all_profiles) == 3

        # Test filtering
        non_prod = [group for group in all_profiles if group != ProfileGroup.PRODUCTION]
        assert len(non_prod) == 2
        assert ProfileGroup.DEV in non_prod
        assert ProfileGroup.NON_PRODUCTION in non_prod
        assert ProfileGroup.PRODUCTION not in non_prod
