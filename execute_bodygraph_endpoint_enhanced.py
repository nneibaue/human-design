#!/usr/bin/env python3
"""Execute bodygraph endpoint implementation strand using DODO-Lite with enhanced context.

This strand composes three agents with detailed, concrete examples:
1. implementer - FastAPI endpoint + data transformation
2. d3_specialist - D3.js v7 visualization with Rebecca Energy aesthetic
3. test_engineer - Comprehensive test suite

Timeline: 24-30 minutes
"""

import asyncio
import json
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from human_design.strands import create_strand


async def execute_bodygraph_endpoint_strand():
    """Execute the bodygraph endpoint implementation strand with enhanced context."""

    print("=" * 80)
    print("🎨 BODYGRAPH ENDPOINT IMPLEMENTATION STRAND (ENHANCED)")
    print("=" * 80)
    print("Goal: Build /api/bodygraph endpoint with D3 visualization")
    print("Agents: implementer → d3_specialist → test_engineer")
    print("Timeline: 24-30 minutes")
    print("=" * 80)
    print()

    # Build comprehensive context with concrete examples
    context = {
        "task_type": "IMPLEMENTATION",
        "starting_point": "We have RawBodyGraph models that calculate bodygraphs. We need to expose them via API with D3 visualization.",

        "existing_code_examples": {
            "birth_info_creation": '''
# How to create BirthInfo (existing model)
from human_design.models import BirthInfo, LocalTime
from datetime import datetime

birth_info = BirthInfo(
    date="1990-01-15",
    localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
    city="Albuquerque",
    country="NM"
)
''',
            "bodygraph_calculation": '''
# How to calculate RawBodyGraph (existing model)
from human_design.models.bodygraph import RawBodyGraph

bodygraph = RawBodyGraph(birth_info=birth_info)

# Available properties:
bodygraph.conscious_activations  # List[RawActivation]
bodygraph.unconscious_activations  # List[RawActivation]
bodygraph.all_activated_gates  # set[GateNumber]
bodygraph.active_channels  # list[ChannelDefinition]
bodygraph.defined_centers  # set[CenterName]
bodygraph.type  # HDType (Initiator, Builder, Specialist, Coordinator, Observer)
bodygraph.authority  # Authority (Emotional, Sacral, Splenic, etc.)
bodygraph.profile  # Profile (e.g., "3/5")
''',
            "existing_endpoint_pattern": '''
# Example of existing endpoint in app.py
@app.get("/api/people/{person_id}")
async def get_person(person_id: int) -> Person:
    """Get a single person by ID."""
    people = fetch_all_people()
    for person in people:
        if person.id == person_id:
            return person
    raise HTTPException(status_code=404, detail=f"Person {person_id} not found")
'''
        },

        "agent_specific_instructions": {
            "implementer": {
                "task": "Create FastAPI endpoint and data transformation layer",
                "specific_actions": [
                    "1. Add @app.post('/api/bodygraph') endpoint to src/human_design/web/app.py",
                    "2. Create src/human_design/api/bodygraph_renderer.py with BodygraphRenderer class",
                    "3. BodygraphRenderer.to_d3_format() must convert RawBodyGraph to D3-friendly JSON",
                    "4. Handle errors: invalid dates, geocoding failures, missing timezone",
                    "5. Return JSON matching the response_schema below"
                ],
                "code_to_create": '''
# FILE: src/human_design/api/bodygraph_renderer.py
from typing import Any
from ..models.bodygraph import RawBodyGraph
from ..models.core import CenterName

class BodygraphRenderer:
    """Convert RawBodyGraph to D3-friendly JSON format."""

    # Center coordinates for fixed bodygraph geometry (SVG viewBox 800x1000)
    CENTER_COORDINATES = {
        "INSPIRATION": (400, 100),   # Head - top triangle
        "MIND": (400, 200),          # Ajna - forehead triangle
        "EXPRESSION": (400, 350),    # Throat - neck square
        "IDENTITY": (400, 500),      # G-Center - heart diamond
        "WILLPOWER": (300, 500),     # Ego/Will - left triangle
        "EMOTION": (500, 650),       # Solar Plexus - right triangle
        "LIFEFORCE": (400, 700),     # Sacral - belly square
        "DRIVE": (400, 850),         # Root - bottom square
        "INTUITION": (300, 650),     # Spleen - left triangle
    }

    CENTER_SHAPES = {
        "LIFEFORCE": "square",
        "EMOTION": "triangle",
        "INTUITION": "triangle",
        "IDENTITY": "diamond",
        "WILLPOWER": "triangle",
        "DRIVE": "square",
        "EXPRESSION": "square",
        "MIND": "triangle",
        "INSPIRATION": "triangle",
    }

    @staticmethod
    def to_d3_format(bodygraph: RawBodyGraph) -> dict[str, Any]:
        """Transform bodygraph to D3 visualization format."""
        # Build centers array
        centers = []
        for center_name in CenterName.__args__:
            centers.append({
                "name": center_name,
                "defined": center_name in bodygraph.defined_centers,
                "x": BodygraphRenderer.CENTER_COORDINATES[center_name][0],
                "y": BodygraphRenderer.CENTER_COORDINATES[center_name][1],
                "shape": BodygraphRenderer.CENTER_SHAPES[center_name],
            })

        # Build channels array
        channels = []
        channel_registry = ChannelRegistry.load()
        for channel in bodygraph.active_channels:
            channels.append({
                "id": f"{channel.gate_a}-{channel.gate_b}",
                "gate_a": channel.gate_a,
                "gate_b": channel.gate_b,
                "defined": True,
                "from_center": channel.center_a,
                "to_center": channel.center_b,
            })

        # Build gates array
        gates = []
        for activation in bodygraph.conscious_activations:
            gates.append({
                "number": activation.gate,
                "line": activation.line,
                "planet": activation.planet.name,
                "activation": "conscious",
            })
        for activation in bodygraph.unconscious_activations:
            gates.append({
                "number": activation.gate,
                "line": activation.line,
                "planet": activation.planet.name,
                "activation": "unconscious",
            })

        return {
            "centers": centers,
            "channels": channels,
            "gates": gates,
            "type": bodygraph.type.value,
            "authority": bodygraph.authority.value,
            "profile": str(bodygraph.profile),
        }

# FILE: src/human_design/web/app.py (add this endpoint)
@app.post("/api/bodygraph")
async def calculate_bodygraph(
    date: str = Query(..., description="Birth date (YYYY-MM-DD)", example="1990-01-15"),
    time: str = Query(..., description="Birth time (HH:MM)", example="09:13"),
    location: str = Query(..., description="City, State/Country", example="Albuquerque, NM"),
) -> dict[str, Any]:
    """Calculate bodygraph from birth information.

    Returns D3-friendly JSON with centers, channels, and gates.
    """
    try:
        # Parse birth data
        from datetime import datetime
        from ..models.bodygraph import BirthInfo, RawBodyGraph
        from ..models.coordinates import LocalTime
        from ..api.bodygraph_renderer import BodygraphRenderer

        # Split location into city and country
        parts = location.split(",")
        if len(parts) < 2:
            raise ValueError("Location must be in format: City, State/Country")

        city = parts[0].strip()
        country = ",".join(parts[1:]).strip()

        # Parse date and time
        date_time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

        # Create BirthInfo
        birth_info = BirthInfo(
            date=date,
            localtime=LocalTime(date_time),
            city=city,
            country=country,
        )

        # Calculate bodygraph
        bodygraph = RawBodyGraph(birth_info=birth_info)

        # Transform to D3 format
        renderer = BodygraphRenderer()
        bodygraph_data = renderer.to_d3_format(bodygraph)

        return {
            "birth_info": {
                "date": date,
                "time": time,
                "location": location,
                "timezone": birth_info.timezone,
            },
            "bodygraph": bodygraph_data,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=f"Geocoding error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")
'''
            },

            "d3_specialist": {
                "task": "Create D3.js v7 visualization with Rebecca Energy aesthetic",
                "specific_actions": [
                    "1. Create src/human_design/web/static/js/d3-bodygraph.js",
                    "2. Create src/human_design/web/static/css/bodygraph.css",
                    "3. Use D3 v7 API (.join() method, not .enter()/.exit())",
                    "4. Apply Rebecca Energy color palette (warm browns, golds, greens)",
                    "5. Add interactive hover tooltips and click handlers",
                    "6. Create demo page: src/human_design/web/templates/bodygraph.html"
                ],
                "code_to_create": '''
// FILE: src/human_design/web/static/js/d3-bodygraph.js
/**
 * D3.js v7 Bodygraph Visualization
 * Rebecca Energy aesthetic: warm, cozy, magical
 */

function renderBodygraph(data, containerId) {
    const container = d3.select(containerId);
    const width = 800;
    const height = 1000;

    // Create SVG
    const svg = container.append("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", `0 0 ${width} ${height}`)
        .attr("class", "bodygraph-svg");

    // Draw centers
    const centers = svg.selectAll(".center")
        .data(data.centers, d => d.name)
        .join("g")
        .attr("class", d => `center ${d.defined ? "defined" : "undefined"}`)
        .attr("transform", d => `translate(${d.x}, ${d.y})`);

    // Center shapes
    centers.append("path")
        .attr("d", d => getCenterShape(d.shape))
        .attr("class", d => d.defined ? "center-defined" : "center-undefined");

    // Center labels
    centers.append("text")
        .text(d => d.name)
        .attr("class", "center-label")
        .attr("text-anchor", "middle")
        .attr("dy", "0.3em");

    // Draw channels
    const channels = svg.selectAll(".channel")
        .data(data.channels)
        .join("path")
        .attr("class", "channel active")
        .attr("d", d => getChannelPath(d.from_center, d.to_center, data.centers));

    // Draw gates
    const gates = svg.selectAll(".gate")
        .data(data.gates)
        .join("circle")
        .attr("class", d => `gate ${d.activation}`)
        .attr("cx", d => getGatePosition(d.number, data.centers).x)
        .attr("cy", d => getGatePosition(d.number, data.centers).y)
        .attr("r", 8);

    // Tooltips
    gates.on("mouseover", (event, d) => {
        showTooltip(event, `Gate ${d.number}.${d.line} (${d.planet})`);
    }).on("mouseout", hideTooltip);
}

function getCenterShape(shape) {
    const size = 60;
    switch (shape) {
        case "square":
            return `M ${-size/2} ${-size/2} h ${size} v ${size} h ${-size} Z`;
        case "triangle":
            return `M 0 ${-size/2} L ${size/2} ${size/2} L ${-size/2} ${size/2} Z`;
        case "diamond":
            return `M 0 ${-size/2} L ${size/2} 0 L 0 ${size/2} L ${-size/2} 0 Z`;
        default:
            return "";
    }
}

function getChannelPath(fromCenter, toCenter, centers) {
    const from = centers.find(c => c.name === fromCenter);
    const to = centers.find(c => c.name === toCenter);
    return `M ${from.x} ${from.y} L ${to.x} ${to.y}`;
}

// FILE: src/human_design/web/static/css/bodygraph.css
/* Rebecca Energy Aesthetic */
:root {
    --defined-center: #8B4513;      /* Saddle brown */
    --undefined-center: #F5F5DC;    /* Beige */
    --conscious: #4A5D23;           /* Dark olive green */
    --unconscious: #8B0000;         /* Dark red */
    --emergent: #DAA520;            /* Goldenrod */
    --background: #2C1810;          /* Deep brown */
    --text: #F5E6D3;                /* Warm cream */
}

.bodygraph-svg {
    background: var(--background);
    border-radius: 8px;
}

.center-defined {
    fill: var(--defined-center);
    stroke: var(--text);
    stroke-width: 2;
}

.center-undefined {
    fill: var(--undefined-center);
    stroke: var(--text);
    stroke-width: 2;
}

.center-label {
    fill: var(--text);
    font-family: "Georgia", serif;
    font-size: 12px;
}

.channel.active {
    stroke: var(--defined-center);
    stroke-width: 4;
    fill: none;
}

.gate.conscious {
    fill: var(--conscious);
    stroke: var(--text);
    stroke-width: 1;
}

.gate.unconscious {
    fill: var(--unconscious);
    stroke: var(--text);
    stroke-width: 1;
}
'''
            },

            "test_engineer": {
                "task": "Create comprehensive test suite",
                "specific_actions": [
                    "1. Create tests/test_bodygraph_endpoint.py",
                    "2. Test happy path: valid birth data returns 200",
                    "3. Test invalid date format returns 400",
                    "4. Test invalid location format returns 400",
                    "5. Test response schema matches expected structure",
                    "6. Use parametrized tests for multiple birth dates",
                    "7. Use FastAPI TestClient for endpoint testing"
                ],
                "code_to_create": '''
# FILE: tests/test_bodygraph_endpoint.py
import pytest
from fastapi.testclient import TestClient
from human_design.web.app import app

client = TestClient(app)

def test_bodygraph_endpoint_success():
    """Test successful bodygraph calculation."""
    response = client.post(
        "/api/bodygraph",
        params={
            "date": "1990-01-15",
            "time": "09:13",
            "location": "Albuquerque, NM"
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Check birth_info structure
    assert "birth_info" in data
    assert data["birth_info"]["date"] == "1990-01-15"
    assert data["birth_info"]["time"] == "09:13"
    assert "timezone" in data["birth_info"]

    # Check bodygraph structure
    assert "bodygraph" in data
    bodygraph = data["bodygraph"]

    assert "centers" in bodygraph
    assert len(bodygraph["centers"]) == 9  # 9 centers

    assert "channels" in bodygraph
    assert isinstance(bodygraph["channels"], list)

    assert "gates" in bodygraph
    assert len(bodygraph["gates"]) == 26  # 13 conscious + 13 unconscious

    assert "type" in bodygraph
    assert "authority" in bodygraph
    assert "profile" in bodygraph

@pytest.mark.parametrize("date,time,location", [
    ("1990-01-15", "09:13", "Albuquerque, NM"),
    ("1985-06-20", "14:30", "New York, NY"),
    ("2000-12-25", "00:00", "London, UK"),
])
def test_bodygraph_multiple_birth_dates(date, time, location):
    """Test bodygraph calculation with multiple birth dates."""
    response = client.post(
        "/api/bodygraph",
        params={"date": date, "time": time, "location": location}
    )
    assert response.status_code == 200

def test_bodygraph_invalid_date():
    """Test invalid date format returns 400."""
    response = client.post(
        "/api/bodygraph",
        params={
            "date": "invalid",
            "time": "09:13",
            "location": "Albuquerque, NM"
        }
    )
    assert response.status_code == 400

def test_bodygraph_invalid_location():
    """Test invalid location format returns 400."""
    response = client.post(
        "/api/bodygraph",
        params={
            "date": "1990-01-15",
            "time": "09:13",
            "location": "InvalidLocation"
        }
    )
    assert response.status_code == 400
'''
            }
        },

        "response_schema": {
            "birth_info": {
                "date": "1990-01-15",
                "time": "09:13",
                "location": "Albuquerque, NM",
                "timezone": "America/Denver"
            },
            "bodygraph": {
                "centers": [
                    {
                        "name": "LIFEFORCE",
                        "defined": True,
                        "x": 400,
                        "y": 700,
                        "shape": "square"
                    }
                ],
                "channels": [
                    {
                        "id": "42-53",
                        "gate_a": 42,
                        "gate_b": 53,
                        "defined": True,
                        "from_center": "LIFEFORCE",
                        "to_center": "EMOTION"
                    }
                ],
                "gates": [
                    {
                        "number": 42,
                        "line": 3,
                        "planet": "SUN",
                        "activation": "conscious"
                    }
                ],
                "type": "Specialist",
                "authority": "Emotional",
                "profile": "3/5"
            }
        }
    }

    problem = """BUILD A COMPLETE BODYGRAPH ENDPOINT WITH D3 VISUALIZATION

YOU MUST CREATE THESE FILES:
1. src/human_design/api/bodygraph_renderer.py - BodygraphRenderer class
2. src/human_design/web/app.py - Add @app.post('/api/bodygraph') endpoint
3. src/human_design/web/static/js/d3-bodygraph.js - D3 visualization
4. src/human_design/web/static/css/bodygraph.css - Rebecca Energy styling
5. tests/test_bodygraph_endpoint.py - Comprehensive tests

IMPLEMENTER AGENT:
- Read the existing code examples in context["existing_code_examples"]
- Use RawBodyGraph and BirthInfo from existing models (DON'T RECREATE)
- Create bodygraph_renderer.py with BodygraphRenderer class
- Add endpoint to app.py following existing endpoint patterns
- See context["agent_specific_instructions"]["implementer"]["code_to_create"]

D3 SPECIALIST AGENT:
- Create D3.js v7 visualization (use .join() method)
- Fixed bodygraph geometry (coordinates provided in implementer's code)
- Rebecca Energy palette: browns #8B4513, creams #F5E6D3, greens #4A5D23
- Interactive tooltips on hover
- See context["agent_specific_instructions"]["d3_specialist"]["code_to_create"]

TEST ENGINEER AGENT:
- Use FastAPI TestClient for endpoint testing
- Test happy path (200 response)
- Test error cases (400 for invalid input)
- Parametrized tests for multiple birth dates
- See context["agent_specific_instructions"]["test_engineer"]["code_to_create"]

EXPECTED OUTPUT: Working /api/bodygraph endpoint that returns D3-ready JSON
"""

    print("Creating strand with 3 Opus agents and detailed context...")
    strand = create_strand(
        problem=problem,
        agents=["implementer", "d3_specialist", "test_engineer"],
        strand_type="implementation",
        context=context,
    )

    print(f"✓ Strand ID: {strand.definition.strand_id}")
    print(f"✓ Agents: {', '.join(strand.definition.agents)}")
    print(f"✓ Context size: {len(json.dumps(context))} bytes")
    print()
    print("▶️  Executing strand with enhanced context...")
    print()

    result = await strand.run()

    print()
    print("=" * 80)
    print("✅ BODYGRAPH ENDPOINT STRAND COMPLETE")
    print("=" * 80)
    print(f"Status: {result.status}")
    print(f"Strand ID: {result.strand_id}")
    print()

    if result.findings:
        print("📋 Agent Findings:")
        for agent_name, finding in result.findings.items():
            print(f"\n{'='*60}")
            print(f"{agent_name.upper()}:")
            print('='*60)
            if isinstance(finding, dict):
                print(json.dumps(finding, indent=2))
            else:
                print(f"{finding}")

    print()
    print("🔍 VERIFICATION STEPS:")
    print("1. Check files created:")
    print("   - src/human_design/api/bodygraph_renderer.py")
    print("   - src/human_design/web/static/js/d3-bodygraph.js")
    print("   - src/human_design/web/static/css/bodygraph.css")
    print("   - tests/test_bodygraph_endpoint.py")
    print()
    print("2. Run tests: pytest tests/test_bodygraph_endpoint.py -v")
    print()
    print("3. Manual test: curl -X POST 'http://localhost:8000/api/bodygraph' \\")
    print("     -d 'date=1990-01-15' -d 'time=09:13' -d 'location=Albuquerque, NM'")
    print()

    return strand


if __name__ == "__main__":
    try:
        strand = asyncio.run(execute_bodygraph_endpoint_strand())
    except KeyboardInterrupt:
        print("\n\n⚠️  Strand interrupted")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
