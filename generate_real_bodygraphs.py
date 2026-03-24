#!/usr/bin/env python
"""Generate real bodygraphs for visualization examples.

Uses actual birth data for:
- Neat Nate (Nathan Neibauer)
- Rebecca (Rebecca Jolli)
"""

import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from human_design.models.bodygraph import BirthInfo, RawBodyGraph
from human_design.models.coordinates import LocalTime

load_dotenv()

def generate_bodygraph(name: str, date: str, time: str, city: str, state: str) -> dict:
    """Generate bodygraph and return as dict.

    Args:
        name: Person's name
        date: Birth date (YYYY-MM-DD)
        time: Birth time (HH:MM)
        city: Birth city
        state: Birth state

    Returns:
        Dict with bodygraph data
    """
    # Parse date and time
    year, month, day = map(int, date.split('-'))
    hour, minute = map(int, time.split(':'))

    birth_datetime = datetime(year, month, day, hour, minute)

    birth_info = BirthInfo(
        date=date,
        localtime=LocalTime(birth_datetime),
        city=city,
        state=state,
    )

    # Calculate bodygraph
    raw_bg = RawBodyGraph.from_birth_info(birth_info)

    # Convert to visualization-friendly format
    return {
        "name": name,
        "birth_info": {
            "date": date,
            "time": time,
            "city": city,
            "state": state,
        },
        "centers": {
            center_name: {"is_defined": center.is_defined}
            for center_name, center in raw_bg.centers.items()
        },
        "gates": [
            {
                "number": gate.gate_number,
                "line": gate.line_number,
                "is_personality": gate.is_personality,
            }
            for gate in raw_bg.activations
        ],
        "type": raw_bg.type.value if raw_bg.type else None,
        "authority": raw_bg.authority.value if raw_bg.authority else None,
        "profile": f"{raw_bg.profile.personality}/{raw_bg.profile.design}" if raw_bg.profile else None,
    }


if __name__ == "__main__":
    print("🎨 Generating Real Bodygraphs for D3 Visualization\n")

    # TODO: Get actual birth data from user
    print("⚠️  PLACEHOLDER DATA - Need real birth info!")
    print("Please provide birth data for:")
    print("  1. Neat Nate (Nathan Neibauer)")
    print("  2. Rebecca (Rebecca Jolli)")
    print()

    # Example placeholders (user will replace)
    examples = [
        {
            "name": "Neat Nate",
            "date": "1990-01-15",  # PLACEHOLDER
            "time": "09:13",       # PLACEHOLDER
            "city": "Albuquerque", # PLACEHOLDER
            "state": "NM",         # PLACEHOLDER
        },
        {
            "name": "Rebecca",
            "date": "1985-06-21",  # PLACEHOLDER
            "time": "14:30",       # PLACEHOLDER
            "city": "Portland",    # PLACEHOLDER
            "state": "OR",         # PLACEHOLDER
        },
    ]

    bodygraphs = []

    for person in examples:
        print(f"Generating bodygraph for {person['name']}...")
        try:
            bg_data = generate_bodygraph(
                person["name"],
                person["date"],
                person["time"],
                person["city"],
                person["state"],
            )
            bodygraphs.append(bg_data)

            # Show summary
            defined_centers = sum(1 for c in bg_data["centers"].values() if c["is_defined"])
            print(f"  ✓ {defined_centers}/9 centers defined")
            print(f"  ✓ {len(bg_data['gates'])} gates active")
            print(f"  ✓ Type: {bg_data['type']}")
            print(f"  ✓ Authority: {bg_data['authority']}")
            print(f"  ✓ Profile: {bg_data['profile']}")
            print()
        except Exception as e:
            print(f"  ✗ Failed: {e}\n")

    # Save to file
    output_file = Path("bodygraph_examples.json")
    with open(output_file, "w") as f:
        json.dump(bodygraphs, f, indent=2)

    print(f"💾 Saved {len(bodygraphs)} bodygraphs to {output_file}")
    print()
    print("📝 Next steps:")
    print("  1. Update birth data in this script")
    print("  2. Run: uv run python generate_real_bodygraphs.py")
    print("  3. Use bodygraph_examples.json for D3 visualization")
