"""
Tests for channel formation logic.

Tests:
- ChannelDefinition model
- CenterRegistry singleton
- ChannelRegistry singleton
- RawBodyGraph.active_channels computed property
- RawBodyGraph.defined_centers computed property
"""

import pytest

from human_design.models.channel import ChannelDefinition, ChannelRegistry, CenterRegistry
from human_design.models.core import CenterName, GateNumber


class TestChannelDefinition:
    """Tests for ChannelDefinition model."""

    def test_channel_definition_creation(self):
        """Test creating a ChannelDefinition."""
        channel = ChannelDefinition(
            channel_id=1,
            name="Test Channel",
            gate_a=1,
            gate_b=8,
            center_a="IDENTITY",
            center_b="EXPRESSION",
        )
        assert channel.channel_id == 1
        assert channel.name == "Test Channel"
        assert channel.gate_a == 1
        assert channel.gate_b == 8
        assert channel.center_a == "IDENTITY"
        assert channel.center_b == "EXPRESSION"

    @pytest.mark.parametrize(
        "activated_gates,expected",
        [
            ({1, 8}, True),  # Both gates activated
            ({1}, False),  # Only gate_a activated
            ({8}, False),  # Only gate_b activated
            (set(), False),  # No gates activated
            ({1, 8, 10, 20}, True),  # Both gates + extras
        ],
    )
    def test_is_formed_by(self, activated_gates, expected):
        """Test channel formation detection."""
        channel = ChannelDefinition(
            channel_id=1,
            name="Test Channel",
            gate_a=1,
            gate_b=8,
            center_a="IDENTITY",
            center_b="EXPRESSION",
        )
        assert channel.is_formed_by(activated_gates) == expected

    def test_gates_property(self):
        """Test gates property returns tuple."""
        channel = ChannelDefinition(
            channel_id=1,
            name="Test Channel",
            gate_a=1,
            gate_b=8,
            center_a="IDENTITY",
            center_b="EXPRESSION",
        )
        assert channel.gates == (1, 8)

    def test_centers_property(self):
        """Test centers property returns tuple."""
        channel = ChannelDefinition(
            channel_id=1,
            name="Test Channel",
            gate_a=1,
            gate_b=8,
            center_a="IDENTITY",
            center_b="EXPRESSION",
        )
        assert channel.centers == ("IDENTITY", "EXPRESSION")


class TestCenterRegistry:
    """Tests for CenterRegistry singleton."""

    def test_singleton_pattern(self):
        """Test that CenterRegistry is a singleton."""
        registry1 = CenterRegistry.load()
        registry2 = CenterRegistry.load()
        assert registry1 is registry2

    def test_load_centers(self):
        """Test loading centers from centers.yaml."""
        registry = CenterRegistry.load()
        # Test some known gate-to-center mappings
        assert registry.get_center(1) == "IDENTITY"
        assert registry.get_center(64) == "INSPIRATION"
        assert registry.get_center(5) == "LIFEFORCE"

    def test_all_gates_assigned(self):
        """Test that all 64 gates are assigned to centers."""
        registry = CenterRegistry.load()
        for gate_num in range(1, 65):
            center = registry.get_center(gate_num)
            assert center is not None
            assert isinstance(center, str)


class TestChannelRegistry:
    """Tests for ChannelRegistry singleton."""

    def test_singleton_pattern(self):
        """Test that ChannelRegistry is a singleton."""
        registry1 = ChannelRegistry.load()
        registry2 = ChannelRegistry.load()
        assert registry1 is registry2

    def test_load_channels(self):
        """Test loading channels from channels.yaml."""
        registry = ChannelRegistry.load()
        assert len(registry.all_channels) == 36

    def test_channel_structure(self):
        """Test that loaded channels have correct structure."""
        registry = ChannelRegistry.load()
        for channel in registry.all_channels:
            assert 1 <= channel.channel_id <= 36
            assert len(channel.name) > 0
            assert 1 <= channel.gate_a <= 64
            assert 1 <= channel.gate_b <= 64
            assert channel.gate_a != channel.gate_b
            assert len(channel.center_a) > 0
            assert len(channel.center_b) > 0

    @pytest.mark.parametrize(
        "activated_gates,min_expected_channels",
        [
            ({1, 8}, 1),  # Channel 1-8 formed
            ({1, 8, 10, 20}, 2),  # At least 2 channels
            ({1}, 0),  # No channels (only 1 gate)
            (set(), 0),  # No channels (no gates)
        ],
    )
    def test_get_formed_channels(self, activated_gates, min_expected_channels):
        """Test getting formed channels from gate activations."""
        registry = ChannelRegistry.load()
        formed = registry.get_formed_channels(activated_gates)
        assert len(formed) >= min_expected_channels

    def test_no_channels_with_single_gate(self):
        """Test that no channels form with only one gate."""
        registry = ChannelRegistry.load()
        for gate_num in range(1, 65):
            formed = registry.get_formed_channels({gate_num})
            assert len(formed) == 0, f"Gate {gate_num} should not form channel alone"


class TestRawBodyGraphIntegration:
    """Tests for RawBodyGraph channel integration."""

    def test_active_channels_empty_chart(self):
        """Test active_channels with no gate activations."""
        # NOTE: Cannot test empty chart - RawBodyGraph always calculates activations
        # from astronomical data. This test validates the registry handles empty sets.
        from human_design.models.channel import ChannelRegistry

        registry = ChannelRegistry.load()
        formed = registry.get_formed_channels(set())
        assert len(formed) == 0

    def test_active_channels_with_known_chart(self):
        """Test active_channels with real astronomical data."""
        from human_design.models.bodygraph import BirthInfo, RawBodyGraph
        from human_design.models.coordinates import LocalTime
        from datetime import datetime

        # Create bodygraph with real birth data
        bg = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        # Verify active_channels property works
        active_channels = bg.active_channels
        assert isinstance(active_channels, list)
        # Real chart should have some channels formed
        assert len(active_channels) > 0
        # Verify each channel is properly formed
        for channel in active_channels:
            assert channel.gate_a in bg.all_activated_gates
            assert channel.gate_b in bg.all_activated_gates

    def test_defined_centers_with_known_chart(self):
        """Test defined_centers with real astronomical data."""
        from human_design.models.bodygraph import BirthInfo, RawBodyGraph
        from human_design.models.coordinates import LocalTime
        from datetime import datetime

        # Create bodygraph with real birth data
        bg = RawBodyGraph(
            birth_info=BirthInfo(
                date="1990-01-15",
                localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
                city="Albuquerque",
                country="NM",
            )
        )

        # Verify defined_centers property works
        defined = bg.defined_centers
        assert isinstance(defined, set)
        # Real chart should have some defined centers
        assert len(defined) > 0
        # Each defined center should appear in the active channels
        for center in defined:
            assert any(
                center in (ch.center_a, ch.center_b) for ch in bg.active_channels
            )


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_channel_with_same_gate_twice(self):
        """Test that channel detection works even if same gate appears multiple times."""
        registry = ChannelRegistry.load()
        # Having gate 1 multiple times should still work
        formed = registry.get_formed_channels({1, 1, 8})
        assert len(formed) >= 1

    def test_large_activation_set(self):
        """Test with many gate activations."""
        registry = ChannelRegistry.load()
        # All gates activated - should form all 36 channels
        all_gates = set(range(1, 65))
        formed = registry.get_formed_channels(all_gates)
        assert len(formed) == 36
