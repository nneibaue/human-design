# D3 Specialist Agent Refinement Analysis

**Date**: 2026-03-23
**Investigation Type**: Agent Refinement
**Target**: `src/human_design/agents/d3_specialist.py`

## Executive Summary

The d3_specialist agent has a solid foundation but lacks tool integration and practical implementation patterns. This analysis identifies key gaps and provides actionable refinements.

## Current State Analysis

### Strengths ✅

1. **Clear System Prompt**: Well-structured prompt with D3.js v7 patterns
2. **Rebecca Energy Defined**: Color palette and aesthetic guidelines documented
3. **Bodygraph Knowledge**: Understands 9 centers, 36 channels, 64 gates structure
4. **Pydantic v2 Compliant**: Uses proper ConfigDict and BaseModel patterns
5. **Architecture Aligned**: Follows pydantic-ai Agent patterns

### Gaps Identified ❌

1. **No Tool Registration**: `# TODO: Import from dodo.agent_tools when available`
2. **No Practical Examples**: System prompt has conceptual code, not real working examples
3. **Missing Data Flow**: No clear path from RawBodyGraph → SVG data → D3 rendering
4. **No Integration Guidance**: Unclear how agent connects to broader visualization system
5. **Incomplete Dependencies**: D3SpecialistDeps doesn't validate static_directory existence
6. **No Error Handling**: design_visualization() doesn't handle failures gracefully
7. **Missing Tool Methods**: No @agent.tool decorated methods for concrete operations

## Comparative Analysis

### Pattern: Python Linguist Agent (Good Example)

```python
# FROM: python_linguist.py
from dodo.agent_tools import (
    register_filesystem_tools,
    register_code_search_tools,
    FileSystemDeps,
    CodeSearchDeps,
)

# Agent creation with tool registration
agent = Agent(
    model=model or "claude-sonnet-4-5-20250929",
    system_prompt=PYTHON_LINGUIST_SYSTEM_PROMPT,
    deps_type=PythonLinguistDeps,
)
register_filesystem_tools(agent)  # ✅ Registers read_file, write_file, etc.
register_code_search_tools(agent)  # ✅ Registers grep, glob, etc.
```

**D3 Specialist Should Do Same**: Register dodo agent tools for file operations.

### Data Model: RawBodyGraph → D3 JSON

```python
# FROM: bodygraph.py
class RawBodyGraph(BaseModel):
    personality: dict[Planet, PlanetActivation]  # Conscious activations
    design: dict[Planet, PlanetActivation]       # Unconscious activations
    defined_centers: set[CenterName]
    defined_channels: list[ChannelDefinition]
    hd_type: HDType                              # BUILDER, INITIATOR, etc.
    authority: Authority
    profile: Profile
```

**D3 Specialist Needs**: Method to convert RawBodyGraph → D3-friendly JSON schema.

## Refined Architecture Recommendations

### 1. Tool Registration (CRITICAL)

```python
def create_d3_specialist_agent(deps: D3SpecialistDeps, model: str | None = None) -> Agent:
    """Create D3 specialist agent with tools."""
    agent = Agent(
        model=model or "claude-sonnet-4-5-20250929",
        system_prompt=D3_SPECIALIST_SYSTEM_PROMPT,
        deps_type=D3SpecialistDeps,
    )

    # Register shared tools from dodo
    register_filesystem_tools(agent)      # read_file, write_file, list_directory
    register_code_search_tools(agent)     # grep, glob
    register_git_history_tools(agent)     # git_log, git_diff

    return agent
```

### 2. Custom D3-Specific Tools

Add @agent.tool decorated methods for visualization operations:

```python
@agent.tool
async def convert_bodygraph_to_d3_data(
    ctx: RunContext[D3SpecialistDeps],
    bodygraph: dict[str, Any]
) -> dict[str, Any]:
    """Convert RawBodyGraph to D3-friendly JSON structure.

    Args:
        bodygraph: RawBodyGraph serialized as dict

    Returns:
        D3 visualization data with centers, channels, gates
    """
    # Extract activations
    personality = bodygraph.get("personality", {})
    design = bodygraph.get("design", {})

    # Build D3 data structure
    return {
        "centers": _extract_centers(bodygraph),
        "channels": _extract_channels(bodygraph),
        "gates": _extract_gates(personality, design),
        "type": bodygraph.get("hd_type"),
        "authority": bodygraph.get("authority"),
    }

@agent.tool
async def generate_d3_visualization_code(
    ctx: RunContext[D3SpecialistDeps],
    data_schema: dict[str, Any],
    interaction_features: list[str]
) -> str:
    """Generate D3.js v7 code for bodygraph rendering.

    Args:
        data_schema: D3 data structure specification
        interaction_features: Requested interactions (hover, click, zoom)

    Returns:
        JavaScript code implementing D3 visualization
    """
    # Template-based D3 code generation
    # Uses modern D3 v7 patterns: .join(), data binding, etc.
    pass

@agent.tool
async def validate_svg_geometry(
    ctx: RunContext[D3SpecialistDeps],
    center_positions: dict[str, tuple[float, float]],
    channel_paths: dict[str, str]
) -> dict[str, Any]:
    """Validate bodygraph SVG geometry for accuracy.

    Checks:
    - All 9 centers have positions
    - Channel paths connect correct centers
    - Gate positions align with channels

    Returns:
        Validation report with errors/warnings
    """
    pass
```

### 3. Enhanced System Prompt

Add concrete working examples from actual codebase:

```python
D3_SPECIALIST_SYSTEM_PROMPT = """You are a D3 Specialist agent for Human Design bodygraph visualizations.

## DATA MODEL INTEGRATION

The bodygraph data comes from RawBodyGraph models in src/human_design/models/bodygraph.py:

**Input Structure** (from Python backend):
```python
# RawBodyGraph has planetary activations
bodygraph = RawBodyGraph(
    personality={
        Planet.SUN: PlanetActivation(gate=42, line=3, longitude=264.5),
        Planet.EARTH: PlanetActivation(gate=32, line=3, longitude=84.5),
        # ... other planets
    },
    design={
        Planet.SUN: PlanetActivation(gate=53, line=1, longitude=177.2),
        # ... other planets
    },
    defined_centers={'LIFEFORCE', 'EMOTION'},
    defined_channels=[ChannelDefinition(id='42-53', gates=[42, 53])],
    hd_type=HDType.BUILDER,
    authority=Authority.EMOTIONAL,
    profile=Profile.PROFILE_6_2
)
```

**Your job**: Convert this to D3-friendly JSON and generate visualization code.

**Output Format** (D3 data structure):
```json
{
  "centers": [
    {"name": "LIFEFORCE", "x": 200, "y": 400, "defined": true, "shape": "square"},
    {"name": "EMOTION", "x": 180, "y": 300, "defined": true, "shape": "triangle"}
  ],
  "channels": [
    {"id": "42-53", "from": "LIFEFORCE", "to": "EMOTION", "defined": true}
  ],
  "gates": [
    {"number": 42, "line": 3, "planet": "SUN", "type": "personality"},
    {"number": 53, "line": 1, "planet": "SUN", "type": "design"}
  ],
  "type": "BUILDER",
  "authority": "EMOTIONAL",
  "profile": "6/2"
}
```

## TOOL USAGE

You have access to filesystem and code search tools via dodo shared infrastructure:

- **read_file(path)** - Read source files
- **write_file(path, content)** - Write D3 code to static/js/
- **grep(pattern, path)** - Search for patterns
- **glob(pattern)** - Find files matching pattern
- **git_log()** - Check commit history

**Example workflow**:
1. Read existing bodygraph.py to understand data model
2. Generate D3 code using convert_bodygraph_to_d3_data tool
3. Write D3 visualization code to static/js/d3-bodygraph.js
4. Create CSS styles in static/css/bodygraph-styles.css

... [rest of refined prompt]
"""
```

### 4. Improved Dependency Validation

```python
@dataclass
class D3SpecialistDeps:
    """D3 Specialist agent dependencies."""
    workspace_root: Path
    static_directory: Path

    def __post_init__(self):
        """Validate D3 specialist dependencies."""
        if not self.workspace_root.exists():
            raise ValueError(f"Workspace root does not exist: {self.workspace_root}")

        if not self.workspace_root.is_dir():
            raise ValueError(f"Workspace root is not a directory: {self.workspace_root}")

        # Create static directory if it doesn't exist (don't fail)
        static_path = self.workspace_root / self.static_directory
        if not static_path.exists():
            logger.warning(f"Static directory doesn't exist, will create: {static_path}")
            static_path.mkdir(parents=True, exist_ok=True)
```

## Implementation Priority

### HIGH Priority (Week 1)
1. ✅ Add tool registration (register_filesystem_tools, register_code_search_tools)
2. ✅ Implement convert_bodygraph_to_d3_data @agent.tool method
3. ✅ Update system prompt with concrete RawBodyGraph examples
4. ✅ Improve D3SpecialistDeps validation

### MEDIUM Priority (Week 2)
5. ⏳ Implement generate_d3_visualization_code @agent.tool method
6. ⏳ Add validate_svg_geometry @agent.tool method
7. ⏳ Create integration tests with RawBodyGraph fixtures
8. ⏳ Document agent usage patterns in README

### LOW Priority (Week 3+)
9. ⏳ Add error handling and retry logic to design_visualization()
10. ⏳ Create example notebooks demonstrating agent usage
11. ⏳ Performance optimization for large composite charts

## Integration Points

### With Existing Codebase

1. **bodygraph.py** → Provides RawBodyGraph data model
2. **calculate_utils.py** → Geocoding and ephemeris calculations
3. **64keys API (api.py)** → Fetch semantic overlays (optional)
4. **Web layer (web/app.py)** → FastAPI routes calling agent

### Future Enhancements

1. **Composite visualization** → Multi-person overlays (family penta, relationship)
2. **Transit overlay** → Current sky activations on bodygraph
3. **Animation** → D3 transitions for dynamic charts
4. **Accessibility** → ARIA labels, keyboard navigation
5. **Export** → SVG download, PNG rendering via canvas

## Testing Strategy

### Unit Tests
```python
def test_convert_bodygraph_to_d3_data():
    """Test bodygraph → D3 JSON conversion."""
    bodygraph = create_test_bodygraph()
    d3_data = convert_bodygraph_to_d3_data(bodygraph.dict())

    assert len(d3_data["centers"]) == 9
    assert len(d3_data["gates"]) > 0
    assert d3_data["type"] == "BUILDER"

def test_generate_d3_code():
    """Test D3 code generation from schema."""
    schema = {"centers": [...], "channels": [...]}
    code = generate_d3_visualization_code(schema, ["hover", "click"])

    assert "d3.select" in code
    assert "join(" in code  # D3 v7 pattern
    assert ".on('mouseover'" in code  # Hover interaction
```

### Integration Tests
```python
async def test_agent_end_to_end():
    """Test complete agent workflow."""
    agent = create_d3_specialist_agent(deps)

    result = await agent.design_visualization(
        feature="bodygraph_with_hover",
        context={"bodygraph": test_bodygraph.dict()}
    )

    assert result["status"] == "completed"
    assert "d3_code" in result["design"]
    assert "css_styles" in result["design"]
```

## Ontological Alignment

### 64keys Terminology ✅
- Uses BUILDER (not Generator)
- Uses EMOTION (not Solar Plexus)
- Uses LIFEFORCE (not Root)

### Rebecca Energy ✅
- Warm color palette (#8B4513, #F5E6D3, etc.)
- Cozy, magical aesthetic
- Not clinical or technical feeling

### Tropical Zodiac ✅
- Calculations use seasons-based zodiac
- Documented in bodygraph.yaml

## Conclusion

The d3_specialist agent needs **tool registration** and **practical integration** to be production-ready. The refined implementation should:

1. Register dodo shared tools (filesystem, code search)
2. Add custom @agent.tool methods for D3-specific operations
3. Update system prompt with concrete RawBodyGraph examples
4. Improve dependency validation and error handling

**Estimated effort**: 1-2 days for HIGH priority items, 3-5 days for complete refinement.

**Next Steps**: Implement refined d3_specialist.py following patterns from python_linguist.py.
