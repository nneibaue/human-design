"""
Channel formation logic for Human Design bodygraphs.

This module provides:
- ChannelDefinition: Model for a channel (connection between two gates)
- CenterRegistry: Singleton mapping gates to centers
- ChannelRegistry: Singleton registry of all 36 channels

Channel Formation Rules:
- A channel is "formed" when BOTH its gates are activated
- Channels connect two centers
- Centers are "defined" when they have at least one active channel
"""

import importlib.resources
from functools import cached_property
from pathlib import Path
from typing import ClassVar

import yaml
from pydantic import BaseModel, Field

from .core import CenterName, GateNumber


# ==============================================================================
# MODELS
# ==============================================================================


class ChannelDefinition(BaseModel):
    """
    Definition of a channel connecting two gates.

    A channel represents a connection between two gates in the bodygraph.
    When both gates are activated, the channel is "formed" and provides
    a consistent energy flow between the two connected centers.
    """

    channel_id: int = Field(..., description="Unique channel ID (1-36)")
    name: str = Field(..., description="Channel name")
    gate_a: GateNumber = Field(..., description="First gate in the channel")
    gate_b: GateNumber = Field(..., description="Second gate in the channel")
    center_a: CenterName = Field(..., description="Center containing gate_a")
    center_b: CenterName = Field(..., description="Center containing gate_b")

    def is_formed_by(self, activated_gates: set[GateNumber]) -> bool:
        """
        Check if this channel is formed by the given gate activations.

        Args:
            activated_gates: Set of activated gate numbers

        Returns:
            True if both gates are in the activation set
        """
        return self.gate_a in activated_gates and self.gate_b in activated_gates

    @property
    def gates(self) -> tuple[GateNumber, GateNumber]:
        """Return both gates as a tuple."""
        return (self.gate_a, self.gate_b)

    @property
    def centers(self) -> tuple[CenterName, CenterName]:
        """Return both centers as a tuple."""
        return (self.center_a, self.center_b)


# ==============================================================================
# REGISTRIES (SINGLETONS)
# ==============================================================================


class CenterRegistry:
    """
    Singleton registry mapping gates to centers.

    Parses centers.yaml to build a gate → center lookup table.
    """

    _instance: ClassVar["CenterRegistry | None"] = None
    _gate_to_center: dict[GateNumber, CenterName]

    def __init__(self):
        """Private constructor. Use CenterRegistry.load() instead."""
        self._gate_to_center = {}

    @classmethod
    def load(cls) -> "CenterRegistry":
        """
        Load and cache the center registry from centers.yaml.

        Returns:
            Singleton CenterRegistry instance

        Raises:
            FileNotFoundError: If centers.yaml cannot be found
            ValueError: If YAML is malformed
        """
        if cls._instance is None:
            cls._instance = cls._load_from_yaml()
        return cls._instance

    @classmethod
    def _load_from_yaml(cls) -> "CenterRegistry":
        """Parse centers.yaml and build gate → center map."""
        try:
            centers_file = Path(str(importlib.resources.files("human_design"))) / "centers.yaml"
            with open(centers_file, "r", encoding="utf-8") as f:
                centers_data = yaml.safe_load(f)

            gate_to_center: dict[GateNumber, CenterName] = {}
            for center in centers_data:
                center_name = center["name"]
                for gate in center["gates"]:
                    gate_to_center[gate] = center_name

            registry = cls()
            registry._gate_to_center = gate_to_center
            return registry

        except Exception as e:
            raise ValueError(f"Failed to load centers.yaml: {e}") from e

    def get_center(self, gate: GateNumber) -> CenterName:
        """
        Get the center for a given gate.

        Args:
            gate: Gate number (1-64)

        Returns:
            Center name

        Raises:
            KeyError: If gate is not assigned to any center
        """
        return self._gate_to_center[gate]


class ChannelRegistry:
    """
    Singleton registry of all 36 channel definitions.

    Parses channels.yaml and creates ChannelDefinition objects with
    center connections derived from CenterRegistry.
    """

    _instance: ClassVar["ChannelRegistry | None"] = None
    _channels: list[ChannelDefinition]

    def __init__(self):
        """Private constructor. Use ChannelRegistry.load() instead."""
        self._channels = []

    @classmethod
    def load(cls) -> "ChannelRegistry":
        """
        Load and cache all channel definitions from channels.yaml.

        Returns:
            Singleton ChannelRegistry instance

        Raises:
            FileNotFoundError: If channels.yaml cannot be found
            ValueError: If YAML is malformed
        """
        if cls._instance is None:
            cls._instance = cls._load_from_yaml()
        return cls._instance

    @classmethod
    def _load_from_yaml(cls) -> "ChannelRegistry":
        """Parse channels.yaml and create ChannelDefinition objects."""
        try:
            channels_file = Path(str(importlib.resources.files("human_design"))) / "channels.yaml"
            with open(channels_file, "r", encoding="utf-8") as f:
                channels_data = yaml.safe_load(f)

            center_registry = CenterRegistry.load()
            channels: list[ChannelDefinition] = []

            for idx, channel_data in enumerate(channels_data, start=1):
                gate_a, gate_b = channel_data["gates"]
                channels.append(
                    ChannelDefinition(
                        channel_id=idx,
                        name=channel_data["name"],
                        gate_a=gate_a,
                        gate_b=gate_b,
                        center_a=center_registry.get_center(gate_a),
                        center_b=center_registry.get_center(gate_b),
                    )
                )

            registry = cls()
            registry._channels = channels
            return registry

        except Exception as e:
            raise ValueError(f"Failed to load channels.yaml: {e}") from e

    @property
    def all_channels(self) -> list[ChannelDefinition]:
        """Get all 36 channel definitions."""
        return self._channels

    def get_formed_channels(self, activated_gates: set[GateNumber]) -> list[ChannelDefinition]:
        """
        Get all channels formed by the given gate activations.

        A channel is formed when BOTH its gates are activated.

        Args:
            activated_gates: Set of activated gate numbers

        Returns:
            List of formed channels (may be empty)
        """
        return [ch for ch in self._channels if ch.is_formed_by(activated_gates)]
