#!/usr/bin/env python3
"""Execute bodygraph endpoint implementation strand using DODO-Lite.

This strand composes three agents:
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
    """Execute the bodygraph endpoint implementation strand."""

    print("=" * 80)
    print("🎨 BODYGRAPH ENDPOINT IMPLEMENTATION STRAND")
    print("=" * 80)
    print("Goal: Build /api/bodygraph endpoint with D3 visualization")
    print("Agents: implementer → d3_specialist → test_engineer")
    print("Timeline: 24-30 minutes")
    print("=" * 80)
    print()

    # Build comprehensive context for agents
    context = {
        "existing_models": {
            "RawBodyGraph": "src/human_design/models/bodygraph.py",
            "BirthInfo": "src/human_design/models/bodygraph.py",
            "LocalTime": "src/human_design/models/coordinates.py",
        },
        "existing_api": {
            "app": "src/human_design/web/app.py",
            "operations": "src/human_design/api/operations.py",
        },
        "visualization_requirements": {
            "framework": "D3.js v7",
            "format": "SVG",
            "aesthetic": "Rebecca Energy (warm, cozy, magical)",
            "colors": {
                "defined_center": "#8B4513",  # Saddle brown
                "undefined_center": "#F5F5DC",  # Beige
                "conscious": "#4A5D23",  # Dark olive green
                "unconscious": "#8B0000",  # Dark red
                "emergent": "#DAA520",  # Goldenrod
                "background": "#2C1810",  # Deep brown
                "text": "#F5E6D3",  # Warm cream
            },
            "interactivity": ["hover tooltips", "click for details", "responsive layout"],
        },
        "bodygraph_geometry": {
            "centers": 9,
            "channels": 36,
            "gates": 64,
            "structure": "Fixed geometry (not force-directed)",
            "shapes": {
                "LIFEFORCE": "square",
                "EMOTION": "triangle",
                "INTUITION": "triangle",
                "IDENTITY": "diamond",
                "WILLPOWER": "triangle",
                "DRIVE": "square",
                "EXPRESSION": "square",
                "MIND": "triangle",
                "INSPIRATION": "triangle",
            },
        },
        "test_requirements": [
            "Endpoint returns 200 with valid birth info",
            "Response contains centers, channels, gates arrays",
            "Invalid birth info returns 400 with helpful error",
            "Geocoding failure handled gracefully",
            "Response schema validates against expected format",
            "D3 data format matches visualization expectations",
        ],
        "expected_deliverables": {
            "endpoint": "src/human_design/web/app.py (@app.post('/api/bodygraph'))",
            "renderer": "src/human_design/api/bodygraph_renderer.py (BodygraphRenderer class)",
            "d3_code": "src/human_design/web/static/js/d3-bodygraph.js",
            "d3_css": "src/human_design/web/static/css/bodygraph.css",
            "tests": "tests/test_bodygraph_endpoint.py",
            "demo": "src/human_design/web/templates/bodygraph.html (optional)",
        },
        "response_schema": {
            "birth_info": {
                "date": "YYYY-MM-DD",
                "time": "HH:MM",
                "location": "City, State/Country",
                "timezone": "America/Denver",
            },
            "bodygraph": {
                "centers": [
                    {
                        "name": "CenterName",
                        "defined": "boolean",
                        "x": "number",
                        "y": "number",
                        "shape": "string",
                    }
                ],
                "channels": [
                    {
                        "id": "42-53",
                        "gate_a": "number",
                        "gate_b": "number",
                        "defined": "boolean",
                        "from_center": "CenterName",
                        "to_center": "CenterName",
                    }
                ],
                "gates": [
                    {
                        "number": "number",
                        "line": "number",
                        "center": "CenterName",
                        "planet": "PlanetName",
                        "activation": "conscious|unconscious",
                    }
                ],
                "type": "string",
                "authority": "string",
                "profile": "string",
            },
        },
    }

    problem = """Build a bodygraph calculation and visualization endpoint at /api/bodygraph that:
1. Accepts birth information (date, time, location)
2. Calculates RawBodyGraph using existing models
3. Transforms bodygraph data to D3-friendly JSON format
4. Returns structured response for frontend rendering
5. Includes D3.js v7 code for interactive SVG visualization
6. Applies Rebecca Energy aesthetic (warm, cozy, magical)
7. Has comprehensive test coverage

CRITICAL REQUIREMENTS:
- Use existing RawBodyGraph models (don't recreate calculation logic)
- Create BodygraphRenderer class for data transformation
- D3.js v7 (modern API with .join() method)
- Rebecca Energy color palette (warm browns, golds, greens)
- Interactive hover tooltips and click behaviors
- Comprehensive test suite (happy path + edge cases)
- Fixed bodygraph geometry (not force-directed layout)

OUTPUT FILES:
1. src/human_design/web/app.py - Add @app.post('/api/bodygraph') endpoint
2. src/human_design/api/bodygraph_renderer.py - NEW BodygraphRenderer class
3. src/human_design/web/static/js/d3-bodygraph.js - NEW D3 visualization
4. src/human_design/web/static/css/bodygraph.css - NEW Rebecca Energy styling
5. tests/test_bodygraph_endpoint.py - NEW test suite
6. src/human_design/web/templates/bodygraph.html - NEW demo page (optional)
"""

    print("Creating strand with 3 agents...")
    strand = create_strand(
        problem=problem,
        agents=["implementer", "d3_specialist", "test_engineer"],
        strand_type="implementation",
        context=context,
    )

    print(f"✓ Strand ID: {strand.definition.strand_id}")
    print(f"✓ Agents: {', '.join(strand.definition.agents)}")
    print()
    print("▶️  Executing strand...")
    print()
    print("Phase 1: implementer - FastAPI endpoint + data transformation (8-10 min)")
    print("Phase 2: d3_specialist - D3 visualization + Rebecca Energy styling (10-12 min)")
    print("Phase 3: test_engineer - Comprehensive test suite (6-8 min)")
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
            print(f"\n{agent_name}:")
            if isinstance(finding, dict):
                print(json.dumps(finding, indent=2))
            else:
                print(f"  {finding}")

    print()
    print("🔍 VERIFICATION STEPS:")
    print("1. Run tests: pytest tests/test_bodygraph_endpoint.py -v")
    print("2. Manual test: curl -X POST 'http://localhost:8000/api/bodygraph' \\")
    print("     -d 'date=1990-01-15' -d 'time=09:13' -d 'location=Albuquerque, NM'")
    print("3. Open src/human_design/web/templates/bodygraph.html in browser")
    print("4. Verify Rebecca Energy aesthetic (warm browns, golds, greens)")
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
