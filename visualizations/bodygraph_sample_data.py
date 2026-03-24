#!/usr/bin/env python3
"""
Generate sample bodygraph data for D3 visualization.

This script creates a RawBodyGraph and exports it as JSON suitable
for embedding in the standalone HTML visualization.
"""

import json
from datetime import datetime
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from human_design.models.bodygraph import BirthInfo, RawBodyGraph
from human_design.models.coordinates import LocalTime


def generate_bodygraph_data():
    """Generate sample bodygraph data and export as JSON."""
    
    # Create birth info for a sample person
    birth_info = BirthInfo(
        date="1990-01-15",
        localtime=LocalTime(datetime(1990, 1, 15, 10, 30)),
        city="New York",
        country="USA",
    )
    
    # Calculate the bodygraph
    bodygraph = RawBodyGraph(birth_info=birth_info)
    
    # Extract data for D3 visualization
    data = {
        "birthInfo": {
            "date": birth_info.date,
            "city": birth_info.city,
            "country": birth_info.country,
            "coordinates": {
                "latitude": birth_info.coordinates[0],
                "longitude": birth_info.coordinates[1],
            },
        },
        "conscious_activations": [
            {
                "planet": a.planet.name,
                "gate": a.gate,
                "line": a.line,
                "gate_line": a.gate_line,
            }
            for a in bodygraph.conscious_activations
        ],
        "unconscious_activations": [
            {
                "planet": a.planet.name,
                "gate": a.gate,
                "line": a.line,
                "gate_line": a.gate_line,
            }
            for a in bodygraph.unconscious_activations
        ],
        "activated_gates": sorted(list(bodygraph.all_activated_gates)),
        "active_channels": [
            {
                "id": f"{c.channel_id}",
                "name": c.name,
                "gate_a": c.gate_a,
                "gate_b": c.gate_b,
                "center_a": c.center_a,
                "center_b": c.center_b,
            }
            for c in bodygraph.active_channels
        ],
        "defined_centers": sorted(list(bodygraph.defined_centers)),
        "type": bodygraph.type.value if hasattr(bodygraph.type, 'value') else str(bodygraph.type),
        "authority": bodygraph.authority.value if hasattr(bodygraph.authority, 'value') else str(bodygraph.authority),
        "profile": {
            "notation": bodygraph.profile.notation,
        },
    }
    
    return data


if __name__ == "__main__":
    data = generate_bodygraph_data()
    print(json.dumps(data, indent=2))
