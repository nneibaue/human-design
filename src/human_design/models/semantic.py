"""
Semantic interpretation layer for Human Design.

This module provides the type-safe schema and loader for hot-swappable
semantic interpretation systems (64keys, Ra Traditional, Jolly Alchemy, etc.).

Core principle: Raw calculations produce coordinates (gate 42, line 3).
Semantic systems interpret coordinates with meaning ("Maturation", "Increase", etc.).

Usage:
    from human_design.semantic import SemanticLoader
    
    # Load a semantic system
    semantics = SemanticLoader.load("64keys")  # or "ra_traditional", "jolly_alchemy"
    
    # Get gate meaning
    gate_meaning = semantics.gates[42]
    print(gate_meaning.name)  # "Maturation" (64keys) or "Increase" (Ra)
    
    # Get type description
    type_desc = semantics.types["sacral_motor_throat"]
    print(type_desc.display_name)  # "Specialist" (64keys) or "Manifesting Generator" (Ra)
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Protocol, runtime_checkable

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .core import CenterName, GateLineNumber, GateNumber


# =============================================================================
# SEMANTIC SCHEMA MODELS
# =============================================================================


class LineSemantics(BaseModel):
    """Semantic interpretation of a single line (1-6) within a gate."""

    line_number: GateLineNumber
    title: str = Field(..., description="Line name/archetype")
    text: str = Field(..., description="Line description/meaning")
    keywords: list[str] = Field(default_factory=list, description="Optional keywords")

    # Allow system-specific custom fields
    extra: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for specific semantic systems"
    )


class GateSemantics(BaseModel):
    """Semantic interpretation of a gate."""

    gate_number: GateNumber
    name: str = Field(..., description="Gate name (e.g., 'Maturation', 'Increase')")
    quarter: str | None = Field(None, description="Quarter classification (64keys-specific)")
    summary: str = Field(..., description="One-line essence of the gate")
    description: str = Field(..., description="Full gate description")
    strive: str | None = Field(None, description="Guidance for expressing this gate (64keys-specific)")
    keywords: list[str] = Field(default_factory=list, description="Optional keywords")

    lines: list[LineSemantics] = Field(..., description="The six lines (1-6)")

    # Allow system-specific custom fields
    extra: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for specific semantic systems"
    )

    @field_validator("lines")
    @classmethod
    def validate_lines(cls, lines: list[LineSemantics]) -> list[LineSemantics]:
        """Ensure exactly 6 lines, numbered 1-6."""
        if len(lines) != 6:
            raise ValueError(f"Gate must have exactly 6 lines, got {len(lines)}")
        line_numbers = {line.line_number for line in lines}
        if line_numbers != {1, 2, 3, 4, 5, 6}:
            raise ValueError(f"Lines must be numbered 1-6, got {line_numbers}")
        return lines

    def get_line(self, line_number: GateLineNumber) -> LineSemantics | None:
        """Get a specific line by number."""
        for line in self.lines:
            if line.line_number == line_number:
                return line
        return None


class TypeSemantics(BaseModel):
    """Semantic interpretation of a Human Design type."""

    type_code: str = Field(
        ...,
        description="Internal type code (e.g., 'sacral_motor_throat', 'no_definition')",
    )
    display_name: str = Field(
        ..., description="Display name in this system (e.g., 'Specialist', 'Manifesting Generator')"
    )
    traditional_name: str | None = Field(
        None, description="Ra Uru Hu's traditional name for cross-reference"
    )
    strategy: str = Field(..., description="Decision-making strategy")
    signature: str = Field(..., description="Feeling when aligned")
    not_self_theme: str = Field(..., description="Feeling when not aligned")
    description: str = Field(..., description="Full type description")

    # Allow system-specific custom fields
    extra: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for specific semantic systems"
    )


class AuthoritySemantics(BaseModel):
    """Semantic interpretation of an authority (decision-making strategy)."""

    authority_code: str = Field(
        ..., description="Internal authority code (e.g., 'emotional', 'sacral')"
    )
    display_name: str = Field(
        ...,
        description="Display name in this system (e.g., 'Emotional', 'Wave Wisdom')",
    )
    traditional_name: str | None = Field(
        None, description="Ra Uru Hu's traditional name for cross-reference"
    )
    center_dependencies: list[CenterName] = Field(
        ..., description="Which centers must be defined for this authority"
    )
    decision_strategy: str = Field(..., description="How to use this authority")
    time_frame: str = Field(..., description="How long decisions take")
    description: str = Field(..., description="Full authority description")
    hierarchy_rank: int = Field(..., description="Priority in authority hierarchy (1=highest)")

    # Allow system-specific custom fields
    extra: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for specific semantic systems"
    )


class CenterSemantics(BaseModel):
    """Semantic interpretation of a center (both defined and undefined states)."""

    center_name: CenterName = Field(..., description="Internal center name (e.g., 'LIFEFORCE')")
    display_name: str = Field(
        ..., description="Display name in this system (e.g., 'Life Force', 'Source Well')"
    )
    traditional_name: str | None = Field(
        None, description="Ra Uru Hu's traditional name for cross-reference"
    )
    function: str = Field(..., description="What this center does")

    # Defined state
    defined_description: str = Field(..., description="Description when center is defined (colored in)")
    defined_shadow: str | None = Field(None, description="Shadow side when defined")

    # Undefined state
    undefined_description: str = Field(
        ..., description="Description when center is undefined (white/open)"
    )
    undefined_shadow: str | None = Field(None, description="Shadow side when undefined")
    undefined_wisdom: str | None = Field(None, description="Wisdom of undefined state")

    questions: list[str] = Field(
        default_factory=list, description="Contemplation questions for this center"
    )

    # Allow system-specific custom fields
    extra: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for specific semantic systems"
    )


class ProfileSemantics(BaseModel):
    """Semantic interpretation of a profile (e.g., 1/3, 4/6)."""

    profile_notation: str = Field(..., description="Profile notation (e.g., '1/3', '4/6')")
    display_name: str = Field(
        ..., description="Display name in this system (e.g., 'Investigator/Martyr')"
    )
    traditional_name: str | None = Field(
        None, description="Ra Uru Hu's traditional name for cross-reference"
    )
    conscious_line: GateLineNumber = Field(..., description="Conscious (personality) line number")
    unconscious_line: GateLineNumber = Field(..., description="Unconscious (design) line number")
    description: str = Field(..., description="Full profile description")

    life_theme: str | None = Field(None, description="Life theme for this profile")
    keywords: list[str] = Field(default_factory=list, description="Optional keywords")

    # Allow system-specific custom fields
    extra: dict[str, Any] = Field(
        default_factory=dict, description="Custom fields for specific semantic systems"
    )

    @field_validator("profile_notation")
    @classmethod
    def validate_notation(cls, notation: str) -> str:
        """Ensure profile notation is in correct format (e.g., '1/3')."""
        parts = notation.split("/")
        if len(parts) != 2:
            raise ValueError(f"Profile notation must be 'X/Y' format, got '{notation}'")
        try:
            conscious = int(parts[0])
            unconscious = int(parts[1])
            if not (1 <= conscious <= 6 and 1 <= unconscious <= 6):
                raise ValueError("Lines must be 1-6")
        except ValueError as e:
            raise ValueError(f"Invalid profile notation '{notation}': {e}") from e
        return notation


class SemanticInterpretation(BaseModel):
    """
    Complete semantic interpretation system.

    Provides all terminology and descriptions for a specific interpretation
    system (64keys, Ra Traditional, Jolly Alchemy, etc.).
    """

    system_id: str = Field(..., description="Unique system identifier (e.g., '64keys')")
    version: str = Field(..., description="Semantic versioning (e.g., '1.0.0')")
    author: str | None = Field(None, description="System author/creator")
    license: str | None = Field(None, description="License identifier (e.g., 'CC-BY-4.0')")
    description: str | None = Field(None, description="System description")

    gates: dict[GateNumber, GateSemantics] = Field(..., description="Gate interpretations (1-64)")
    types: dict[str, TypeSemantics] = Field(..., description="Type interpretations")
    authorities: dict[str, AuthoritySemantics] = Field(..., description="Authority interpretations")
    centers: dict[CenterName, CenterSemantics] = Field(..., description="Center interpretations")
    profiles: dict[str, ProfileSemantics] = Field(..., description="Profile interpretations (12 profiles)")

    model_config = ConfigDict(extra="allow")

    @field_validator("gates")
    @classmethod
    def validate_gates(cls, gates: dict[GateNumber, GateSemantics]) -> dict[GateNumber, GateSemantics]:
        """Ensure all 64 gates are present."""
        if len(gates) != 64:
            raise ValueError(f"Must have exactly 64 gates, got {len(gates)}")
        missing = set(range(1, 65)) - set(gates.keys())
        if missing:
            raise ValueError(f"Missing gates: {sorted(missing)}")
        return gates

    @field_validator("types")
    @classmethod
    def validate_types(cls, types: dict[str, TypeSemantics]) -> dict[str, TypeSemantics]:
        """Ensure all 5 core types are present."""
        required_codes = {
            "no_definition",
            "sacral_defined_no_motor_throat",
            "sacral_motor_throat",
            "motor_throat_no_sacral",
            "other_definition",
        }
        missing = required_codes - set(types.keys())
        if missing:
            raise ValueError(f"Missing required type codes: {missing}")
        return types

    @field_validator("authorities")
    @classmethod
    def validate_authorities(cls, authorities: dict[str, AuthoritySemantics]) -> dict[str, AuthoritySemantics]:
        """Ensure all 7 authorities are present."""
        required_codes = {"emotional", "sacral", "splenic", "ego", "self", "mental", "lunar"}
        missing = required_codes - set(authorities.keys())
        if missing:
            raise ValueError(f"Missing required authority codes: {missing}")
        return authorities

    @field_validator("centers")
    @classmethod
    def validate_centers(cls, centers: dict[CenterName, CenterSemantics]) -> dict[CenterName, CenterSemantics]:
        """Ensure all 9 centers are present."""
        required_centers: set[CenterName] = {
            "INSPIRATION",
            "MIND",
            "EXPRESSION",
            "IDENTITY",
            "WILLPOWER",
            "EMOTION",
            "DRIVE",
            "LIFEFORCE",
            "INTUITION",
        }
        missing = required_centers - set(centers.keys())
        if missing:
            raise ValueError(f"Missing required centers: {missing}")
        return centers

    @field_validator("profiles")
    @classmethod
    def validate_profiles(cls, profiles: dict[str, ProfileSemantics]) -> dict[str, ProfileSemantics]:
        """Ensure all 12 profiles are present."""
        required_profiles = {
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
        }
        missing = required_profiles - set(profiles.keys())
        if missing:
            raise ValueError(f"Missing required profiles: {missing}")
        return profiles


# =============================================================================
# SEMANTIC PROVIDER PROTOCOL
# =============================================================================


@runtime_checkable
class SemanticProvider(Protocol):
    """
    Protocol for semantic interpretation systems.

    All semantic systems must provide these methods for converting raw
    coordinates to meaningful descriptions.
    """

    def get_gate_meaning(self, gate: GateNumber, line: GateLineNumber) -> LineSemantics:
        """Get the semantic meaning of a gate.line activation."""
        ...

    def get_type_description(self, type_code: str) -> TypeSemantics:
        """Get the semantic description of a type."""
        ...

    def get_authority_description(self, authority_code: str) -> AuthoritySemantics:
        """Get the semantic description of an authority."""
        ...

    def get_center_meaning(self, center: CenterName, defined: bool) -> tuple[str, str]:
        """Get the semantic meaning of a center (returns display_name, description)."""
        ...


# =============================================================================
# SEMANTIC LOADER (FACTORY)
# =============================================================================


class SemanticLoader:
    """
    Factory for loading semantic interpretation systems from YAML config files.

    Semantic systems are stored in: ontology/semantics/<system_id>/
    Each system directory contains:
    - manifest.yaml (system metadata)
    - types.yaml (type interpretations)
    - authorities.yaml (authority interpretations)
    - centers.yaml (center interpretations)
    - profiles.yaml (profile interpretations)
    - gates/ (directory with gate_01.yaml through gate_64.yaml)

    Usage:
        semantics = SemanticLoader.load("64keys")
        gate = semantics.gates[42]
        print(gate.name)  # "Maturation"
    """

    ONTOLOGY_ROOT = Path(__file__).parent.parent / "ontology" / "semantics"

    @classmethod
    @lru_cache(maxsize=10)
    def load(cls, system_id: str) -> SemanticInterpretation:
        """
        Load a semantic interpretation system from YAML files.

        Args:
            system_id: System identifier (e.g., "64keys", "ra_traditional", "jolly_alchemy")

        Returns:
            Validated SemanticInterpretation model

        Raises:
            FileNotFoundError: If system directory doesn't exist
            ValidationError: If YAML files are malformed or incomplete
        """
        system_dir = cls.ONTOLOGY_ROOT / system_id
        if not system_dir.exists():
            available = [d.name for d in cls.ONTOLOGY_ROOT.iterdir() if d.is_dir()]
            raise FileNotFoundError(
                f"Semantic system not found: {system_id}\n"
                f"Available systems: {available}\n"
                f"Directory: {system_dir}"
            )

        # Load manifest
        manifest_path = system_dir / "manifest.yaml"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Missing manifest.yaml in {system_dir}")
        manifest = yaml.safe_load(manifest_path.read_text())

        # Load gates (from individual files or aggregated)
        gates = cls._load_gates(system_dir)

        # Load other components
        types = cls._load_yaml_dict(system_dir / "types.yaml", TypeSemantics, "type_code")
        authorities = cls._load_yaml_dict(
            system_dir / "authorities.yaml", AuthoritySemantics, "authority_code"
        )
        centers = cls._load_yaml_dict(system_dir / "centers.yaml", CenterSemantics, "center_name")
        profiles = cls._load_yaml_dict(
            system_dir / "profiles.yaml", ProfileSemantics, "profile_notation"
        )

        return SemanticInterpretation(
            system_id=system_id,
            version=manifest["version"],
            author=manifest.get("author"),
            license=manifest.get("license"),
            description=manifest.get("description"),
            gates=gates,
            types=types,
            authorities=authorities,
            centers=centers,
            profiles=profiles,
        )

    @classmethod
    def _load_gates(cls, system_dir: Path) -> dict[GateNumber, GateSemantics]:
        """Load gate semantics from individual files or aggregated YAML."""
        gates_dir = system_dir / "gates"
        if gates_dir.exists() and gates_dir.is_dir():
            # Load from individual gate files (gate_01.yaml, gate_02.yaml, ...)
            gates: dict[GateNumber, GateSemantics] = {}
            for gate_file in sorted(gates_dir.glob("gate_*.yaml")):
                gate_num_str = gate_file.stem.split("_")[1]
                gate_num = int(gate_num_str)
                gate_data = yaml.safe_load(gate_file.read_text())
                gates[gate_num] = GateSemantics(**gate_data)  # type: ignore
            return gates
        else:
            # Load from aggregated gates.yaml
            gates_path = system_dir / "gates.yaml"
            if not gates_path.exists():
                raise FileNotFoundError(
                    f"Missing gates/ directory or gates.yaml in {system_dir}"
                )
            gates_list = yaml.safe_load(gates_path.read_text())
            return {g["gate_number"]: GateSemantics(**g) for g in gates_list}

    @classmethod
    def _load_yaml_dict(
        cls, yaml_path: Path, model_class: type[BaseModel], key_field: str
    ) -> dict[Any, Any]:
        """Load a list of models from YAML and convert to dict keyed by field."""
        if not yaml_path.exists():
            raise FileNotFoundError(f"Missing {yaml_path}")
        items = yaml.safe_load(yaml_path.read_text())
        if not isinstance(items, list):
            raise ValueError(f"{yaml_path} must contain a list, got {type(items)}")
        return {item[key_field]: model_class(**item) for item in items}

    @classmethod
    def list_available_systems(cls) -> list[str]:
        """List all available semantic systems."""
        if not cls.ONTOLOGY_ROOT.exists():
            return []
        return [d.name for d in cls.ONTOLOGY_ROOT.iterdir() if d.is_dir() and not d.name.startswith("_")]


# =============================================================================
# ENVIRONMENT-BASED DEFAULT
# =============================================================================


def get_default_semantic_system() -> str:
    """
    Get semantic system from environment variable or default to 64keys.

    Environment variable: HD_SEMANTIC_SYSTEM

    Returns:
        System identifier (e.g., "64keys", "ra_traditional")
    """
    return os.getenv("HD_SEMANTIC_SYSTEM", "64keys")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def load_semantic_system(system_id: str | None = None) -> SemanticInterpretation:
    """
    Load a semantic system (convenience wrapper).

    Args:
        system_id: System identifier or None to use environment default

    Returns:
        SemanticInterpretation instance
    """
    if system_id is None:
        system_id = get_default_semantic_system()
    return SemanticLoader.load(system_id)
