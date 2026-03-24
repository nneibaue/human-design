# Bodygraph Visualization Implementation Guide

**Related ADR:** [ADR-002: Bodygraph Visualization Architecture](./ADR-002-bodygraph-visualization-architecture.md)

## Overview

This guide provides concrete implementation steps for building accurate Human Design bodygraph visualizations using the architecture defined in ADR-002.

## Phase 1: Research - Reverse Engineering 64keys.com

### Objective
Extract accurate geometric coordinates for centers, gates, and channel paths from 64keys.com's rendering system.

### Research Checklist

#### 1. Inspect 64keys Chart Page
```
URL: https://www.64keys.com/chart?id={person_id}
Tools: Chrome DevTools (Elements, Network, Console)
```

**Questions to answer:**
- [ ] What rendering technology? (SVG, Canvas, Image)
- [ ] Center positions (x, y coordinates for all 9 centers)
- [ ] Channel path definitions (SVG path strings or coordinate lists)
- [ ] Gate positions relative to centers
- [ ] SVG viewBox dimensions

#### 2. Extract SVG Structure (if SVG-based)

**Steps:**
1. Right-click bodygraph → Inspect Element
2. Locate `<svg>` root element
3. Copy `viewBox` attribute: `<svg viewBox="x y width height">`
4. Find center elements (likely `<circle>`, `<polygon>`, or `<path>`)
5. Record center positions:

```python
# Expected output format
CENTER_POSITIONS = {
    "INSPIRATION": (x, y),    # Head/Crown
    "MIND": (x, y),            # Ajna/Third Eye
    "EXPRESSION": (x, y),      # Throat
    "IDENTITY": (x, y),        # G-Center/Self
    "WILLPOWER": (x, y),       # Ego/Heart
    "EMOTION": (x, y),         # Solar Plexus
    "DRIVE": (x, y),           # Sacral
    "LIFEFORCE": (x, y),       # Root
    "INTUITION": (x, y),       # Spleen
}
```

6. Find channel paths (likely `<path d="...">`):

```python
# Example channel path extraction
CHANNEL_PATHS = {
    1: "M x1,y1 L x2,y2",  # Channel 1-8 (IDENTITY-EXPRESSION)
    2: "M x1,y1 C cx1,cy1 cx2,cy2 x2,y2",  # Curved path example
    # ... all 36 channels
}
```

#### 3. Alternative: Canvas/Image Analysis

If 64keys uses Canvas or pre-rendered images:

1. Take high-resolution screenshot of bodygraph
2. Load in image editor (Photoshop, GIMP)
3. Measure pixel coordinates of centers
4. Convert to relative coordinates (percentage of total width/height)
5. Trace channel paths manually

**Tools:**
- ImageMagick: `convert bodygraph.png -resize 1000x1000 bodygraph_large.png`
- GIMP: Use ruler tool to measure distances
- Online SVG editor: Recreate paths by hand if needed

#### 4. Validate Accuracy

**Test cases:**
- Known chart (e.g., Ra Uru Hu's chart - public figure in HD)
- Compare our rendering to 64keys screenshot
- Measure visual differences (should be < 5px variance)

### Deliverable: Geometry Constants File

```python
# src/human_design/visualization/geometry.py
"""
Bodygraph geometry constants extracted from 64keys.com.

Coordinates are in SVG coordinate space (viewBox: 0 0 800 1000).
Origin (0,0) is top-left corner.

Reference: 64keys.com chart rendering (inspected 2025-01-30)
"""

from typing import Final

# SVG Canvas dimensions
VIEWBOX: Final[tuple[float, float, float, float]] = (0, 0, 800, 1000)
WIDTH: Final[float] = 800
HEIGHT: Final[float] = 1000

# Center positions (x, y) in SVG coordinates
CENTER_POSITIONS: Final[dict[str, tuple[float, float]]] = {
    "INSPIRATION": (400, 100),   # Head - top center
    "MIND": (400, 200),           # Ajna - below head
    "EXPRESSION": (400, 350),     # Throat - neck area
    "IDENTITY": (400, 500),       # G-Center - heart area
    "WILLPOWER": (300, 500),      # Ego - right of G
    "EMOTION": (500, 650),        # Solar Plexus - below G, left
    "DRIVE": (400, 750),          # Sacral - lower abdomen
    "LIFEFORCE": (400, 900),      # Root - base
    "INTUITION": (300, 650),      # Spleen - below ego, right
}

# Center shapes (for rendering)
CENTER_SHAPES: Final[dict[str, str]] = {
    "INSPIRATION": "triangle",
    "MIND": "triangle",
    "EXPRESSION": "square",
    "IDENTITY": "diamond",
    "WILLPOWER": "triangle",
    "EMOTION": "square",
    "DRIVE": "square",
    "LIFEFORCE": "square",
    "INTUITION": "triangle",
}

# Channel paths (SVG path strings connecting center pairs)
# Format: "M x1,y1 L x2,y2" (straight) or "M x1,y1 C cx1,cy1 cx2,cy2 x2,y2" (curved)
CHANNEL_PATHS: Final[dict[int, str]] = {
    # Channel ID: SVG path
    1: "M 400,100 L 400,200",     # 64-47: INSPIRATION-MIND
    2: "M 400,200 L 400,350",     # 4-63: MIND-EXPRESSION
    # ... (populate all 36 channels)
}

# Gate positions on channels (percentage along channel path, 0.0-1.0)
GATE_POSITIONS: Final[dict[int, float]] = {
    # Gate number: position on channel (0.0 = center A, 1.0 = center B)
    1: 0.8,   # Gate 1 is 80% along channel from IDENTITY toward EXPRESSION
    8: 0.2,   # Gate 8 is 20% along same channel
    # ... (populate all 64 gates)
}
```

**NOTE:** Numbers above are PLACEHOLDERS. Phase 1 research must fill in real values.

---

## Phase 2: Backend Visualization API

### Step 1: Create Visualization Models

```python
# src/human_design/visualization/models.py
"""
Pydantic models for bodygraph visualization data.

These models transform calculation results (RawBodyGraph, CompositeBodyGraph)
into frontend-ready rendering instructions.
"""

from typing import Literal
from pydantic import BaseModel, Field

from ..models.core import CenterName, GateNumber

class CenterVisualization(BaseModel):
    """Visual representation of a center in the bodygraph."""
    
    name: CenterName
    position: tuple[float, float] = Field(
        ...,
        description="(x, y) SVG coordinates"
    )
    is_defined: bool = Field(
        ...,
        description="True if center has active channel(s)"
    )
    shape: Literal["triangle", "square", "diamond"] = Field(
        ...,
        description="SVG shape to render"
    )
    fill_color: str = Field(
        ...,
        description="Hex color for center fill"
    )
    stroke_color: str = Field(
        default="#000000",
        description="Hex color for center border"
    )
    size: float = Field(
        default=60.0,
        description="Rendering size in SVG units"
    )

class ChannelVisualization(BaseModel):
    """Visual representation of a channel connection."""
    
    channel_id: int = Field(
        ...,
        ge=1,
        le=36,
        description="Channel number (1-36)"
    )
    gate_a: GateNumber
    gate_b: GateNumber
    path: str = Field(
        ...,
        description="SVG path string (e.g., 'M 100,200 L 300,400')"
    )
    is_active: bool = Field(
        ...,
        description="True if both gates are activated"
    )
    activation_type: Literal["individual", "emergent", "none"] = Field(
        default="none",
        description="How this channel is activated in composite charts"
    )
    stroke_color: str = Field(
        ...,
        description="Hex color for channel line"
    )
    stroke_width: float = Field(
        default=3.0,
        description="Line thickness in SVG units"
    )
    opacity: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Opacity (0.0-1.0)"
    )

class ActivationVisualization(BaseModel):
    """Visual representation of a planetary gate activation."""
    
    gate: GateNumber
    planet: str = Field(
        ...,
        description="Planet name (SUN, MOON, MERCURY, etc.)"
    )
    is_conscious: bool = Field(
        ...,
        description="True = personality/conscious, False = design/unconscious"
    )
    position: tuple[float, float] = Field(
        ...,
        description="(x, y) position on channel for rendering icon"
    )
    color: str = Field(
        ...,
        description="Hex color (conscious vs unconscious)"
    )
    label: str = Field(
        ...,
        description="Display text (e.g., '☉ 4.3' for Sun Gate 4 Line 3)"
    )

class CompositeLayer(BaseModel):
    """Layer for composite chart rendering (individual vs emergent)."""
    
    layer_type: Literal["individual", "composite", "emergent"] = Field(
        ...,
        description="Type of channels in this layer"
    )
    channels: list[ChannelVisualization] = Field(
        default_factory=list,
        description="Channels belonging to this layer"
    )
    opacity: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Layer opacity for visual separation"
    )
    label: str = Field(
        ...,
        description="Human-readable layer name"
    )

class BodygraphVisualizationSchema(BaseModel):
    """
    Complete visualization schema for frontend rendering.
    
    This is the JSON payload sent to D3.js renderer.
    """
    
    centers: list[CenterVisualization] = Field(
        ...,
        description="All 9 centers with visual properties"
    )
    channels: list[ChannelVisualization] = Field(
        ...,
        description="All 36 channels with activation states"
    )
    activations: list[ActivationVisualization] = Field(
        default_factory=list,
        description="Planetary activations on gates"
    )
    composite_layers: list[CompositeLayer] | None = Field(
        default=None,
        description="Layers for composite charts (null for individuals)"
    )
    svg_viewbox: tuple[float, float, float, float] = Field(
        ...,
        description="SVG viewBox (x, y, width, height)"
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Additional chart metadata (person name, date, etc.)"
    )
```

### Step 2: Create Visualization Builder

```python
# src/human_design/visualization/builder.py
"""
Build BodygraphVisualizationSchema from calculation models.

Transforms RawBodyGraph/CompositeBodyGraph into frontend-ready JSON.
"""

from ..models.bodygraph import RawBodyGraph
from ..models.composite import CompositeBodyGraph
from ..models.channel import ChannelRegistry
from .geometry import CENTER_POSITIONS, CENTER_SHAPES, CHANNEL_PATHS, VIEWBOX
from .models import (
    BodygraphVisualizationSchema,
    CenterVisualization,
    ChannelVisualization,
    ActivationVisualization,
    CompositeLayer,
)
from .theme import REBECCA_PALETTE

class BodygraphVisualizationBuilder:
    """
    Builder for creating visualization schemas from bodygraph models.
    
    Usage:
        builder = BodygraphVisualizationBuilder()
        viz = builder.build_individual(raw_bodygraph)
        viz = builder.build_composite(composite_bodygraph)
    """
    
    def __init__(self):
        self.channel_registry = ChannelRegistry.load()
    
    def build_individual(
        self,
        bodygraph: RawBodyGraph
    ) -> BodygraphVisualizationSchema:
        """
        Build visualization for an individual bodygraph.
        
        Args:
            bodygraph: Calculated RawBodyGraph
            
        Returns:
            Complete visualization schema
        """
        centers = self._build_centers(bodygraph)
        channels = self._build_channels(bodygraph)
        activations = self._build_activations(bodygraph)
        
        return BodygraphVisualizationSchema(
            centers=centers,
            channels=channels,
            activations=activations,
            composite_layers=None,  # No layers for individual
            svg_viewbox=VIEWBOX,
            metadata={
                "person": f"{bodygraph.birth_info.city}, {bodygraph.birth_info.country}",
                "date": bodygraph.birth_info.date,
            }
        )
    
    def build_composite(
        self,
        composite: CompositeBodyGraph
    ) -> BodygraphVisualizationSchema:
        """
        Build visualization for a composite bodygraph.
        
        Shows individual + emergent channels in separate layers.
        
        Args:
            composite: Calculated CompositeBodyGraph
            
        Returns:
            Visualization with composite layers
        """
        centers = self._build_centers_composite(composite)
        
        # Build layers
        individual_channels = self._get_individual_channels(composite)
        emergent_channels_list = composite.emergent_channels()
        
        layers = [
            CompositeLayer(
                layer_type="individual",
                channels=individual_channels,
                opacity=0.6,
                label="Individual Channels"
            ),
            CompositeLayer(
                layer_type="emergent",
                channels=[
                    self._channel_to_visualization(ch, "emergent")
                    for ch in emergent_channels_list
                ],
                opacity=1.0,
                label="Emergent Channels"
            )
        ]
        
        # All channels combined (for main view)
        all_channels = self._build_channels_composite(composite)
        
        # Activations from all charts
        activations = []
        for chart in composite.charts:
            activations.extend(self._build_activations(chart))
        
        return BodygraphVisualizationSchema(
            centers=centers,
            channels=all_channels,
            activations=activations,
            composite_layers=layers,
            svg_viewbox=VIEWBOX,
            metadata={
                "chart_type": "composite",
                "person_count": len(composite.charts),
            }
        )
    
    def _build_centers(
        self,
        bodygraph: RawBodyGraph | CompositeBodyGraph
    ) -> list[CenterVisualization]:
        """Build center visualizations with definition states."""
        centers = []
        defined_centers = bodygraph.defined_centers
        
        for center_name, position in CENTER_POSITIONS.items():
            is_defined = center_name in defined_centers
            centers.append(
                CenterVisualization(
                    name=center_name,  # type: ignore
                    position=position,
                    is_defined=is_defined,
                    shape=CENTER_SHAPES[center_name],  # type: ignore
                    fill_color=REBECCA_PALETTE["defined_center"] if is_defined 
                               else REBECCA_PALETTE["undefined_center"],
                    stroke_color="#8B4513",  # Earthy brown border
                    size=60.0,
                )
            )
        
        return centers
    
    _build_centers_composite = _build_centers  # Same logic for composite
    
    def _build_channels(
        self,
        bodygraph: RawBodyGraph
    ) -> list[ChannelVisualization]:
        """Build channel visualizations for individual chart."""
        channels = []
        active_channels = bodygraph.active_channels
        active_channel_ids = {ch.channel_id for ch in active_channels}
        
        for channel_def in self.channel_registry.all_channels:
            is_active = channel_def.channel_id in active_channel_ids
            channels.append(
                ChannelVisualization(
                    channel_id=channel_def.channel_id,
                    gate_a=channel_def.gate_a,
                    gate_b=channel_def.gate_b,
                    path=CHANNEL_PATHS[channel_def.channel_id],
                    is_active=is_active,
                    activation_type="individual" if is_active else "none",
                    stroke_color=REBECCA_PALETTE["active_channel"] if is_active
                                 else REBECCA_PALETTE["inactive_channel"],
                    stroke_width=4.0 if is_active else 1.0,
                    opacity=1.0 if is_active else 0.3,
                )
            )
        
        return channels
    
    def _build_channels_composite(
        self,
        composite: CompositeBodyGraph
    ) -> list[ChannelVisualization]:
        """Build channels for composite, marking emergent ones."""
        channels = []
        active_channels = composite.active_channels
        emergent_channels = composite.emergent_channels()
        
        emergent_ids = {ch.channel_id for ch in emergent_channels}
        active_ids = {ch.channel_id for ch in active_channels}
        
        for channel_def in self.channel_registry.all_channels:
            is_emergent = channel_def.channel_id in emergent_ids
            is_active = channel_def.channel_id in active_ids
            
            if is_emergent:
                activation_type = "emergent"
                color = REBECCA_PALETTE["emergent_channel"]
            elif is_active:
                activation_type = "individual"
                color = REBECCA_PALETTE["active_channel"]
            else:
                activation_type = "none"
                color = REBECCA_PALETTE["inactive_channel"]
            
            channels.append(
                ChannelVisualization(
                    channel_id=channel_def.channel_id,
                    gate_a=channel_def.gate_a,
                    gate_b=channel_def.gate_b,
                    path=CHANNEL_PATHS[channel_def.channel_id],
                    is_active=is_active,
                    activation_type=activation_type,
                    stroke_color=color,
                    stroke_width=5.0 if is_emergent else 4.0 if is_active else 1.0,
                    opacity=1.0 if is_emergent else 0.8 if is_active else 0.3,
                )
            )
        
        return channels
    
    def _build_activations(
        self,
        bodygraph: RawBodyGraph
    ) -> list[ActivationVisualization]:
        """Build activation visualizations for planetary gates."""
        activations = []
        
        # Conscious activations
        for act in bodygraph.conscious_activations:
            pos = self._get_gate_position(act.gate)
            activations.append(
                ActivationVisualization(
                    gate=act.gate,
                    planet=act.planet.name,
                    is_conscious=True,
                    position=pos,
                    color=REBECCA_PALETTE["conscious"],
                    label=f"{self._planet_symbol(act.planet.name)} {act.gate_line}"
                )
            )
        
        # Unconscious activations
        for act in bodygraph.unconscious_activations:
            pos = self._get_gate_position(act.gate)
            activations.append(
                ActivationVisualization(
                    gate=act.gate,
                    planet=act.planet.name,
                    is_conscious=False,
                    position=pos,
                    color=REBECCA_PALETTE["unconscious"],
                    label=f"{self._planet_symbol(act.planet.name)} {act.gate_line}"
                )
            )
        
        return activations
    
    def _get_gate_position(self, gate: int) -> tuple[float, float]:
        """
        Calculate SVG position for a gate on its channel.
        
        TODO: Implement using GATE_POSITIONS from geometry.py
        """
        # Placeholder - calculate from channel path + gate position
        return (0.0, 0.0)
    
    def _planet_symbol(self, planet_name: str) -> str:
        """Get Unicode symbol for planet."""
        symbols = {
            "SUN": "☉",
            "EARTH": "🜨",
            "MOON": "☽",
            "MERCURY": "☿",
            "VENUS": "♀",
            "MARS": "♂",
            "JUPITER": "♃",
            "SATURN": "♄",
            "URANUS": "♅",
            "NEPTUNE": "♆",
            "PLUTO": "♇",
            "NORTH_NODE": "☊",
            "SOUTH_NODE": "☋",
        }
        return symbols.get(planet_name, "")
    
    def _get_individual_channels(
        self,
        composite: CompositeBodyGraph
    ) -> list[ChannelVisualization]:
        """Get channels that exist in individual charts (not emergent)."""
        emergent = set(ch.channel_id for ch in composite.emergent_channels())
        active = set(ch.channel_id for ch in composite.active_channels)
        individual_ids = active - emergent
        
        return [
            self._channel_to_visualization(ch, "individual")
            for ch in composite.active_channels
            if ch.channel_id in individual_ids
        ]
    
    def _channel_to_visualization(
        self,
        channel_def,
        activation_type: str
    ) -> ChannelVisualization:
        """Convert ChannelDefinition to visualization."""
        color_map = {
            "individual": REBECCA_PALETTE["active_channel"],
            "emergent": REBECCA_PALETTE["emergent_channel"],
        }
        
        return ChannelVisualization(
            channel_id=channel_def.channel_id,
            gate_a=channel_def.gate_a,
            gate_b=channel_def.gate_b,
            path=CHANNEL_PATHS[channel_def.channel_id],
            is_active=True,
            activation_type=activation_type,  # type: ignore
            stroke_color=color_map[activation_type],
            stroke_width=4.0,
            opacity=1.0,
        )
```

### Step 3: Create Theme Module

```python
# src/human_design/visualization/theme.py
"""
Rebecca Energy aesthetic theme for bodygraph visualizations.

Color palette: Cozy autumnal forest, twilight magic.
Mood: Warm, inviting, mystical (NOT clinical).
"""

from typing import Final

REBECCA_PALETTE: Final[dict[str, str]] = {
    # Centers
    "defined_center": "#8B4513",      # Saddle brown - earthy grounding
    "undefined_center": "#F5F5DC",    # Beige - soft openness
    
    # Activations
    "conscious": "#4A5D23",           # Forest green - grounded personality
    "unconscious": "#8B0000",         # Dark red - deep design/unconscious
    
    # Channels
    "active_channel": "#CD853F",      # Peru - warm flowing energy
    "emergent_channel": "#DAA520",    # Goldenrod - magical emergence
    "inactive_channel": "#D3D3D3",    # Light gray - dormant potential
    
    # Accents
    "twilight_purple": "#6A4C93",     # Dusk magic
    "autumn_orange": "#D97642",       # Cozy warmth
    "forest_shadow": "#2F4F2F",       # Dark green depth
    
    # UI Elements
    "background": "#FFF8E7",          # Cornsilk - warm page background
    "text": "#3E2723",                # Dark brown - readable text
    "border": "#8B6F47",              # Light brown - subtle borders
}

# CSS custom properties for theming
CSS_VARIABLES = """
:root {
    --rebecca-defined-center: #8B4513;
    --rebecca-undefined-center: #F5F5DC;
    --rebecca-conscious: #4A5D23;
    --rebecca-unconscious: #8B0000;
    --rebecca-active-channel: #CD853F;
    --rebecca-emergent-channel: #DAA520;
    --rebecca-inactive-channel: #D3D3D3;
    --rebecca-background: #FFF8E7;
    --rebecca-text: #3E2723;
}
"""
```

### Step 4: Add API Endpoints

```python
# src/human_design/web/app.py (additions)

from ..visualization.builder import BodygraphVisualizationBuilder
from ..visualization.models import BodygraphVisualizationSchema

# ... existing imports and setup ...

@app.get("/api/bodygraph/{person_id}/visualization")
async def get_bodygraph_visualization(
    person_id: int
) -> BodygraphVisualizationSchema:
    """
    Get visualization data for a person's bodygraph.
    
    Returns JSON schema ready for D3.js rendering.
    """
    # TODO: Fetch person from 64keys and calculate bodygraph
    # For now, assume we have a function to get RawBodyGraph
    from ..models.bodygraph import RawBodyGraph, BirthInfo
    
    # Mock: In real implementation, fetch from database/API
    birth_info = BirthInfo(
        date="1990-01-01",
        localtime="1990-01-01T12:00:00",
        city="New York",
        country="USA"
    )
    bodygraph = RawBodyGraph(birth_info=birth_info)
    
    builder = BodygraphVisualizationBuilder()
    return builder.build_individual(bodygraph)


@app.post("/api/bodygraph/composite/visualization")
async def get_composite_visualization(
    person_ids: list[int]
) -> BodygraphVisualizationSchema:
    """
    Get visualization for a composite bodygraph.
    
    Combines multiple people's charts and highlights emergent channels.
    """
    # TODO: Fetch people and calculate composite
    from ..models.bodygraph import RawBodyGraph
    from ..models.composite import CompositeBodyGraph
    
    # Mock: In real implementation, fetch from database/API
    charts = []  # list of RawBodyGraph instances
    
    composite = CompositeBodyGraph(charts=charts)
    
    builder = BodygraphVisualizationBuilder()
    return builder.build_composite(composite)
```

---

## Phase 3: Frontend D3.js Rendering

### Step 1: Create D3 Renderer Module

```javascript
// src/human_design/web/static/js/bodygraph.js

/**
 * Bodygraph D3.js Renderer
 * 
 * Renders Human Design bodygraph visualizations from backend JSON schema.
 * Uses Rebecca Energy aesthetic (cozy, warm, autumnal).
 */

class BodygraphRenderer {
  constructor(containerId, visualizationData) {
    this.data = visualizationData;
    this.container = d3.select(`#${containerId}`);
    
    // Create SVG canvas
    this.svg = this.container
      .append("svg")
      .attr("viewBox", this.data.svg_viewbox.join(" "))
      .attr("class", "bodygraph-svg");
    
    // Create layer groups
    this.centersGroup = this.svg.append("g").attr("class", "centers");
    this.channelsGroup = this.svg.append("g").attr("class", "channels");
    this.activationsGroup = this.svg.append("g").attr("class", "activations");
    this.labelsGroup = this.svg.append("g").attr("class", "labels");
  }
  
  render() {
    this.renderChannels();
    this.renderCenters();
    this.renderActivations();
    
    if (this.data.composite_layers) {
      this.renderCompositeLayers();
    }
  }
  
  renderCenters() {
    const centers = this.centersGroup
      .selectAll(".center")
      .data(this.data.centers)
      .enter()
      .append("g")
      .attr("class", d => `center ${d.is_defined ? "defined" : "undefined"}`)
      .attr("transform", d => `translate(${d.position[0]}, ${d.position[1]})`);
    
    centers.each(function(d) {
      const group = d3.select(this);
      
      // Render shape based on center type
      switch (d.shape) {
        case "triangle":
          group.append("polygon")
            .attr("points", "-30,25 30,25 0,-40")
            .attr("fill", d.fill_color)
            .attr("stroke", d.stroke_color)
            .attr("stroke-width", 2);
          break;
        
        case "square":
          group.append("rect")
            .attr("x", -30)
            .attr("y", -30)
            .attr("width", 60)
            .attr("height", 60)
            .attr("fill", d.fill_color)
            .attr("stroke", d.stroke_color)
            .attr("stroke-width", 2);
          break;
        
        case "diamond":
          group.append("polygon")
            .attr("points", "0,-40 40,0 0,40 -40,0")
            .attr("fill", d.fill_color)
            .attr("stroke", d.stroke_color)
            .attr("stroke-width", 2);
          break;
      }
      
      // Add center name label
      group.append("text")
        .attr("y", 5)
        .attr("text-anchor", "middle")
        .attr("class", "center-label")
        .text(d.name);
    });
  }
  
  renderChannels() {
    this.channelsGroup
      .selectAll(".channel")
      .data(this.data.channels)
      .enter()
      .append("path")
      .attr("d", d => d.path)
      .attr("stroke", d => d.stroke_color)
      .attr("stroke-width", d => d.stroke_width)
      .attr("opacity", d => d.opacity)
      .attr("fill", "none")
      .attr("class", d => `channel channel-${d.activation_type}`);
  }
  
  renderActivations() {
    const activations = this.activationsGroup
      .selectAll(".activation")
      .data(this.data.activations)
      .enter()
      .append("g")
      .attr("class", d => `activation ${d.is_conscious ? "conscious" : "unconscious"}`)
      .attr("transform", d => `translate(${d.position[0]}, ${d.position[1]})`);
    
    // Draw activation circle
    activations.append("circle")
      .attr("r", 8)
      .attr("fill", d => d.color)
      .attr("stroke", "#000")
      .attr("stroke-width", 1);
    
    // Add label
    activations.append("text")
      .attr("x", 12)
      .attr("y", 5)
      .attr("class", "activation-label")
      .text(d => d.label);
  }
  
  renderCompositeLayers() {
    // Add layer toggle controls
    const legend = this.container
      .append("div")
      .attr("class", "composite-legend");
    
    this.data.composite_layers.forEach((layer, i) => {
      const toggle = legend.append("div")
        .attr("class", "layer-toggle")
        .html(`
          <input type="checkbox" id="layer-${i}" checked>
          <label for="layer-${i}">${layer.label}</label>
        `);
      
      // Wire up toggle to show/hide layer
      toggle.select("input").on("change", function() {
        d3.selectAll(`.layer-${i}`)
          .style("display", this.checked ? "block" : "none");
      });
    });
  }
}

// Export for use in HTML
window.BodygraphRenderer = BodygraphRenderer;
```

### Step 2: Add CSS Styling

```css
/* src/human_design/web/static/css/bodygraph.css */

/* Rebecca Energy Theme Variables */
:root {
    --rebecca-defined-center: #8B4513;
    --rebecca-undefined-center: #F5F5DC;
    --rebecca-conscious: #4A5D23;
    --rebecca-unconscious: #8B0000;
    --rebecca-active-channel: #CD853F;
    --rebecca-emergent-channel: #DAA520;
    --rebecca-inactive-channel: #D3D3D3;
    --rebecca-background: #FFF8E7;
    --rebecca-text: #3E2723;
}

/* Container */
.bodygraph-container {
    background: var(--rebecca-background);
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* SVG Canvas */
.bodygraph-svg {
    max-width: 100%;
    height: auto;
}

/* Centers */
.center.defined polygon,
.center.defined rect {
    fill: var(--rebecca-defined-center);
    transition: fill 0.3s ease;
}

.center.undefined polygon,
.center.undefined rect {
    fill: var(--rebecca-undefined-center);
    stroke: var(--rebecca-defined-center);
}

.center:hover polygon,
.center:hover rect {
    filter: brightness(1.2);
}

.center-label {
    font-size: 12px;
    font-weight: 600;
    fill: var(--rebecca-text);
    pointer-events: none;
}

/* Channels */
.channel {
    transition: stroke-width 0.3s ease, opacity 0.3s ease;
}

.channel-individual {
    stroke: var(--rebecca-active-channel);
}

.channel-emergent {
    stroke: var(--rebecca-emergent-channel);
    stroke-dasharray: 5, 5;
    animation: dash 1s linear infinite;
}

.channel-none {
    stroke: var(--rebecca-inactive-channel);
}

@keyframes dash {
    to {
        stroke-dashoffset: -10;
    }
}

/* Activations */
.activation.conscious circle {
    fill: var(--rebecca-conscious);
}

.activation.unconscious circle {
    fill: var(--rebecca-unconscious);
}

.activation-label {
    font-size: 10px;
    fill: var(--rebecca-text);
    font-family: monospace;
}

/* Composite Layer Legend */
.composite-legend {
    margin-top: 20px;
    padding: 15px;
    background: rgba(255, 255, 255, 0.9);
    border-radius: 8px;
    border: 1px solid var(--rebecca-border);
}

.layer-toggle {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
}

.layer-toggle input {
    margin-right: 10px;
}

.layer-toggle label {
    color: var(--rebecca-text);
    font-weight: 500;
    cursor: pointer;
}
```

### Step 3: Create HTML Template

```html
<!-- src/human_design/web/templates/bodygraph.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bodygraph - {{ person.name }}</title>
    
    <!-- D3.js -->
    <script src="https://d3js.org/d3.v7.min.js"></script>
    
    <!-- Rebecca Energy Theme -->
    <link rel="stylesheet" href="/static/css/bodygraph.css">
    <script src="/static/js/bodygraph.js"></script>
</head>
<body>
    <div class="container">
        <h1>Bodygraph: {{ person.name }}</h1>
        
        <div id="bodygraph-container" class="bodygraph-container">
            <!-- D3 will render here -->
        </div>
        
        <div class="metadata">
            <p><strong>Birth:</strong> {{ person.birth_date }}</p>
            <p><strong>Location:</strong> {{ person.birth_city }}, {{ person.birth_country }}</p>
        </div>
    </div>
    
    <script>
        // Fetch visualization data and render
        fetch(`/api/bodygraph/{{ person.id }}/visualization`)
            .then(res => res.json())
            .then(data => {
                const renderer = new BodygraphRenderer("bodygraph-container", data);
                renderer.render();
            })
            .catch(err => {
                console.error("Failed to load bodygraph:", err);
            });
    </script>
</body>
</html>
```

---

## Phase 4: Integration and Testing

### Testing Strategy

#### Unit Tests (Backend)

```python
# tests/test_visualization_builder.py
import pytest
from human_design.models.bodygraph import RawBodyGraph, BirthInfo
from human_design.visualization.builder import BodygraphVisualizationBuilder

def test_build_individual_visualization():
    """Test individual bodygraph visualization generation."""
    birth_info = BirthInfo(
        date="1990-01-01",
        localtime="1990-01-01T12:00:00",
        city="New York",
        country="USA"
    )
    bodygraph = RawBodyGraph(birth_info=birth_info)
    
    builder = BodygraphVisualizationBuilder()
    viz = builder.build_individual(bodygraph)
    
    # Assertions
    assert len(viz.centers) == 9  # All centers present
    assert len(viz.channels) == 36  # All channels present
    assert viz.composite_layers is None  # No layers for individual
    assert viz.svg_viewbox == (0, 0, 800, 1000)  # Correct viewBox

def test_composite_visualization_emergent_channels():
    """Test emergent channels are identified in composite visualization."""
    # Create two charts that form emergent channel
    # (Implementation depends on test data)
    pass
```

#### Visual Regression Tests

```python
# tests/test_visual_regression.py
"""
Visual regression tests comparing rendered SVGs to reference images.

Uses Playwright or Selenium to capture screenshots.
"""
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        yield browser
        browser.close()

def test_bodygraph_rendering(browser):
    """Compare rendered bodygraph to reference screenshot."""
    page = browser.new_page()
    page.goto("http://localhost:8000/bodygraph/1")
    
    # Wait for D3 rendering to complete
    page.wait_for_selector(".bodygraph-svg")
    
    # Take screenshot
    screenshot = page.screenshot()
    
    # Compare to reference (using imagehash or similar)
    # assert screenshot_matches_reference(screenshot)
```

### Integration Checklist

- [ ] Phase 1 research complete (64keys geometry extracted)
- [ ] Backend models implemented and tested
- [ ] API endpoints return valid JSON
- [ ] D3 renderer displays all centers correctly
- [ ] Channels render with correct paths
- [ ] Activations show at correct positions
- [ ] Composite layers toggle on/off
- [ ] Rebecca Energy theme applied consistently
- [ ] Mobile responsive (viewBox scaling works)
- [ ] Accessibility (SVG has ARIA labels)

---

## Next Steps

1. **Complete Phase 1 Research**
   - Inspect 64keys.com and document geometry
   - Fill in `geometry.py` with real coordinates

2. **Implement Backend**
   - Create Pydantic visualization models
   - Build `BodygraphVisualizationBuilder`
   - Add API endpoints
   - Write unit tests

3. **Implement Frontend**
   - Build D3.js `BodygraphRenderer`
   - Style with Rebecca Energy CSS
   - Create HTML template
   - Test in browser

4. **Visual QA**
   - Compare to 64keys screenshots
   - Adjust geometry if needed
   - Test composite overlays
   - Get stakeholder sign-off

---

## Resources

- [D3.js Gallery](https://observablehq.com/@d3/gallery)
- [SVG Path Syntax](https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Paths)
- [Pydantic JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/)
- [FastAPI Static Files](https://fastapi.tiangolo.com/tutorial/static-files/)

---

**Document Status:** Draft  
**Last Updated:** 2025-01-30  
**Owner:** Visualization Team (Strand 2)
