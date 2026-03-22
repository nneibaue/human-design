"""
Type and Authority calculation for Human Design bodygraphs.

This module determines:
- HDType (Initiator/Builder/Specialist/Coordinator/Observer)
- Authority (7-tier hierarchy from Emotional to Lunar)
- Profile (12 profiles from Sun conscious/unconscious lines)

These are calculated from channel formation patterns and center definitions.
"""

from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, computed_field

from .core import CenterName, GateLineNumber

if TYPE_CHECKING:
    from .bodygraph import RawBodyGraph
    from .channel import ChannelDefinition


class HDType(str, Enum):
    """
    Human Design Type using 64keys terminology.

    Traditional HD terms in parentheses.
    Type is determined by which centers are defined and how they connect.
    """

    INITIATOR = "Initiator"  # Manifestor
    BUILDER = "Builder"  # Pure Generator
    SPECIALIST = "Specialist"  # Manifesting Generator
    COORDINATOR = "Coordinator"  # Projector
    OBSERVER = "Observer"  # Reflector


class Authority(str, Enum):
    """
    Human Design Authority - decision-making strategy.

    Authority follows a hierarchical precedence (first defined wins).
    The order listed here is the evaluation order.
    """

    EMOTIONAL = "Emotional"  # Solar Plexus defined
    SACRAL = "Sacral"  # Sacral (LIFEFORCE) defined, no Emotion
    SPLENIC = "Splenic"  # Spleen (INTUITION) defined, no Emotion/Sacral
    EGO = "Ego"  # Heart (WILLPOWER) defined, no Emotion/Sacral/Splenic
    SELF = "Self"  # G (IDENTITY) defined, no higher authorities
    MENTAL = "Mental"  # Ajna (MIND) defined, no other authority centers
    LUNAR = "Lunar"  # No centers defined (Reflectors only)


class Profile(BaseModel):
    """
    Human Design Profile - role and life theme.

    Profile is determined by the line numbers of the conscious (personality)
    and unconscious (design) Sun activations.

    There are 12 possible profiles: 1/3, 1/4, 2/4, 2/5, 3/5, 3/6, 4/6, 4/1, 5/1, 5/2, 6/2, 6/3
    """

    conscious_line: GateLineNumber
    unconscious_line: GateLineNumber

    @computed_field  # type: ignore
    @property
    def profile_notation(self) -> str:
        """Profile in standard notation (e.g., '1/3', '4/6')."""
        return f"{self.conscious_line}/{self.unconscious_line}"

    @computed_field  # type: ignore
    @property
    def profile_name(self) -> str:
        """Traditional profile name."""
        names = {
            "1/3": "Investigator/Martyr",
            "1/4": "Investigator/Opportunist",
            "2/4": "Hermit/Opportunist",
            "2/5": "Hermit/Heretic",
            "3/5": "Martyr/Heretic",
            "3/6": "Martyr/Role Model",
            "4/6": "Opportunist/Role Model",
            "4/1": "Opportunist/Investigator",
            "5/1": "Heretic/Investigator",
            "5/2": "Heretic/Hermit",
            "6/2": "Role Model/Hermit",
            "6/3": "Role Model/Martyr",
        }
        return names.get(self.profile_notation, f"Unknown Profile ({self.profile_notation})")


class TypeAuthorityCalculator:
    """
    Calculator for determining Type, Authority, and Profile from a RawBodyGraph.

    This class encapsulates the complex logic for type/authority determination
    based on channel formation patterns.
    """

    def __init__(self, bodygraph: "RawBodyGraph"):
        """Initialize calculator with a bodygraph."""
        self.bodygraph = bodygraph
        self.defined_centers = bodygraph.defined_centers
        self.active_channels = bodygraph.active_channels

    def calculate_type(self) -> HDType:
        """
        Calculate Human Design Type from defined centers and channels.

        Type determination logic:
        1. Observer: No defined centers
        2. Initiator: Motor-to-Throat without Sacral
        3. Specialist: Sacral defined AND motor-to-throat
        4. Builder: Sacral defined, no motor-to-throat
        5. Coordinator: At least one defined center, but not above conditions
        """
        # Check if any centers are defined
        if not self.defined_centers:
            return HDType.OBSERVER

        # Check if LIFEFORCE (Sacral) is defined
        sacral_defined = "LIFEFORCE" in self.defined_centers

        # Check for motor-to-throat connection
        motor_to_throat = self._has_motor_to_throat_connection()

        if sacral_defined and motor_to_throat:
            return HDType.SPECIALIST
        elif sacral_defined:
            return HDType.BUILDER
        elif motor_to_throat:
            return HDType.INITIATOR
        else:
            return HDType.COORDINATOR

    def calculate_authority(self) -> Authority:
        """
        Calculate Authority based on hierarchical precedence of defined centers.

        Authority order (first defined wins):
        1. Emotional (EMOTION)
        2. Sacral (LIFEFORCE)
        3. Splenic (INTUITION)
        4. Ego (WILLPOWER)
        5. Self (IDENTITY)
        6. Mental (MIND)
        7. Lunar (no centers)
        """
        if "EMOTION" in self.defined_centers:
            return Authority.EMOTIONAL
        elif "LIFEFORCE" in self.defined_centers:
            return Authority.SACRAL
        elif "INTUITION" in self.defined_centers:
            return Authority.SPLENIC
        elif "WILLPOWER" in self.defined_centers:
            return Authority.EGO
        elif "IDENTITY" in self.defined_centers:
            return Authority.SELF
        elif "MIND" in self.defined_centers:
            return Authority.MENTAL
        else:
            return Authority.LUNAR

    def calculate_profile(self) -> Profile:
        """
        Calculate Profile from Sun conscious/unconscious line numbers.

        Profile is determined by:
        - Conscious line: From personality (conscious) Sun activation
        - Unconscious line: From design (unconscious) Sun activation
        """
        from .core import Planet

        # Find Sun in conscious activations
        conscious_sun = next(
            (act for act in self.bodygraph.conscious_activations if act.planet == Planet.SUN),
            None,
        )
        if not conscious_sun:
            raise RuntimeError("No conscious Sun activation found")

        # Find Sun in unconscious activations
        unconscious_sun = next(
            (act for act in self.bodygraph.unconscious_activations if act.planet == Planet.SUN),
            None,
        )
        if not unconscious_sun:
            raise RuntimeError("No unconscious Sun activation found")

        return Profile(
            conscious_line=conscious_sun.line,
            unconscious_line=unconscious_sun.line,
        )

    def _has_motor_to_throat_connection(self) -> bool:
        """
        Check if there's a motor-to-throat connection.

        Motors: WILLPOWER, EMOTION, DRIVE, LIFEFORCE
        Throat: EXPRESSION

        A motor-to-throat connection means at least one channel connects
        a motor center to the throat (EXPRESSION) center.
        """
        motor_centers: set[CenterName] = {"WILLPOWER", "EMOTION", "DRIVE", "LIFEFORCE"}
        throat_center: CenterName = "EXPRESSION"

        for channel in self.active_channels:
            centers = {channel.center_a, channel.center_b}
            # Check if channel connects a motor to throat
            if throat_center in centers and any(motor in centers for motor in motor_centers):
                return True

        return False
