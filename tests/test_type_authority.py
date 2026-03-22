"""
Tests for Type, Authority, and Profile calculation.

Tests:
- HDType enum and type determination logic
- Authority enum and authority hierarchy
- Profile model and calculation
- TypeAuthorityCalculator integration
- Edge cases and validation
"""

import pytest

from human_design.models.bodygraph import BirthInfo, RawBodyGraph
from human_design.models.coordinates import LocalTime
from human_design.models.type_authority import Authority, HDType, Profile, TypeAuthorityCalculator
from datetime import datetime


class TestHDType:
    """Tests for HDType enum."""

    def test_hd_type_values(self):
        """Test HDType enum has all 5 types."""
        assert HDType.INITIATOR.value == "Initiator"
        assert HDType.BUILDER.value == "Builder"
        assert HDType.SPECIALIST.value == "Specialist"
        assert HDType.COORDINATOR.value == "Coordinator"
        assert HDType.OBSERVER.value == "Observer"

    def test_all_types_present(self):
        """Test all 5 types are defined."""
        types = list(HDType)
        assert len(types) == 5


class TestAuthority:
    """Tests for Authority enum."""

    def test_authority_values(self):
        """Test Authority enum has all 7 authorities."""
        assert Authority.EMOTIONAL.value == "Emotional"
        assert Authority.SACRAL.value == "Sacral"
        assert Authority.SPLENIC.value == "Splenic"
        assert Authority.EGO.value == "Ego"
        assert Authority.SELF.value == "Self"
        assert Authority.MENTAL.value == "Mental"
        assert Authority.LUNAR.value == "Lunar"

    def test_all_authorities_present(self):
        """Test all 7 authorities are defined."""
        authorities = list(Authority)
        assert len(authorities) == 7


class TestProfile:
    """Tests for Profile model."""

    @pytest.mark.parametrize(
        "conscious,unconscious,expected_notation,expected_name",
        [
            (1, 3, "1/3", "Investigator/Martyr"),
            (1, 4, "1/4", "Investigator/Opportunist"),
            (2, 4, "2/4", "Hermit/Opportunist"),
            (2, 5, "2/5", "Hermit/Heretic"),
            (3, 5, "3/5", "Martyr/Heretic"),
            (3, 6, "3/6", "Martyr/Role Model"),
            (4, 6, "4/6", "Opportunist/Role Model"),
            (4, 1, "4/1", "Opportunist/Investigator"),
            (5, 1, "5/1", "Heretic/Investigator"),
            (5, 2, "5/2", "Heretic/Hermit"),
            (6, 2, "6/2", "Role Model/Hermit"),
            (6, 3, "6/3", "Role Model/Martyr"),
        ],
    )
    def test_profile_notation_and_name(
        self, conscious, unconscious, expected_notation, expected_name
    ):
        """Test all 12 profile notations and names."""
        profile = Profile(conscious_line=conscious, unconscious_line=unconscious)
        assert profile.profile_notation == expected_notation
        assert profile.profile_name == expected_name

    def test_profile_properties(self):
        """Test profile model properties."""
        profile = Profile(conscious_line=4, unconscious_line=6)
        assert profile.conscious_line == 4
        assert profile.unconscious_line == 6
        assert profile.profile_notation == "4/6"
        assert profile.profile_name == "Opportunist/Role Model"


class TestTypeAuthorityCalculator:
    """Tests for TypeAuthorityCalculator with real bodygraphs."""

    def test_calculator_with_real_chart(self):
        """Test calculator works with real astronomical data."""
        bg = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        calculator = TypeAuthorityCalculator(bg)

        # Type should be one of the 5 types
        hd_type = calculator.calculate_type()
        assert hd_type in HDType

        # Authority should be one of the 7 authorities
        authority = calculator.calculate_authority()
        assert authority in Authority

        # Profile should be valid
        profile = calculator.calculate_profile()
        assert 1 <= profile.conscious_line <= 6
        assert 1 <= profile.unconscious_line <= 6
        assert profile.profile_notation in [
            "1/3",
            "1/4",
            "2/4",
            "2/5",
            "3/5",
            "3/6",
            "4/6",
            "4/1",
            "5/1",
            "5/2",
            "6/2",
            "6/3",
        ]

    def test_authority_hierarchy(self):
        """Test authority follows hierarchical precedence."""
        # This test validates the authority calculation logic
        # Authority order: Emotional > Sacral > Splenic > Ego > Self > Mental > Lunar
        bg = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        calculator = TypeAuthorityCalculator(bg)
        authority = calculator.calculate_authority()

        # Validate that if Emotional is defined, authority is Emotional
        if "EMOTION" in bg.defined_centers:
            assert authority == Authority.EMOTIONAL
        # Validate that if Sacral is defined and no Emotional, authority is Sacral
        elif "LIFEFORCE" in bg.defined_centers:
            assert authority == Authority.SACRAL
        # And so on through the hierarchy


class TestRawBodyGraphIntegration:
    """Tests for RawBodyGraph type/authority/profile integration."""

    def test_bodygraph_has_type_property(self):
        """Test RawBodyGraph has type computed property."""
        bg = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        # Type property should exist and return HDType
        assert hasattr(bg, "type")
        assert isinstance(bg.type, HDType)

    def test_bodygraph_has_authority_property(self):
        """Test RawBodyGraph has authority computed property."""
        bg = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        # Authority property should exist and return Authority
        assert hasattr(bg, "authority")
        assert isinstance(bg.authority, Authority)

    def test_bodygraph_has_profile_property(self):
        """Test RawBodyGraph has profile computed property."""
        bg = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        # Profile property should exist and return Profile
        assert hasattr(bg, "profile")
        assert isinstance(bg.profile, Profile)
        assert bg.profile.profile_notation in [
            "1/3",
            "1/4",
            "2/4",
            "2/5",
            "3/5",
            "3/6",
            "4/6",
            "4/1",
            "5/1",
            "5/2",
            "6/2",
            "6/3",
        ]

    def test_type_authority_profile_consistency(self):
        """Test type, authority, and profile are consistent for a chart."""
        bg = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        # All properties should be accessible
        hd_type = bg.type
        authority = bg.authority
        profile = bg.profile

        # Type-specific validations
        if hd_type == HDType.OBSERVER:
            # Observers have no defined centers and Lunar authority
            assert len(bg.defined_centers) == 0
            assert authority == Authority.LUNAR
        elif hd_type in (HDType.BUILDER, HDType.SPECIALIST):
            # Builders and Specialists have Sacral defined
            assert "LIFEFORCE" in bg.defined_centers
        elif hd_type == HDType.INITIATOR:
            # Initiators have motor-to-throat but no Sacral
            assert "LIFEFORCE" not in bg.defined_centers

        # Profile should always be one of the 12 valid profiles
        assert profile.profile_notation in [
            "1/3",
            "1/4",
            "2/4",
            "2/5",
            "3/5",
            "3/6",
            "4/6",
            "4/1",
            "5/1",
            "5/2",
            "6/2",
            "6/3",
        ]


class TestEdgeCases:
    """Test edge cases and validation."""

    def test_motor_to_throat_detection(self):
        """Test motor-to-throat connection detection."""
        bg = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        calculator = TypeAuthorityCalculator(bg)
        has_motor_throat = calculator._has_motor_to_throat_connection()

        # If motor-to-throat exists, at least one channel should connect motor to throat
        if has_motor_throat:
            motor_centers = {"WILLPOWER", "EMOTION", "DRIVE", "LIFEFORCE"}
            throat_center = "EXPRESSION"

            motor_throat_channels = [
                ch
                for ch in bg.active_channels
                if throat_center in {ch.center_a, ch.center_b}
                and any(motor in {ch.center_a, ch.center_b} for motor in motor_centers)
            ]
            assert len(motor_throat_channels) > 0

    def test_profile_sun_validation(self):
        """Test profile calculation requires Sun activations."""
        bg = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        # Profile should be calculable (Sun always present)
        profile = bg.profile
        assert profile is not None
        assert 1 <= profile.conscious_line <= 6
        assert 1 <= profile.unconscious_line <= 6
