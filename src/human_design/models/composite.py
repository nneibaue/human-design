"""
Composite bodygraphs - combining multiple charts through gate activation stacking.

Key insight: A chart is already two transits (conscious + unconscious).
Interaction/penta/transit charts are just MORE gate activation sets stacked together.

New channels can form when charts combine:
- Sandy has Gate 1 (no channel alone)
- Heath has Gate 8 (no channel alone)
- Sandy + Heath = Channel 1-8 forms → new connection emerges
"""

from typing import TYPE_CHECKING

from pydantic import BaseModel, computed_field

from .channel import ChannelDefinition, ChannelRegistry
from .core import CenterName, GateNumber
from .type_authority import Authority, HDType, Profile, TypeAuthorityCalculator

if TYPE_CHECKING:
    from .bodygraph import RawBodyGraph


class CompositeBodyGraph(BaseModel):
    """
    Composite bodygraph created by stacking gate activations from multiple charts.

    This represents interaction charts (2 people), penta charts (3-5 people),
    multichart (2-16 people), or any chart with transit overlays.

    All existing logic (channel formation, center definition, type/authority)
    works unchanged - it operates on the union of all activated gates.

    Example:
        interaction = chart1 + chart2
        penta = chart1 + chart2 + chart3 + chart4
        with_transit = chart + transit_now()
    """

    charts: list["RawBodyGraph"]

    @property
    def all_activated_gates(self) -> set[GateNumber]:
        """
        Union of all gates from all charts.

        This is where new channels can form - gates from different charts
        can complete each other to form channels that don't exist in
        individual charts.

        Returns:
            Set of all unique gate numbers across all charts
        """
        gates: set[GateNumber] = set()
        for chart in self.charts:
            gates.update(chart.all_activated_gates)
        return gates

    @computed_field  # type: ignore
    @property
    def active_channels(self) -> list[ChannelDefinition]:
        """
        Get all channels formed by combined gate activations.

        NOTE: This may include NEW channels that don't exist in any
        individual chart. This is the essence of interaction/penta charts -
        new connections emerge when people come together.

        Returns:
            List of formed channels (may include emergent channels)
        """
        channel_registry = ChannelRegistry.load()
        return channel_registry.get_formed_channels(self.all_activated_gates)

    @computed_field  # type: ignore
    @property
    def defined_centers(self) -> set[CenterName]:
        """
        Get all centers defined by combined activations.

        Centers may become defined in the composite that aren't defined
        in any individual chart, when gates from different charts complete
        a channel.

        Returns:
            Set of defined center names in the composite
        """
        defined: set[CenterName] = set()
        for channel in self.active_channels:
            defined.add(channel.center_a)
            defined.add(channel.center_b)
        return defined

    @computed_field  # type: ignore
    @property
    def type(self) -> HDType:
        """
        Calculate composite Type from combined definition.

        Note: Composite type may differ from individual types.
        Example: Two Coordinators might form a Specialist composite
        if their combined gates create motor-to-throat connection.

        Returns:
            HDType for the composite chart
        """
        calculator = TypeAuthorityCalculator(self)  # type: ignore
        return calculator.calculate_type()

    @computed_field  # type: ignore
    @property
    def authority(self) -> Authority:
        """
        Calculate composite Authority from combined centers.

        Follows same hierarchical precedence as individual charts.

        Returns:
            Authority enum for the composite
        """
        calculator = TypeAuthorityCalculator(self)  # type: ignore
        return calculator.calculate_authority()

    def __add__(self, other: "RawBodyGraph | CompositeBodyGraph | Transit") -> "CompositeBodyGraph":
        """
        Add another chart to this composite.

        Supports chaining:
            penta = chart1 + chart2 + chart3 + chart4 + chart5

        Args:
            other: Another bodygraph, composite, or transit

        Returns:
            New composite with all charts combined
        """
        from .transit import Transit

        if isinstance(other, CompositeBodyGraph):
            return CompositeBodyGraph(charts=self.charts + other.charts)
        elif isinstance(other, Transit):
            return CompositeBodyGraph(charts=self.charts + [other._as_bodygraph()])
        else:
            return CompositeBodyGraph(charts=self.charts + [other])

    def emergent_channels(self) -> list[ChannelDefinition]:
        """
        Find channels that exist in composite but not in any individual chart.

        These are the "magic" of interaction/penta - new connections that
        emerge when people come together.

        Returns:
            List of emergent channels
        """
        composite_channels = set(
            (ch.gate_a, ch.gate_b) for ch in self.active_channels
        )

        individual_channels: set[tuple[int, int]] = set()
        for chart in self.charts:
            for ch in chart.active_channels:
                individual_channels.add((ch.gate_a, ch.gate_b))

        emergent_pairs = composite_channels - individual_channels
        channel_registry = ChannelRegistry.load()

        emergent = []
        for ch in self.active_channels:
            if (ch.gate_a, ch.gate_b) in emergent_pairs:
                emergent.append(ch)

        return emergent
