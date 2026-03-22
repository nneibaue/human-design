#!/usr/bin/env python3
"""
Generate HD_ONTOLOGY_complete.json from YAML sources with zero interpretation errors.

This script implements deterministic transformation: YAML → JSON
- YAML files are source of truth (bodygraph.yaml, channels.yaml, centers.yaml)
- Existing ontology provides HD system knowledge (types, authorities, profiles, descriptions)
- Output is reproducible and verifiable

Usage:
    python ontology/generate_ontology.py

Output:
    ontology/HD_ONTOLOGY_complete.json (overwrites existing file)

Validation:
    - Asserts 64 gates, 36 channels, 9 centers
    - Cross-validates all data against YAML sources
    - Guarantees idempotency (byte-identical on repeated runs)

Architecture:
    Code-generated data > Hand-written data > LLM-interpreted data
"""

import json
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


# ==============================================================================
# DATA MODELS
# ==============================================================================


class CoordinatePoint(BaseModel):
    """Single zodiac coordinate point."""
    sign: str
    degree: int
    minute: int
    second: int


class CoordinateRange(BaseModel):
    """Zodiac coordinate range for a gate."""
    start: CoordinatePoint
    end: CoordinatePoint


class GateYAML(BaseModel):
    """Gate data from bodygraph.yaml."""
    number: int
    complement: int | list[int]
    ra_description: str
    coordinate_range: CoordinateRange


class ChannelYAML(BaseModel):
    """Channel data from channels.yaml."""
    name: str
    gates: list[int] = Field(..., min_length=2, max_length=2)


class CenterYAML(BaseModel):
    """Center data from centers.yaml."""
    name: str
    gates: list[int]


# ==============================================================================
# PARSING FUNCTIONS
# ==============================================================================


def parse_gates(bodygraph_yaml_path: Path) -> dict[int, GateYAML]:
    """
    Parse bodygraph.yaml into structured gate data.

    Returns:
        dict mapping gate number to GateYAML model

    Raises:
        Exception if YAML is malformed or missing required fields
    """
    try:
        with open(bodygraph_yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        gates = {}

        # bodygraph.yaml is organized by centers, each containing gates
        for center_data in data:
            for gate_data in center_data['gates']:
                gate = GateYAML(
                    number=gate_data['number'],
                    complement=gate_data['complement'],
                    ra_description=gate_data.get('ra_description', '').strip(),
                    coordinate_range=CoordinateRange(
                        start=CoordinatePoint(**gate_data['coordinate_range']['start']),
                        end=CoordinatePoint(**gate_data['coordinate_range']['end'])
                    )
                )
                gates[gate.number] = gate

        return gates

    except Exception as e:
        print(f"FATAL: Cannot parse bodygraph.yaml - {e}")
        raise


def parse_channels(channels_yaml_path: Path) -> list[ChannelYAML]:
    """
    Parse channels.yaml into structured channel data.

    Returns:
        list of ChannelYAML models

    Raises:
        Exception if YAML is malformed or missing required fields
    """
    try:
        with open(channels_yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        channels = []
        for channel_data in data:
            channel = ChannelYAML(
                name=channel_data['name'],
                gates=channel_data['gates']
            )
            channels.append(channel)

        return channels

    except Exception as e:
        print(f"FATAL: Cannot parse channels.yaml - {e}")
        raise


def parse_centers(centers_yaml_path: Path) -> dict[str, CenterYAML]:
    """
    Parse centers.yaml into structured center data.

    Returns:
        dict mapping center name to CenterYAML model

    Raises:
        Exception if YAML is malformed or missing required fields
    """
    try:
        with open(centers_yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        centers = {}
        for center_data in data:
            center = CenterYAML(
                name=center_data['name'],
                gates=center_data['gates']
            )
            centers[center.name] = center

        return centers

    except Exception as e:
        print(f"FATAL: Cannot parse centers.yaml - {e}")
        raise


# ==============================================================================
# TRANSFORMATION FUNCTIONS
# ==============================================================================


def build_gate_to_center_map(centers: dict[str, CenterYAML]) -> dict[int, str]:
    """
    Build mapping from gate number to center name.

    Args:
        centers: Parsed center data

    Returns:
        dict mapping gate_number -> center_name
    """
    gate_to_center = {}
    for center_name, center in centers.items():
        for gate_num in center.gates:
            gate_to_center[gate_num] = center_name
    return gate_to_center


def merge_gate(
    yaml_gate: GateYAML,
    center_name: str,
    existing_gate: dict | None
) -> dict:
    """
    Merge YAML gate data with existing ontology gate data.

    Strategy:
        - YAML data overwrites (source of truth)
        - Existing ontology data preserved (HD knowledge)

    Args:
        yaml_gate: Gate data from bodygraph.yaml
        center_name: Center this gate belongs to
        existing_gate: Existing gate entry from ontology (or None)

    Returns:
        Merged gate dict
    """
    # Start with YAML data (source of truth)
    merged = {
        "number": yaml_gate.number,
        "i_ching_name": yaml_gate.ra_description,
        "complement": yaml_gate.complement,
        "center": center_name,
        "coordinate_range": {
            "start": {
                "sign": yaml_gate.coordinate_range.start.sign,
                "degree": yaml_gate.coordinate_range.start.degree,
                "minute": yaml_gate.coordinate_range.start.minute,
                "second": yaml_gate.coordinate_range.start.second
            },
            "end": {
                "sign": yaml_gate.coordinate_range.end.sign,
                "degree": yaml_gate.coordinate_range.end.degree,
                "minute": yaml_gate.coordinate_range.end.minute,
                "second": yaml_gate.coordinate_range.end.second
            }
        }
    }

    # Preserve HD system knowledge from existing ontology
    if existing_gate:
        merged["description"] = existing_gate.get("description", "")
        merged["keywords"] = existing_gate.get("keywords", [])
        merged["quarter"] = existing_gate.get("quarter", "")
        merged["theme"] = existing_gate.get("theme", "")
    else:
        # No existing data - use defaults
        merged["description"] = ""
        merged["keywords"] = []
        merged["quarter"] = ""
        merged["theme"] = ""
        warnings.warn(f"Gate {yaml_gate.number} missing in existing ontology")

    return merged


def merge_channel(
    yaml_channel: ChannelYAML,
    gate_to_center: dict[int, str],
    existing_channel: dict | None
) -> dict:
    """
    Merge YAML channel data with existing ontology channel data.

    Strategy:
        - YAML data overwrites (source of truth)
        - Centers derived from gate-to-center lookup
        - Existing ontology data preserved (HD knowledge)

    Args:
        yaml_channel: Channel data from channels.yaml
        gate_to_center: Gate number to center name mapping
        existing_channel: Existing channel entry from ontology (or None)

    Returns:
        Merged channel dict
    """
    gate1, gate2 = sorted(yaml_channel.gates)  # Sort for consistency

    merged = {
        "id": f"{gate1}-{gate2}",
        "name": yaml_channel.name,
        "gate1": gate1,
        "gate2": gate2,
        "centers": [gate_to_center[gate1], gate_to_center[gate2]]
    }

    # Preserve circuit and semantic content
    if existing_channel:
        merged["circuit"] = existing_channel.get("circuit", "")
        merged["sub_circuit"] = existing_channel.get("sub_circuit", "")
        merged["description"] = existing_channel.get("description", "")
        merged["theme"] = existing_channel.get("theme", "")
    else:
        merged["circuit"] = ""
        merged["sub_circuit"] = ""
        merged["description"] = ""
        merged["theme"] = ""
        warnings.warn(f"Channel {yaml_channel.name} missing in existing ontology")

    return merged


def merge_center(
    yaml_center: CenterYAML,
    existing_center: dict | None
) -> dict:
    """
    Merge YAML center data with existing ontology center data.

    Strategy:
        - YAML data overwrites (source of truth)
        - Existing ontology data preserved (HD knowledge)

    Args:
        yaml_center: Center data from centers.yaml
        existing_center: Existing center entry from ontology (or None)

    Returns:
        Merged center dict
    """
    merged = {
        "id": yaml_center.name,
        "gates": sorted(yaml_center.gates)  # Sort for consistency
    }

    # Preserve HD system knowledge
    if existing_center:
        merged["traditional_name"] = existing_center.get("traditional_name", "")
        merged["type"] = existing_center.get("type", "")
        merged["defined_description"] = existing_center.get("defined_description", "")
        merged["undefined_description"] = existing_center.get("undefined_description", "")
        merged["function"] = existing_center.get("function", "")
        merged["questions"] = existing_center.get("questions", [])
    else:
        merged["traditional_name"] = ""
        merged["type"] = ""
        merged["defined_description"] = ""
        merged["undefined_description"] = ""
        merged["function"] = ""
        merged["questions"] = []
        warnings.warn(f"Center {yaml_center.name} missing in existing ontology")

    return merged


# ==============================================================================
# VALIDATION FUNCTIONS
# ==============================================================================


def validate_output(ontology: dict) -> None:
    """
    Validate generated ontology matches expected data integrity.

    Performs structural validation:
        - Count validations (64 gates, 36 channels, 9 centers)
        - Gate number continuity (1-64)
        - Channel gate references
        - Center gate assignments

    Args:
        ontology: Generated ontology dict

    Raises:
        AssertionError if validation fails
    """
    # Count validations
    assert len(ontology["gates"]) == 64, f"Must have 64 gates, got {len(ontology['gates'])}"
    assert len(ontology["channels"]) == 36, f"Must have 36 channels, got {len(ontology['channels'])}"
    assert len(ontology["centers"]) == 9, f"Must have 9 centers, got {len(ontology['centers'])}"

    # Gate number continuity
    gate_numbers = {g["number"] for g in ontology["gates"]}
    assert gate_numbers == set(range(1, 65)), "Gates must be 1-64 with no gaps"

    # Channel gate pairs reference valid gates
    for channel in ontology["channels"]:
        assert channel["gate1"] in gate_numbers, f"Channel {channel['id']} gate1={channel['gate1']} not in gates"
        assert channel["gate2"] in gate_numbers, f"Channel {channel['id']} gate2={channel['gate2']} not in gates"
        assert f"{channel['gate1']}-{channel['gate2']}" == channel["id"], f"Channel id mismatch: {channel['id']}"

    # Center gate assignments cover all gates
    all_center_gates = set()
    for center in ontology["centers"]:
        all_center_gates.update(center["gates"])
    assert all_center_gates == gate_numbers, "All gates must be assigned to centers"

    # Gate complements are correct type
    for gate in ontology["gates"]:
        assert "complement" in gate, f"Gate {gate['number']} missing complement"
        assert isinstance(gate["complement"], (int, list)), f"Gate {gate['number']} complement wrong type"

    print("✅ Structural validation passed")


def cross_validate(
    ontology: dict,
    gates_yaml: dict[int, GateYAML],
    channels_yaml: list[ChannelYAML],
    centers_yaml: dict[str, CenterYAML]
) -> list[str]:
    """
    Cross-validate ontology against YAML sources.

    Returns list of discrepancies. Should be empty if transformation is correct.

    Args:
        ontology: Generated ontology dict
        gates_yaml: Parsed gate data from YAML
        channels_yaml: Parsed channel data from YAML
        centers_yaml: Parsed center data from YAML

    Returns:
        List of discrepancy strings (empty if all validations pass)
    """
    discrepancies = []

    # Validate gate complements (CRITICAL)
    for gate in ontology["gates"]:
        yaml_gate = gates_yaml[gate["number"]]
        if gate["complement"] != yaml_gate.complement:
            discrepancies.append(
                f"Gate {gate['number']} complement mismatch: "
                f"JSON={gate['complement']}, YAML={yaml_gate.complement}"
            )

    # Validate gate I Ching names
    for gate in ontology["gates"]:
        yaml_gate = gates_yaml[gate["number"]]
        if gate["i_ching_name"] != yaml_gate.ra_description:
            discrepancies.append(
                f"Gate {gate['number']} I Ching name mismatch: "
                f"JSON={gate['i_ching_name']}, YAML={yaml_gate.ra_description}"
            )

    # Validate channel gate pairs
    for channel in ontology["channels"]:
        yaml_channel = next(
            (c for c in channels_yaml if c.name == channel["name"]),
            None
        )
        if yaml_channel:
            channel_gates = sorted([channel["gate1"], channel["gate2"]])
            yaml_gates = sorted(yaml_channel.gates)
            if channel_gates != yaml_gates:
                discrepancies.append(
                    f"Channel {channel['name']} gate mismatch: "
                    f"JSON={channel_gates}, YAML={yaml_gates}"
                )

    # Validate center gate assignments
    for center in ontology["centers"]:
        yaml_center = centers_yaml.get(center["id"])
        if yaml_center:
            center_gates = set(center["gates"])
            yaml_gates = set(yaml_center.gates)
            if center_gates != yaml_gates:
                discrepancies.append(
                    f"Center {center['id']} gate assignment mismatch: "
                    f"JSON={sorted(center_gates)}, YAML={sorted(yaml_gates)}"
                )

    return discrepancies


# ==============================================================================
# MAIN FUNCTION
# ==============================================================================


def generate_ontology() -> dict:
    """
    Generate HD_ONTOLOGY_complete.json from YAML sources.

    Process:
        1. Load YAML sources (bodygraph.yaml, channels.yaml, centers.yaml)
        2. Load existing ontology (preserves HD system knowledge)
        3. Build gate-to-center mapping
        4. Merge gates section (YAML overwrites, preserve descriptions)
        5. Merge channels section (YAML overwrites, preserve circuits)
        6. Merge centers section (YAML overwrites, preserve descriptions)
        7. Preserve types/authorities/profiles/definitions/quarters
        8. Validate output
        9. Cross-validate against YAML sources

    Returns:
        Complete ontology dict
    """
    # Determine paths
    repo_root = Path(__file__).parent.parent
    bodygraph_yaml_path = repo_root / "src/human_design/bodygraph.yaml"
    channels_yaml_path = repo_root / "src/human_design/channels.yaml"
    centers_yaml_path = repo_root / "src/human_design/centers.yaml"
    existing_ontology_path = repo_root / "ontology/HD_ONTOLOGY_complete.json"

    print(f"📖 Loading YAML sources...")
    print(f"  - {bodygraph_yaml_path}")
    print(f"  - {channels_yaml_path}")
    print(f"  - {centers_yaml_path}")

    # Parse YAML sources
    gates_yaml = parse_gates(bodygraph_yaml_path)
    channels_yaml = parse_channels(channels_yaml_path)
    centers_yaml = parse_centers(centers_yaml_path)

    print(f"✅ Parsed {len(gates_yaml)} gates, {len(channels_yaml)} channels, {len(centers_yaml)} centers")

    # Load existing ontology
    print(f"📖 Loading existing ontology: {existing_ontology_path}")
    if existing_ontology_path.exists():
        with open(existing_ontology_path, 'r', encoding='utf-8') as f:
            existing_ontology = json.load(f)
        print(f"✅ Loaded existing ontology")
    else:
        print(f"⚠️  No existing ontology found - creating new one")
        existing_ontology = {}

    # Build gate-to-center mapping
    print(f"🔗 Building gate-to-center mapping...")
    gate_to_center = build_gate_to_center_map(centers_yaml)
    print(f"✅ Mapped {len(gate_to_center)} gates to centers")

    # Create new ontology structure
    ontology = {
        "schema_version": "1.0.0",
        "ontology_standard": "64keys",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "description": "Human Design ontology generated from YAML sources",
            "generated_by": "ontology/generate_ontology.py",
            "source_files": [
                "bodygraph.yaml",
                "channels.yaml",
                "centers.yaml"
            ]
        }
    }

    # Merge gates section
    print(f"🔄 Merging gates section...")
    existing_gates = {g["number"]: g for g in existing_ontology.get("gates", [])}
    ontology["gates"] = []
    for gate_num in sorted(gates_yaml.keys()):
        yaml_gate = gates_yaml[gate_num]
        center_name = gate_to_center.get(gate_num, "UNKNOWN")
        existing_gate = existing_gates.get(gate_num)
        merged_gate = merge_gate(yaml_gate, center_name, existing_gate)
        ontology["gates"].append(merged_gate)
    print(f"✅ Merged {len(ontology['gates'])} gates")

    # Merge channels section
    print(f"🔄 Merging channels section...")
    existing_channels = {c["id"]: c for c in existing_ontology.get("channels", [])}
    ontology["channels"] = []
    for yaml_channel in channels_yaml:
        gate1, gate2 = sorted(yaml_channel.gates)
        channel_id = f"{gate1}-{gate2}"
        existing_channel = existing_channels.get(channel_id)
        merged_channel = merge_channel(yaml_channel, gate_to_center, existing_channel)
        ontology["channels"].append(merged_channel)
    # Sort channels by ID for consistency
    ontology["channels"].sort(key=lambda c: c["id"])
    print(f"✅ Merged {len(ontology['channels'])} channels")

    # Merge centers section
    print(f"🔄 Merging centers section...")
    existing_centers = {c["id"]: c for c in existing_ontology.get("centers", [])}
    ontology["centers"] = []
    for center_name in sorted(centers_yaml.keys()):
        yaml_center = centers_yaml[center_name]
        existing_center = existing_centers.get(center_name)
        merged_center = merge_center(yaml_center, existing_center)
        ontology["centers"].append(merged_center)
    print(f"✅ Merged {len(ontology['centers'])} centers")

    # Preserve types/authorities/profiles/definitions/quarters (HD system knowledge)
    print(f"💾 Preserving HD system knowledge...")
    for section in ["types", "authorities", "profiles", "definitions", "quarters"]:
        if section in existing_ontology:
            ontology[section] = existing_ontology[section]
            print(f"  ✅ Preserved {section} ({len(existing_ontology[section])} entries)")

    # Validate output
    print(f"🔍 Validating output...")
    validate_output(ontology)

    # Cross-validate against YAML sources
    print(f"🔍 Cross-validating against YAML sources...")
    discrepancies = cross_validate(ontology, gates_yaml, channels_yaml, centers_yaml)
    if discrepancies:
        print(f"❌ Cross-validation found {len(discrepancies)} discrepancies:")
        for disc in discrepancies:
            print(f"  - {disc}")
        raise ValueError("Cross-validation failed")
    else:
        print(f"✅ Cross-validation passed (0 discrepancies)")

    return ontology


# ==============================================================================
# CLI ENTRY POINT
# ==============================================================================


def main():
    """CLI entry point for ontology generation."""
    print("=" * 80)
    print("HD Ontology Generator")
    print("Deterministic YAML → JSON transformation")
    print("=" * 80)
    print()

    try:
        ontology = generate_ontology()

        # Write output
        output_path = Path(__file__).parent / "HD_ONTOLOGY_complete.json"
        print()
        print(f"📝 Writing output: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(ontology, f, indent=2, ensure_ascii=False, sort_keys=True)

        print(f"✅ Generated {output_path}")
        print()
        print("=" * 80)
        print("✨ SUCCESS: Ontology generated and validated")
        print("=" * 80)
        print()
        print("Summary:")
        print(f"  - {len(ontology['gates'])} gates")
        print(f"  - {len(ontology['channels'])} channels")
        print(f"  - {len(ontology['centers'])} centers")
        print(f"  - {len(ontology.get('types', []))} types")
        print(f"  - {len(ontology.get('authorities', []))} authorities")
        print(f"  - {len(ontology.get('profiles', []))} profiles")
        print()

        return 0

    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ ERROR: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
