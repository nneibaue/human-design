#!/usr/bin/env python
"""Fetch real bodygraphs from 64keys storage for visualization examples.

Retrieves birth data for:
- Neat Nate (Nathan Neibauer)
- Rebecca (Rebecca Jolli)
"""

import json
from pathlib import Path
from dotenv import load_dotenv

from human_design.api import list_people, get_person
from human_design.models.bodygraph import RawBodyGraph

load_dotenv()

def bodygraph_to_dict(person_name: str, bg: RawBodyGraph) -> dict:
    """Convert RawBodyGraph to visualization-friendly dict.

    Args:
        person_name: Person's name
        bg: RawBodyGraph instance

    Returns:
        Dict with bodygraph data for D3 visualization
    """
    return {
        "name": person_name,
        "centers": {
            center_name: {"is_defined": center.is_defined}
            for center_name, center in bg.centers.items()
        },
        "gates": [
            {
                "number": gate.gate_number,
                "line": gate.line_number,
                "is_personality": gate.is_personality,
            }
            for gate in bg.activations
        ],
        "type": bg.type.value if bg.type else None,
        "authority": bg.authority.value if bg.authority else None,
        "profile": f"{bg.profile.personality}/{bg.profile.design}" if bg.profile else None,
    }


if __name__ == "__main__":
    print("🔍 Fetching bodygraphs from 64keys storage\n")

    # List all people to see what's available
    print("📋 People in storage:")
    all_people = list_people()

    if not all_people:
        print("  ⚠️  No people found in storage!")
        print("  Add people using: hd bodygraph <date> <time> <city> <state>")
        exit(1)

    for person in all_people:
        print(f"  - {person.name} (ID: {person.id})")
    print()

    # Search for our targets
    targets = ["Neat Nate", "Nathan", "Rebecca"]
    bodygraphs = []

    for target in targets:
        try:
            print(f"Looking for '{target}'...")
            person = get_person(target)
            print(f"  ✓ Found: {person.name}")

            # Get their bodygraph
            bg = RawBodyGraph.from_birth_info(person.birth_info)

            # Convert to dict
            bg_data = bodygraph_to_dict(person.name, bg)
            bodygraphs.append(bg_data)

            # Show summary
            defined_centers = sum(1 for c in bg_data["centers"].values() if c["is_defined"])
            print(f"    Birth: {person.birth_info.date} {person.birth_info.localtime.time}")
            print(f"    Location: {person.birth_info.city}, {person.birth_info.state}")
            print(f"    Centers: {defined_centers}/9 defined")
            print(f"    Gates: {len(bg_data['gates'])} active")
            print(f"    Type: {bg_data['type']}")
            print(f"    Authority: {bg_data['authority']}")
            print(f"    Profile: {bg_data['profile']}")
            print()

        except ValueError as e:
            print(f"  ✗ {e}\n")
            continue

    if not bodygraphs:
        print("❌ No bodygraphs found!")
        print("Available people:")
        for person in all_people:
            print(f"  - {person.name}")
        exit(1)

    # Save to file
    output_file = Path("bodygraph_examples.json")
    with open(output_file, "w") as f:
        json.dump(bodygraphs, f, indent=2)

    print(f"✅ Saved {len(bodygraphs)} bodygraphs to {output_file}")
    print()
    print("📝 Next steps:")
    print("  1. Review bodygraph_examples.json")
    print("  2. Use this data in D3 visualization test")
