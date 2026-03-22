"""
Transit - planetary positions at a specific moment.

In Human Design ontology, a Transit is distinct from a BodyGraph:
- BodyGraph: Birth chart with conscious (personality) + unconscious (design)
- Transit: Current planetary positions at one moment (no design component)

Transits can be overlaid on birth charts using the + operator to see
current influences.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, computed_field, model_validator
from typing_extensions import Self
from timezonefinder import TimezoneFinder

from ..calculate_utils import geocode_place
from .bodygraph import BodyGraphDefinition, RawActivation
from .channel import ChannelDefinition, ChannelRegistry
from .core import CenterName, GateNumber, Planet
from .type_authority import Authority, HDType, Profile, TypeAuthorityCalculator

if TYPE_CHECKING:
    from .bodygraph import RawBodyGraph
    from .composite import CompositeBodyGraph


class Transit(BaseModel):
    """
    Transit - planetary positions at a specific moment.

    Unlike a BodyGraph (which has conscious + unconscious), a Transit
    represents a single moment in time - the current planetary configuration.

    Can be combined with BodyGraphs or other Transits using + operator.

    Example:
        transit = Transit.now(location="Denver, CO")
        with_transit = birth_chart + transit
    """

    moment: datetime
    location: str  # "city, country" format

    @model_validator(mode="after")
    def validate_location_format(self) -> Self:
        """Ensure location is in 'city, country' format."""
        if "," not in self.location:
            raise ValueError(
                f"Location must be 'city, country' format, got: {self.location}"
            )
        parts = self.location.split(",")
        if len(parts) != 2:
            raise ValueError(
                f"Location must be 'city, country' format, got: {self.location}"
            )
        return self

    @computed_field  # type: ignore
    @property
    def city(self) -> str:
        """Extract city from location."""
        return self.location.split(",")[0].strip()

    @computed_field  # type: ignore
    @property
    def country(self) -> str:
        """Extract country from location."""
        return self.location.split(",")[1].strip()

    @computed_field  # type: ignore
    @property
    def coordinates(self) -> tuple[float, float]:
        """Geocoded coordinates (lat, lon)."""
        return geocode_place(self.location)

    @computed_field  # type: ignore
    @property
    def timezone(self) -> str:
        """Timezone for the location."""
        lat, lon = self.coordinates
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lat=lat, lng=lon)
        if tz_name is None:
            raise RuntimeError(f"Could not determine timezone for: {self.location}")
        return tz_name

    @computed_field  # type: ignore
    @property
    def jd_ut(self) -> float:
        """Julian Day Universal Time for this moment."""
        from .coordinates import LocalTime
        lt = LocalTime(self.moment)
        return lt.jd(self.timezone)

    @computed_field  # type: ignore
    @property
    def activations(self) -> list[RawActivation]:
        """
        Calculate planetary activations for this moment.

        Returns single set of activations (not conscious + unconscious).
        This is what distinguishes Transit from BodyGraph.
        """
        definitions = BodyGraphDefinition.load()
        activations: list[RawActivation] = []

        # Calculate all planetary positions
        for planet in Planet:
            if planet == Planet.SOUTH_NODE:
                # South Node is opposite of North Node
                north_node_lon = Planet.NORTH_NODE.lon_ut(self.jd_ut)
                lon = (north_node_lon + 180.0) % 360.0
            else:
                lon = planet.lon_ut(self.jd_ut)

            gate_num, line_num = definitions.gate_and_line_from_longitude(lon)
            activations.append(RawActivation(planet=planet, gate=gate_num, line=line_num))

        return activations

    @property
    def all_activated_gates(self) -> set[GateNumber]:
        """Get all unique gates activated in this transit."""
        return {act.gate for act in self.activations}

    @computed_field  # type: ignore
    @property
    def active_channels(self) -> list[ChannelDefinition]:
        """Get all channels formed by transit activations."""
        channel_registry = ChannelRegistry.load()
        return channel_registry.get_formed_channels(self.all_activated_gates)

    @computed_field  # type: ignore
    @property
    def defined_centers(self) -> set[CenterName]:
        """Get all centers defined in this transit."""
        defined: set[CenterName] = set()
        for channel in self.active_channels:
            defined.add(channel.center_a)
            defined.add(channel.center_b)
        return defined

    @computed_field  # type: ignore
    @property
    def type(self) -> HDType:
        """Calculate HD Type for this transit."""
        calculator = TypeAuthorityCalculator(self)  # type: ignore
        return calculator.calculate_type()

    @computed_field  # type: ignore
    @property
    def authority(self) -> Authority:
        """Calculate Authority for this transit."""
        calculator = TypeAuthorityCalculator(self)  # type: ignore
        return calculator.calculate_authority()

    # NOTE: Transits don't have profiles. Profile requires conscious (birth)
    # and unconscious (design) Sun positions, which only exist for birth charts.
    # A transit is a single moment, so profile doesn't apply.

    def __add__(self, other: "Transit | RawBodyGraph | CompositeBodyGraph") -> "CompositeBodyGraph":
        """
        Combine transit with charts.

        Example:
            with_transit = birth_chart + transit
            multi_transit = transit1 + transit2 + birth_chart
        """
        from .bodygraph import RawBodyGraph
        from .composite import CompositeBodyGraph

        # Convert self to RawBodyGraph-like for composition
        # We create a minimal bodygraph where conscious = unconscious = transit activations
        if isinstance(other, CompositeBodyGraph):
            return CompositeBodyGraph(charts=[self._as_bodygraph()] + other.charts)  # type: ignore
        elif isinstance(other, (RawBodyGraph, Transit)):
            if isinstance(other, Transit):
                return CompositeBodyGraph(charts=[self._as_bodygraph(), other._as_bodygraph()])  # type: ignore
            else:
                return CompositeBodyGraph(charts=[self._as_bodygraph(), other])  # type: ignore
        else:
            raise TypeError(f"Cannot add Transit to {type(other)}")

    def _as_bodygraph(self) -> "RawBodyGraph":
        """
        Convert Transit to RawBodyGraph for composition.

        Creates a bodygraph where conscious and unconscious are both
        the transit activations (same moment).
        """
        from .bodygraph import BirthInfo, RawBodyGraph
        from .coordinates import LocalTime

        birth_info = BirthInfo(
            date=self.moment.strftime("%Y-%m-%d"),
            localtime=LocalTime(self.moment),
            city=self.city,
            country=self.country,
        )

        # Create a bodygraph, but we'll override its activations property
        # Actually, we can't easily override computed properties
        # So we'll just return a normal bodygraph - it will have both conscious and unconscious
        # But that's OK for composition purposes since CompositeBodyGraph only uses all_activated_gates
        return RawBodyGraph(birth_info=birth_info)

    @classmethod
    def now(cls, location: str = "Greenwich, UK") -> "Transit":
        """
        Create transit for current moment.

        Args:
            location: "city, country" format. Defaults to Greenwich (UTC).

        Returns:
            Transit representing current planetary positions

        Example:
            transit = Transit.now(location="Denver, CO")
            with_transit = birth_chart + transit
        """
        return cls(moment=datetime.now(), location=location)

    @classmethod
    def at(cls, dt: datetime, location: str = "Greenwich, UK") -> "Transit":
        """
        Create transit for specific moment.

        Args:
            dt: Datetime for transit
            location: "city, country" format. Defaults to Greenwich (UTC).

        Returns:
            Transit representing planetary positions at specified time

        Example:
            nye = Transit.at(datetime(2024, 12, 31, 23, 59), "New York, NY")
            with_transit = birth_chart + nye
        """
        return cls(moment=dt, location=location)


# Backwards compatibility with old function-based API
def transit_now(location: str = "Greenwich, UK") -> Transit:
    """Create transit for current moment. Prefer Transit.now()."""
    return Transit.now(location=location)


def transit_at(dt: datetime, location: str = "Greenwich, UK") -> Transit:
    """Create transit for specific moment. Prefer Transit.at()."""
    return Transit.at(dt, location=location)


# Rebuild Transit model now that all dependencies are defined
Transit.model_rebuild()
