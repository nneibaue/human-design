"""
Raw bodygraph models for Human Design calculations.

These models represent the "raw" calculated bodygraph data based on
astronomical calculations. They do not include any 64keys.com augmented
content like descriptions, summaries, or interpretations.

The raw models can be converted to 64keys summary models via the API.
"""

import importlib.resources
import math
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Annotated, Self, cast

import pytz  # type: ignore
import swisseph as swe  # type: ignore
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    model_validator,
)
from timezonefinder import TimezoneFinder

from ..calculate_utils import calc_lon_ut, geocode_place
from .coordinates import CoordinateRange, LocalTime
from .core import CenterName, GateLineNumber, GateNumber, Planet, PlanetField

BODYGRAPH_DEFINITION_FILE = Path(str(importlib.resources.files("human_design") / "bodygraph.yaml"))




class GateDefinition(BaseModel):
    """
    Raw gate definition from the bodygraph structure.

    Contains the gate number, complement connection(s), and zodiac coordinate range.
    Does NOT include 64keys content like descriptions or line details.
    """

    number: GateNumber
    complement: int | list[int]  # Some gates connect to multiple other gates
    coordinate_range: CoordinateRange


class CenterDefinition(BaseModel):
    """
    Raw center definition containing its gates.
    """

    name: CenterName
    gates: list[GateDefinition]


class BodyGraphDefinition(BaseModel):
    """
    Complete bodygraph structure definition.

    Loaded from bodygraph_definition.yaml, contains all centers and gates
    with their zodiac coordinate ranges for mapping longitudes to gates.
    """

    centers: list[CenterDefinition]

    @property
    def all_gates(self) -> Iterator[GateDefinition]:
        """Iterate over all gate definitions across all centers."""
        for center in self.centers:
            yield from center.gates

    def get_gate(self, gate_num: int) -> GateDefinition | None:
        """Find a gate definition by its number."""
        for gate in self.all_gates:
            if gate.number == gate_num:
                return gate
        return None

    def gate_and_line_from_longitude(self, lon: float) -> tuple[GateNumber, GateLineNumber]:
        """
        Map zodiac longitude to (gate, line) using bodygraph gate definitions.

        Args:
            lon: Zodiac longitude in degrees (0-360)

        Returns:
            Tuple of (gate_number, line_number)

        Raises:
            RuntimeError: If no gate range contains the longitude
        """
        # Normalize longitude to [0, 360)
        lon = lon % 360.0

        for gate in self.all_gates:
            s = gate.coordinate_range.start_deg
            e = gate.coordinate_range.end_deg

            if s <= e:
                # Normal range (doesn't wrap around 360)
                if s <= lon < e:
                    span = e - s
                    offset = lon - s
                    line = int(math.floor(offset / (span / 6.0))) + 1
                    return gate.number, cast(GateLineNumber, min(max(line, 1), 6))
            else:
                # Range wraps around 360 (e.g., 350-10 degrees)
                if lon >= s or lon < e:
                    span = (360.0 - s) + e
                    offset = (lon - s) if lon >= s else ((360.0 - s) + lon)
                    line = int(math.floor(offset / (span / 6.0))) + 1
                    return gate.number, cast(GateLineNumber, min(max(line, 1), 6))

        raise RuntimeError(f"No gate range found for longitude {lon}")

    @classmethod
    def load(cls) -> Self:
        """Load BodyGraphDefinition from the YAML file."""
        import yaml  # type: ignore

        raw = yaml.safe_load(Path(BODYGRAPH_DEFINITION_FILE).read_text())
        # YAML file is a list of centers at the top level
        return cls.model_validate({"centers": raw})


class RawActivation(BaseModel):
    """
    A raw planetary activation (planet + gate + line).

    This is the calculated result before any 64keys content is added.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "planet": "SUN",
                "gate": 4,
                "line": 3,
            }
        }
    )

    planet: PlanetField
    gate: GateNumber
    line: GateLineNumber

    @computed_field  # type: ignore
    @property
    def gate_line(self) -> str:
        """Gate.line representation (e.g., '4.3')."""
        return f"{self.gate}.{self.line}"


def _assert_hyphenated_european_date(date_str: str) -> str:
    """Assert date string is in YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Date must be in YYYY-MM-DD format: {date_str}") from e
    return date_str


class BirthInfo(BaseModel):
    """
    Birth information used for Human Design chart calculations.

    Contains date, time, and location which are used to calculate
    the Julian Day for both personality (birth) and design (88° earlier) moments.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "1990-01-01",
                "localtime": "1990-01-01T12:00:00",
                "city": "New York",
                "country": "USA",
            }
        }
    )

    # User inputs
    date: Annotated[
        str,
        Field(description="Birth date in YYYY-MM-DD format"),
        AfterValidator(_assert_hyphenated_european_date),
    ]
    localtime: LocalTime
    city: str
    country: str

    @model_validator(mode="after")
    def validate_date_matches_localtime(self) -> Self:
        """Ensure date field matches the date in localtime."""
        lt_date = self.localtime.root.strftime("%Y-%m-%d")
        if lt_date != self.date:
            raise ValueError(f"date ({self.date}) must match localtime date ({lt_date})")
        return self

    @computed_field  # type: ignore
    @property
    def place(self) -> str:
        """Full place string for geocoding."""
        return f"{self.city}, {self.country}"

    @computed_field  # type: ignore
    @property
    def coordinates(self) -> tuple[float, float]:
        """Geocoded coordinates (lat, lon)."""
        return geocode_place(self.place)

    @computed_field  # type: ignore
    @property
    def timezone(self) -> str:
        """Timezone name for the birth location."""
        lat, lon = self.coordinates
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lat=lat, lng=lon)
        if tz_name is None:
            raise RuntimeError(f"Could not determine timezone for coordinates: {lat}, {lon}")
        # Validate timezone
        try:
            pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError as e:
            raise RuntimeError(f"Unknown timezone found: {tz_name}") from e
        return tz_name

    @computed_field  # type: ignore
    @property
    def birth_jd_ut(self) -> float:
        """Julian Day Universal Time of birth."""
        return self.localtime.jd(self.timezone)

    @computed_field  # type: ignore
    @property
    def design_jd_ut(self) -> float:
        """
        Calculate the Julian Day UT for the Design (unconscious) moment.

        In Human Design, the Design calculation finds when the Sun was exactly
        88 degrees earlier in the zodiac (not 88 days - the actual time varies
        based on the Sun's apparent speed throughout the year).

        Uses Newton-Raphson root finding to converge on the exact moment.
        """
        # Get the Sun's ecliptic longitude at birth
        birth_sun_lon = Planet.SUN.lon_ut(self.birth_jd_ut)

        # Target longitude is 88° earlier (with wraparound)
        target = (birth_sun_lon - 88.0) % 360.0

        # Initial guess: approximately 88 days earlier
        current = self.birth_jd_ut - 88.0

        def _angdiff_signed(a: float, b: float) -> float:
            """Compute smallest signed angular difference (a - b) in degrees."""
            d = (a - b + 180.0) % 360.0 - 180.0
            return d

        # Newton-Raphson iteration
        for _ in range(20):
            lon, speed = calc_lon_ut(current, swe.SUN)
            err = _angdiff_signed(lon, target)

            if abs(err) < 1e-6:
                break

            current -= err / (speed if speed != 0 else 0.9856)

        return current


class RawBodyGraph(BaseModel):
    """
    Complete raw bodygraph calculated from birth information.

    Contains all planetary activations for both personality (conscious/birth)
    and design (unconscious/88° earlier) aspects of the chart.

    This is the "raw" calculation result. Use the API to convert this
    to a BodyGraphSummary64Keys with full descriptions and interpretations.
    """

    model_config = ConfigDict(
        json_schema_extra={"description": "Raw bodygraph with personality and design activations"}
    )

    birth_info: BirthInfo

    @computed_field  # type: ignore
    @property
    def conscious_activations(self) -> list[RawActivation]:
        """
        Calculate personality (conscious) planetary activations.

        These are the planetary positions at the moment of birth.
        """
        return self._activations_for_jd(self.birth_info.birth_jd_ut)

    @computed_field  # type: ignore
    @property
    def unconscious_activations(self) -> list[RawActivation]:
        """
        Calculate design (unconscious) planetary activations.

        These are the planetary positions when the Sun was 88° earlier.
        """
        return self._activations_for_jd(self.birth_info.design_jd_ut)

    def _activations_for_jd(self, jd_ut: float) -> list[RawActivation]:
        """
        Calculate all planetary activations for a given Julian Day UT.

        Args:
            jd_ut: Julian Day Universal Time

        Returns:
            List of RawActivation for all planets
        """
        definitions = BodyGraphDefinition.load()
        activations: list[RawActivation] = []

        # Sun
        sun_lon = Planet.SUN.lon_ut(jd_ut)
        gate_num, line_num = definitions.gate_and_line_from_longitude(sun_lon)
        activations.append(RawActivation(planet=Planet.SUN, gate=gate_num, line=line_num))

        # Earth = opposite of Sun (Sun + 180°)
        earth_lon = (sun_lon + 180.0) % 360.0
        gate_num, line_num = definitions.gate_and_line_from_longitude(earth_lon)
        activations.append(RawActivation(planet=Planet.EARTH, gate=gate_num, line=line_num))

        # All other planets (skip SUN, EARTH, and SOUTH_NODE as we handle those specially)
        for planet in Planet:
            if planet in (Planet.SUN, Planet.EARTH, Planet.SOUTH_NODE):
                continue
            lon = planet.lon_ut(jd_ut)
            gate_num, line_num = definitions.gate_and_line_from_longitude(lon)
            activations.append(RawActivation(planet=planet, gate=gate_num, line=line_num))

        # South Node = opposite of North Node
        north_node_lon = Planet.NORTH_NODE.lon_ut(jd_ut)
        south_node_lon = (north_node_lon + 180.0) % 360.0
        gate_num, line_num = definitions.gate_and_line_from_longitude(south_node_lon)
        activations.append(RawActivation(planet=Planet.SOUTH_NODE, gate=gate_num, line=line_num))

        return activations

    @property
    def all_activated_gates(self) -> set[GateNumber]:
        """Get all unique gates activated in the chart."""
        gates: set[GateNumber] = set()
        for activation in self.conscious_activations:
            gates.add(activation.gate)
        for activation in self.unconscious_activations:
            gates.add(activation.gate)
        return gates