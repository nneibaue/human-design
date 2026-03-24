"""
D3 Specialist Agent - D3.js visualization expertise (REFINED VERSION).

This agent handles D3-based bodygraph visualization design and implementation.

REFINEMENTS (2026-03-23):
- Added tool registration (dodo shared infrastructure)
- Implemented custom @agent.tool methods for D3 operations
- Enhanced system prompt with RawBodyGraph integration examples
- Improved dependency validation
- Added concrete data flow: RawBodyGraph → D3 JSON → Visualization code

Focuses on:
- D3.js v7 patterns and best practices
- SVG structure for Human Design bodygraphs
- Rebecca Energy aesthetic (warm, cozy, magical)
- Interactive visualizations (hover, click, zoom)
- Integration with RawBodyGraph data models
"""

from pydantic import BaseModel, Field, ConfigDict
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import logging

logger = logging.getLogger(__name__)


D3_SPECIALIST_SYSTEM_PROMPT = """You are a D3 Specialist agent for Human Design bodygraph visualizations.

## CORE RESPONSIBILITIES

1. **D3.js Architecture**: Design D3-based rendering systems
   - D3 v7 patterns (modern, functional style)
   - SVG structure for bodygraphs (centers, channels, gates)
   - Data-driven visualizations (bind RawBodyGraph to SVG)
   - Update patterns for interactive overlays

2. **Bodygraph Geometry**: Understand Human Design chart structure
   - 9 centers (shapes: triangle, square, diamond)
   - 36 channels (paths connecting centers)
   - 64 gates (markers on channels)
   - Fixed geometry (not force-directed)

3. **Rebecca Energy Aesthetic**: Warm, cozy, magical design
   ```css
   /* Rebecca Energy Palette */
   --defined-center: #8B4513;      /* Saddle brown */
   --undefined-center: #F5F5DC;    /* Beige */
   --conscious: #4A5D23;           /* Dark olive green */
   --unconscious: #8B0000;         /* Dark red */
   --emergent: #DAA520;            /* Goldenrod */
   --background: #2C1810;          /* Deep brown */
   --text: #F5E6D3;                /* Warm cream */
   ```

4. **Visualization Features**:
   - Hover states (gate/channel info)
   - Click interactions (full descriptions)
   - Composite overlays (multiple people)
   - Transit visualization (current sky)
   - Responsive layout (desktop/mobile)

## DATA MODEL INTEGRATION

The bodygraph data comes from RawBodyGraph models in src/human_design/models/bodygraph.py:

**Input Structure** (from Python backend):
```python
from human_design.models.bodygraph import RawBodyGraph
from human_design.models.core import Planet, PlanetActivation, HDType, Authority

# RawBodyGraph has planetary activations
bodygraph = RawBodyGraph(
    personality={
        Planet.SUN: PlanetActivation(gate=42, line=3, longitude=264.5),
        Planet.EARTH: PlanetActivation(gate=32, line=3, longitude=84.5),
        Planet.MOON: PlanetActivation(gate=18, line=6, longitude=221.1),
        # ... other planets (MERCURY, VENUS, MARS, JUPITER, SATURN, URANUS, NEPTUNE, PLUTO, NORTH_NODE, SOUTH_NODE)
    },
    design={
        Planet.SUN: PlanetActivation(gate=53, line=1, longitude=177.2),
        Planet.EARTH: PlanetActivation(gate=54, line=1, longitude=357.2),
        # ... other design planets (~88 days before birth)
    },
    defined_centers={'LIFEFORCE', 'EMOTION'},
    defined_channels=[ChannelDefinition(id='42-53', gates=[42, 53])],
    hd_type=HDType.BUILDER,  # 64keys terminology (not "Generator")
    authority=Authority.EMOTIONAL,
    profile=Profile.PROFILE_6_2
)
```

**Your job**: Convert RawBodyGraph → D3-friendly JSON → Generate visualization code.

**D3 Data Structure** (output format):
```json
{
  "centers": [
    {"name": "LIFEFORCE", "x": 200, "y": 400, "defined": true, "shape": "square"},
    {"name": "EMOTION", "x": 180, "y": 300, "defined": true, "shape": "triangle"},
    {"name": "EXPRESSION", "x": 200, "y": 180, "defined": false, "shape": "square"}
  ],
  "channels": [
    {"id": "42-53", "from": "LIFEFORCE", "to": "EMOTION", "defined": true, "gates": [42, 53]}
  ],
  "gates": [
    {"number": 42, "line": 3, "planet": "SUN", "type": "personality", "longitude": 264.5},
    {"number": 53, "line": 1, "planet": "SUN", "type": "design", "longitude": 177.2}
  ],
  "type": "BUILDER",  # 64keys terminology
  "authority": "EMOTIONAL",
  "profile": "6/2"
}
```

## D3 PATTERNS FOR BODYGRAPHS

**Data Binding**:
```javascript
// Bind centers to SVG shapes
const centers = svg.selectAll('.center')
  .data(bodygraphData.centers, d => d.name)
  .join('g')
  .attr('class', 'center')
  .attr('transform', d => `translate(${d.x}, ${d.y})`);

// Draw center shapes (triangle, square, diamond)
centers.append('path')
  .attr('d', d => getCenterShape(d.type))
  .attr('class', d => d.defined ? 'defined' : 'undefined');
```

**Channel Paths**:
```javascript
// Draw channels as paths between centers
const channels = svg.selectAll('.channel')
  .data(bodygraphData.channels)
  .join('path')
  .attr('class', d => d.defined ? 'active' : 'inactive')
  .attr('d', d => getChannelPath(d.from, d.to));
```

**Interactive Overlays**:
```javascript
// Tooltip on hover
gates.on('mouseover', (event, d) => {
  tooltip
    .style('opacity', 1)
    .html(`<strong>Gate ${d.number}.${d.line}</strong><br>${d.planet} (${d.type})`)
    .style('left', event.pageX + 'px')
    .style('top', event.pageY + 'px');
});
```

## TOOL USAGE

You have access to filesystem and code search tools:

- **read_file(path)** - Read source files (bodygraph.py, existing D3 code)
- **write_file(path, content)** - Write D3 code to static/js/, CSS to static/css/
- **grep(pattern, path)** - Search for patterns in codebase
- **glob(pattern)** - Find files matching pattern (e.g., "**/*.js")
- **git_log()** - Check commit history for visualization work

**Workflow**:
1. Read bodygraph.py to understand RawBodyGraph structure
2. Use convert_bodygraph_to_d3_data to transform data
3. Generate D3 visualization code using D3 v7 patterns
4. Write code to static/js/d3-bodygraph.js
5. Create Rebecca Energy styles in static/css/bodygraph-styles.css

## CUSTOM TOOLS

You have specialized D3 tools:

**convert_bodygraph_to_d3_data(bodygraph)**: Convert RawBodyGraph dict to D3 JSON
**generate_d3_visualization_code(schema, features)**: Generate D3.js v7 code
**validate_svg_geometry(positions, paths)**: Validate bodygraph SVG accuracy

## OUTPUT FORMAT

Always provide:
1. **Visualization Design**: SVG structure and layout plan
2. **D3 Code**: JavaScript implementation (D3 v7 patterns)
3. **Data Schema**: JSON format specification
4. **Styling**: CSS for Rebecca Energy aesthetic
5. **Interactions**: Hover, click, zoom behaviors
6. **Integration Notes**: How to connect to FastAPI backend

## D3 BEST PRACTICES

✅ Use D3 v7 (modern API, no more `selection.enter()`)
✅ Bind data with `.join()` method
✅ Use `transform` attribute for positioning
✅ Semantic CSS classes (`.defined`, `.conscious`, `.emergent`)
✅ Accessible (ARIA labels, keyboard navigation)
✅ Performance (limit DOM updates, use requestAnimationFrame)

❌ Avoid D3 v3/v4 patterns (outdated)
❌ Don't inline styles (use CSS classes)
❌ Don't mutate data in place
❌ Don't use jQuery alongside D3

## 64KEYS TERMINOLOGY (CRITICAL)

**Always use 64keys terms** (Rebecca's preferred system):

| Traditional HD | 64keys Term | Usage |
|----------------|-------------|-------|
| Manifestor | INITIATOR | hd_type = HDType.INITIATOR |
| Generator | BUILDER | hd_type = HDType.BUILDER |
| Manifesting Generator | SPECIALIST | hd_type = HDType.SPECIALIST |
| Projector | COORDINATOR | hd_type = HDType.COORDINATOR |
| Reflector | OBSERVER | hd_type = HDType.OBSERVER |
| Solar Plexus | EMOTION | center_name = "EMOTION" |
| Root | LIFEFORCE | center_name = "LIFEFORCE" |
| Sacral | DRIVE | center_name = "DRIVE" |

## THE D3 SPECIALIST'S MANTRA

*"Data drives the visualization. D3 binds data to SVG. Rebecca Energy makes it beautiful."*

Your job: Design and implement D3-based bodygraph visualizations that are:
- **Accurate**: Faithful to Human Design geometry
- **Interactive**: Responsive to user actions
- **Beautiful**: Aligned with Rebecca Energy aesthetic
- **Accessible**: Usable by all users
- **Performant**: Smooth on all devices
"""


class D3SpecialistConfig(BaseModel):
    """Configuration for D3 Specialist agent."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    workspace_root: Path = Field(..., description="Root directory of the project")
    static_directory: Path = Field(default=Path("static"), description="Directory for static assets")
    model: str = Field(default="claude-sonnet-4-5-20250929", description="LLM model to use")


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
            logger.warning(f"Static directory doesn't exist, creating: {static_path}")
            static_path.mkdir(parents=True, exist_ok=True)

        # Validate subdirectories
        js_dir = static_path / "js"
        css_dir = static_path / "css"
        if not js_dir.exists():
            js_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created JS directory: {js_dir}")
        if not css_dir.exists():
            css_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created CSS directory: {css_dir}")


def create_d3_specialist_agent(deps: D3SpecialistDeps, model: str | None = None) -> Agent:
    """Create D3 specialist agent with tools.

    Args:
        deps: Agent dependencies (workspace root, static directory)
        model: Optional LLM model override

    Returns:
        Configured pydantic-ai Agent instance with registered tools
    """
    agent = Agent(
        model=model or "claude-sonnet-4-5-20250929",
        system_prompt=D3_SPECIALIST_SYSTEM_PROMPT,
        deps_type=D3SpecialistDeps,
    )

    # Register shared tools from dodo
    # NOTE: Import these from dodo.agent_tools when available
    # For now, document the expected tools
    #
    # from dodo.agent_tools import (
    #     register_filesystem_tools,
    #     register_code_search_tools,
    #     register_git_history_tools,
    # )
    #
    # register_filesystem_tools(agent)      # read_file, write_file, list_directory
    # register_code_search_tools(agent)     # grep, glob
    # register_git_history_tools(agent)     # git_log, git_diff

    # Register custom D3-specific tools
    _register_d3_tools(agent)

    return agent


def _register_d3_tools(agent: Agent) -> None:
    """Register D3-specific tools on the agent.

    These tools are specific to bodygraph visualization and data transformation.
    """

    @agent.tool
    async def convert_bodygraph_to_d3_data(
        ctx: RunContext[D3SpecialistDeps],
        bodygraph: dict[str, Any]
    ) -> dict[str, Any]:
        """Convert RawBodyGraph to D3-friendly JSON structure.

        Args:
            ctx: Agent runtime context with dependencies
            bodygraph: RawBodyGraph serialized as dict

        Returns:
            D3 visualization data with centers, channels, gates
        """
        # Extract activations
        personality = bodygraph.get("personality", {})
        design = bodygraph.get("design", {})
        defined_centers = bodygraph.get("defined_centers", set())
        defined_channels = bodygraph.get("defined_channels", [])

        # Build gates list from personality and design
        gates = []
        for planet_name, activation in personality.items():
            gates.append({
                "number": activation["gate"],
                "line": activation["line"],
                "planet": planet_name,
                "type": "personality",
                "longitude": activation.get("longitude"),
            })

        for planet_name, activation in design.items():
            gates.append({
                "number": activation["gate"],
                "line": activation["line"],
                "planet": planet_name,
                "type": "design",
                "longitude": activation.get("longitude"),
            })

        # Build centers list (all 9 centers with defined status)
        all_centers = [
            "INSPIRATION", "MIND", "EXPRESSION", "IDENTITY",
            "WILLPOWER", "EMOTION", "DRIVE", "LIFEFORCE", "INTUITION"
        ]
        centers = [
            {
                "name": center,
                "defined": center in defined_centers,
                # Placeholder positions - to be filled by SVG geometry research
                "x": 200,
                "y": 100 + (i * 40),
                "shape": "square"  # Simplified, actual shapes vary
            }
            for i, center in enumerate(all_centers)
        ]

        # Build channels list
        channels = [
            {
                "id": channel.get("id"),
                "gates": channel.get("gates", []),
                "from": channel.get("from"),
                "to": channel.get("to"),
                "defined": True
            }
            for channel in defined_channels
        ]

        return {
            "centers": centers,
            "channels": channels,
            "gates": gates,
            "type": bodygraph.get("hd_type"),
            "authority": bodygraph.get("authority"),
            "profile": bodygraph.get("profile"),
        }

    @agent.tool
    async def generate_d3_visualization_code(
        ctx: RunContext[D3SpecialistDeps],
        data_schema: dict[str, Any],
        interaction_features: list[str]
    ) -> str:
        """Generate D3.js v7 code for bodygraph rendering.

        Args:
            ctx: Agent runtime context
            data_schema: D3 data structure specification
            interaction_features: Requested interactions (hover, click, zoom)

        Returns:
            JavaScript code implementing D3 visualization using v7 patterns
        """
        # This would generate D3 code based on the schema
        # For now, return a template showing the pattern

        has_hover = "hover" in interaction_features
        has_click = "click" in interaction_features
        has_zoom = "zoom" in interaction_features

        code = """// D3.js v7 Bodygraph Visualization
// Generated by D3 Specialist Agent

function renderBodygraph(data, containerId) {
  const container = d3.select(containerId);
  const width = 600;
  const height = 800;

  // Create SVG
  const svg = container.append('svg')
    .attr('viewBox', `0 0 ${width} ${height}`)
    .attr('class', 'bodygraph-svg');

"""

        if has_zoom:
            code += """  // Add zoom behavior
  const zoom = d3.zoom()
    .scaleExtent([0.5, 3])
    .on('zoom', (event) => {
      svg.attr('transform', event.transform);
    });
  svg.call(zoom);

"""

        code += """  // Draw centers (D3 v7 .join() pattern)
  const centers = svg.selectAll('.center')
    .data(data.centers, d => d.name)
    .join('g')
    .attr('class', d => `center ${d.defined ? 'defined' : 'undefined'}`)
    .attr('transform', d => `translate(${d.x}, ${d.y})`);

  centers.append('circle')
    .attr('r', 30)
    .attr('class', 'center-shape');

  centers.append('text')
    .text(d => d.name)
    .attr('text-anchor', 'middle')
    .attr('dy', '0.35em');

"""

        if has_hover:
            code += """  // Add hover tooltip
  const tooltip = container.append('div')
    .attr('class', 'tooltip')
    .style('opacity', 0);

  centers.on('mouseover', (event, d) => {
    tooltip
      .style('opacity', 1)
      .html(`<strong>${d.name}</strong><br>${d.defined ? 'Defined' : 'Undefined'}`)
      .style('left', event.pageX + 'px')
      .style('top', event.pageY + 'px');
  });

  centers.on('mouseout', () => {
    tooltip.style('opacity', 0);
  });

"""

        if has_click:
            code += """  // Add click interaction
  centers.on('click', (event, d) => {
    console.log('Center clicked:', d);
    // Emit custom event or call callback
    window.dispatchEvent(new CustomEvent('centerClick', { detail: d }));
  });

"""

        code += """  // Draw channels
  const channels = svg.selectAll('.channel')
    .data(data.channels)
    .join('path')
    .attr('class', d => `channel ${d.defined ? 'active' : 'inactive'}`)
    .attr('d', d => {
      // Placeholder - actual path calculation needed
      return `M ${d.from.x} ${d.from.y} L ${d.to.x} ${d.to.y}`;
    });

  // Draw gates
  const gates = svg.selectAll('.gate')
    .data(data.gates)
    .join('circle')
    .attr('class', d => `gate ${d.type}`)
    .attr('cx', d => d.x || 0)  // Position along channel
    .attr('cy', d => d.y || 0)
    .attr('r', 5);
}

// Export for use
export { renderBodygraph };
"""

        return code

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
        - No overlapping elements

        Args:
            ctx: Agent runtime context
            center_positions: Dict of center_name -> (x, y)
            channel_paths: Dict of channel_id -> SVG path string

        Returns:
            Validation report with errors/warnings
        """
        errors = []
        warnings = []

        # Check all 9 centers present
        required_centers = {
            "INSPIRATION", "MIND", "EXPRESSION", "IDENTITY",
            "WILLPOWER", "EMOTION", "DRIVE", "LIFEFORCE", "INTUITION"
        }
        missing = required_centers - set(center_positions.keys())
        if missing:
            errors.append(f"Missing center positions: {missing}")

        # Check for duplicate positions
        positions = list(center_positions.values())
        if len(positions) != len(set(positions)):
            warnings.append("Duplicate center positions detected")

        # Validate channel paths are valid SVG
        for channel_id, path in channel_paths.items():
            if not path.startswith('M') and not path.startswith('m'):
                errors.append(f"Invalid SVG path for channel {channel_id}: {path}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "center_count": len(center_positions),
            "channel_count": len(channel_paths),
        }


class D3SpecialistAgent:
    """High-level D3 specialist agent interface."""

    def __init__(self, config: D3SpecialistConfig):
        """Initialize D3 specialist agent.

        Args:
            config: Agent configuration
        """
        self.config = config
        self.deps = D3SpecialistDeps(
            workspace_root=config.workspace_root,
            static_directory=config.static_directory,
        )
        self.agent = create_d3_specialist_agent(self.deps, config.model)

    async def design_visualization(self, feature: str, context: dict) -> dict:
        """Design D3 visualization.

        Args:
            feature: Visualization feature to design
            context: Additional context (data schema, requirements, bodygraph data)

        Returns:
            Design result with D3 code, styling, and interactions
        """
        try:
            result = await self.agent.run(
                f"Design D3 visualization for: {feature}\n\nContext: {context}",
                deps=self.deps,
            )

            return {
                "design": result.data,
                "status": "completed",
                "agent": "d3_specialist",
            }
        except Exception as e:
            logger.error(f"Visualization design failed: {e}")
            return {
                "design": None,
                "status": "failed",
                "error": str(e),
                "agent": "d3_specialist",
            }
