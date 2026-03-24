#!/usr/bin/env python
"""Generate example bodygraphs for visualization testing.

Uses realistic birth data for example people.
"""

import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from human_design.models.bodygraph import BirthInfo, RawBodyGraph
from human_design.models.coordinates import LocalTime
from human_design.models.core import CenterName

load_dotenv()

def generate_bodygraph(name: str, date: str, time: str, city: str, state: str) -> dict:
    """Generate bodygraph and return as visualization-friendly dict."""

    # Parse date and time
    year, month, day = map(int, date.split('-'))
    hour, minute = map(int, time.split(':'))
    birth_datetime = datetime(year, month, day, hour, minute)

    birth_info = BirthInfo(
        date=date,
        localtime=LocalTime(birth_datetime),
        city=city,
        state=state,
        country="US",
    )

    # Calculate bodygraph
    raw_bg = RawBodyGraph(birth_info=birth_info)

    # Convert to visualization format
    # All 9 centers with their definition status
    all_centers: list[CenterName] = [
        "INSPIRATION", "MIND", "EXPRESSION", "IDENTITY", "WILLPOWER",
        "EMOTION", "DRIVE", "LIFEFORCE", "INTUITION"
    ]

    centers_data = {
        center_name: {"is_defined": center_name in raw_bg.defined_centers}
        for center_name in all_centers
    }

    # Combine conscious (personality) and unconscious (design) activations
    gates_data = []
    for activation in raw_bg.conscious_activations:
        gates_data.append({
            "number": activation.gate,
            "line": activation.line,
            "planet": activation.planet.value,
            "is_personality": True,
        })
    for activation in raw_bg.unconscious_activations:
        gates_data.append({
            "number": activation.gate,
            "line": activation.line,
            "planet": activation.planet.value,
            "is_personality": False,
        })

    return {
        "name": name,
        "birth_info": {
            "date": date,
            "time": time,
            "city": city,
            "state": state,
        },
        "centers": centers_data,
        "gates": gates_data,
        "type": raw_bg.type.value if raw_bg.type else None,
        "authority": raw_bg.authority.value if raw_bg.authority else None,
        "profile": raw_bg.profile.profile_notation if raw_bg.profile else None,
    }


if __name__ == "__main__":
    print("🎨 Generating Example Bodygraphs for D3 Visualization\n")

    # Example people with diverse charts
    examples = [
        {
            "name": "Alex Chen",
            "date": "1988-03-15",
            "time": "14:30",
            "city": "San Francisco",
            "state": "CA",
        },
        {
            "name": "Jordan Martinez",
            "date": "1992-07-22",
            "time": "08:45",
            "city": "Austin",
            "state": "TX",
        },
        {
            "name": "Sam Taylor",
            "date": "1985-11-08",
            "time": "22:15",
            "city": "Portland",
            "state": "OR",
        },
    ]

    bodygraphs = []

    for person in examples:
        print(f"📊 Generating bodygraph for {person['name']}...")
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
            print(f"  ✓ Birth: {bg_data['birth_info']['date']} at {bg_data['birth_info']['time']}")
            print(f"  ✓ Location: {bg_data['birth_info']['city']}, {bg_data['birth_info']['state']}")
            print(f"  ✓ Centers: {defined_centers}/9 defined")
            print(f"  ✓ Gates: {len(bg_data['gates'])} active")
            print(f"  ✓ Type: {bg_data['type']}")
            print(f"  ✓ Authority: {bg_data['authority']}")
            print(f"  ✓ Profile: {bg_data['profile']}")
            print()
        except Exception as e:
            print(f"  ✗ Failed: {e}\n")
            import traceback
            traceback.print_exc()

    if not bodygraphs:
        print("❌ No bodygraphs generated!")
        exit(1)

    # Save to file
    output_file = Path("bodygraph_examples.json")
    with open(output_file, "w") as f:
        json.dump(bodygraphs, f, indent=2)

    print(f"✅ Saved {len(bodygraphs)} bodygraphs to {output_file}")
    print()
    print("📝 Next steps:")
    print("  1. Review bodygraph_examples.json")
    print("  2. Update D3 visualization strand to use this data")
    print("  3. Run: /dodo:compose_strand with opus model")
