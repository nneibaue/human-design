# ADR 002: Bodygraph Visualization Architecture

**Status:** Proposed  
**Date:** 2025-01-30  
**Context:** Strand 2 - Visualization Implementation

## Context

We need to implement accurate Human Design bodygraph visualizations that:

1. **Accurately render** all 9 centers, 36 channels, and 64 gates with correct geometric relationships
2. **Support composite charts** showing individual + composite + emergent channels in different visual styles
3. **Follow Rebecca Energy aesthetic** (cozy autumnal forest, twilight magic) - warm, not clinical
4. **Work with existing models** (`RawBodyGraph`, `CompositeBodyGraph` from Strand 1)

### Current System State

**Existing models (from Strand 1):**
- `RawBodyGraph`: Individual chart with conscious/unconscious activations
- `CompositeBodyGraph`: Stacked gate activations for interaction/penta/transit charts
- `ChannelDefinition`: Channel metadata with gate pairs and center connections
- `CenterRegistry`: Gate → Center mappings
- `emergent_channels()`: Channels that form only in composite

**Web infrastructure:**
- FastAPI app with auth, people browser, chart URL generation
- Jinja2 templates (no visualization rendering yet)
- API endpoints for chart data

**Key questions:**
- How does 64keys.com render bodygraphs? (Need to inspect their site)
- What SVG structure preserves geometric accuracy?
- How to overlay composite layers clearly?

## Decision

**Implement a layered SVG rendering architecture using D3.js** for accurate, interactive bodygraph visualizations with semantic overlays.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (Browser)                     │
├─────────────────────────────────────────────────────────┤
│  Bodygraph Component (D3.js + Rebecca Energy theme)     │
│    ├─ SVG Canvas Layer                                  │
│    ├─ Bodygraph Geometry Layer (centers, channels)      │
│    ├─ Activation Overlay Layer (conscious/unconscious)  │
│    └─ Composite Overlay Layer (emergent channels)       │
└─────────────────────────────────────────────────────────┘
                        ↕ JSON
┌─────────────────────────────────────────────────────────┐
│              Backend (FastAPI + Pydantic)                │
├─────────────────────────────────────────────────────────┤
│  NEW: BodygraphVisualizationSchema                      │
│    ├─ centers: list[CenterVisualization]                │
│    ├─ channels: list[ChannelVisualization]              │
│    ├─ activations: list[ActivationVisualization]        │
│    └─ composite_layers: list[CompositeLayer]            │
└─────────────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────────────┐
│             Existing Models (Strand 1)                   │
│  RawBodyGraph, CompositeBodyGraph, ChannelDefinition    │
└─────────────────────────────────────────────────────────┘
```

### Why D3.js?

**Accuracy First:**
- SVG provides precise geometric control for center positions, channel paths
- D3's data binding ensures rendering matches calculated data exactly
- Declarative transformations (scales, paths, shapes) reduce manual coordinate math

**Aesthetics Second:**
- Full control over colors, gradients, filters (Rebecca Energy theme)
- CSS styling for cozy, warm feel vs clinical look
- Smooth transitions for activation overlays

**Composability:**
- Layer-based rendering naturally separates individual vs composite data
- Can highlight emergent channels with distinct visual treatment
- Easy to add/remove layers for different view modes

### Core Data Types

```python
# NEW: Visualization-specific models (separate from calculation models)

class CenterVisualization(BaseModel):
    """Visual representation of a center."""
    name: CenterName
    position: tuple[float, float]  # (x, y) in SVG coordinates
    is_defined: bool
    shape: Literal["triangle", "square", "diamond"]  # Shape varies by center
    fill_color: str  # Rebecca Energy palette
    stroke_color: str
    size: float

class ChannelVisualization(BaseModel):
    """Visual representation of a channel."""
    channel_id: int
    gate_a: GateNumber
    gate_b: GateNumber
    path: str  # SVG path string (calculated from center positions)
    is_active: bool
    activation_type: Literal["individual", "emergent", "none"]
    stroke_color: str  # Varies by activation type
    stroke_width: float
    opacity: float

class ActivationVisualization(BaseModel):
    """Visual representation of a gate activation."""
    gate: GateNumber
    planet: str
    is_conscious: bool  # True = personality, False = design
    position: tuple[float, float]  # Position on channel
    color: str  # conscious vs unconscious color
    
class CompositeLayer(BaseModel):
    """Layer showing composite-specific data."""
    layer_type: Literal["individual", "composite", "emergent"]
    channels: list[ChannelVisualization]
    opacity: float
    
class BodygraphVisualizationSchema(BaseModel):
    """Complete visualization data for frontend rendering."""
    centers: list[CenterVisualization]
    channels: list[ChannelVisualization]
    activations: list[ActivationVisualization]
    composite_layers: list[CompositeLayer] | None  # Only for composite charts
    svg_viewbox: tuple[float, float, float, float]  # (x, y, width, height)
```

### Rebecca Energy Color Palette

```python
REBECCA_PALETTE = {
    # Centers
    "defined_center": "#8B4513",      # Saddle brown - earthy
    "undefined_center": "#F5F5DC",    # Beige - soft undefined
    
    # Activations
    "conscious": "#4A5D23",           # Forest green - grounded personality
    "unconscious": "#8B0000",         # Dark red - deep design
    
    # Channels
    "active_channel": "#CD853F",      # Peru - warm channel flow
    "emergent_channel": "#DAA520",    # Goldenrod - magical emergence
    "inactive_channel": "#D3D3D3",    # Light gray - dormant potential
    
    # Accents
    "twilight_purple": "#6A4C93",     # Dusk magic
    "autumn_orange": "#D97642",       # Cozy warmth
}
```

## Implementation Strategy

### Phase 1: Reverse-Engineer 64keys Rendering

**Research task (before implementation):**
1. Inspect 64keys.com bodygraph page with browser DevTools
2. Identify rendering approach:
   - SVG? Canvas? Image tiles?
   - If SVG: Extract center positions, channel paths
   - If Canvas: Screenshot and measure geometric relationships
3. Document findings in `docs/64keys-rendering-analysis.md`

**Deliverable:** Accurate center positions and channel path coordinates

### Phase 2: Backend Visualization API

**New endpoint:**
```python
@app.get("/api/bodygraph/{person_id}/visualization")
async def get_bodygraph_visualization(
    person_id: int
) -> BodygraphVisualizationSchema:
    """
    Generate visualization data for a person's bodygraph.
    
    Returns JSON with all centers, channels, activations
    positioned for SVG rendering.
    """
```

**New endpoint for composites:**
```python
@app.post("/api/bodygraph/composite/visualization")
async def get_composite_visualization(
    person_ids: list[int]
) -> BodygraphVisualizationSchema:
    """
    Generate composite visualization with layered channels.
    
    Separates individual vs emergent channels into layers.
    """
```

**Type Safety:**
- All visualization data validated with Pydantic
- Frontend receives guaranteed structure
- No `Any` or untyped dicts

### Phase 3: Frontend D3.js Component

**File structure:**
```
src/human_design/web/static/
├── js/
│   ├── bodygraph.js          # Main D3 rendering logic
│   ├── rebecca-theme.js       # Color palette and styles
│   └── composite-layers.js    # Composite overlay logic
└── css/
    └── bodygraph.css          # Rebecca Energy aesthetic styles
```

**D3 Rendering Pattern:**
```javascript
// bodygraph.js
class BodygraphRenderer {
  constructor(containerId, visualizationData) {
    this.data = visualizationData;
    this.svg = d3.select(`#${containerId}`)
      .append("svg")
      .attr("viewBox", this.data.svg_viewbox);
  }
  
  renderCenters() {
    // Bind center data to SVG shapes
    this.svg.selectAll(".center")
      .data(this.data.centers)
      .enter()
      .append(d => this.getCenterShape(d))
      .attr("fill", d => d.fill_color)
      .attr("class", d => `center ${d.is_defined ? "defined" : "undefined"}`);
  }
  
  renderChannels() {
    // Draw channel paths with activation states
    this.svg.selectAll(".channel")
      .data(this.data.channels)
      .enter()
      .append("path")
      .attr("d", d => d.path)
      .attr("stroke", d => d.stroke_color)
      .attr("stroke-width", d => d.stroke_width)
      .attr("class", d => `channel ${d.activation_type}`);
  }
  
  renderActivations() {
    // Show planetary activations on gates
    this.svg.selectAll(".activation")
      .data(this.data.activations)
      .enter()
      .append("circle")
      .attr("cx", d => d.position[0])
      .attr("cy", d => d.position[1])
      .attr("fill", d => d.color)
      .attr("class", d => d.is_conscious ? "conscious" : "unconscious");
  }
  
  renderCompositeLayers() {
    // Overlay composite-specific channels
    if (!this.data.composite_layers) return;
    
    this.data.composite_layers.forEach(layer => {
      this.svg.append("g")
        .attr("class", `layer-${layer.layer_type}`)
        .attr("opacity", layer.opacity)
        .selectAll(".composite-channel")
        .data(layer.channels)
        .enter()
        .append("path")
        .attr("d", d => d.path)
        .attr("stroke", d => d.stroke_color);
    });
  }
}
```

### Phase 4: Integration with Existing UI

**New page route:**
```python
@app.get("/bodygraph/{person_id}", response_class=HTMLResponse)
async def bodygraph_page(request: Request, person_id: int) -> HTMLResponse:
    """Render bodygraph visualization page for a person."""
    if not request.session.get("authenticated"):
        return RedirectResponse(url="/login", status_code=303)
    
    person = await get_person(person_id)
    return templates.TemplateResponse(
        "bodygraph.html",
        {
            "request": request,
            "person": person,
        }
    )
```

**Template:**
```html
<!-- templates/bodygraph.html -->
<div id="bodygraph-container"></div>

<script>
  fetch(`/api/bodygraph/{{ person.id }}/visualization`)
    .then(res => res.json())
    .then(data => {
      const renderer = new BodygraphRenderer("bodygraph-container", data);
      renderer.renderCenters();
      renderer.renderChannels();
      renderer.renderActivations();
    });
</script>
```

## Consequences

### Positive

✅ **Type-Safe Visualization Pipeline**
- Pydantic validates all visualization data before frontend
- Frontend receives guaranteed JSON structure
- No runtime surprises from malformed data

✅ **Separation of Concerns**
- Calculation logic (Strand 1) stays pure Python
- Visualization logic separate, reusable
- Can swap rendering library without touching calculation models

✅ **Accurate Geometry**
- SVG coordinates ensure precise center/channel positions
- D3 data binding prevents desync between data and rendering
- Can export exact coordinates for testing

✅ **Composite Chart Support**
- Layer-based architecture naturally supports individual + emergent channels
- Visual distinction between activation types
- Easy to toggle layers on/off

✅ **Aesthetic Flexibility**
- Rebecca Energy palette defined once, applied consistently
- CSS theming allows easy color adjustments
- Can create alternate themes (clinical, high-contrast, etc.)

### Negative

⚠️ **Dependency on 64keys Geometry**
- Must reverse-engineer accurate center positions from 64keys
- If 64keys changes rendering, our coordinates may drift
- Mitigation: Store reference screenshots, validate against known charts

⚠️ **Frontend Complexity**
- D3 learning curve for future contributors
- SVG coordinate math can be tricky
- Mitigation: Well-documented component with inline comments

⚠️ **Performance Considerations**
- Large composite charts (5+ people) may have many overlapping channels
- SVG rendering can slow with hundreds of elements
- Mitigation: Use SVG groups, CSS transforms, consider Canvas fallback for large charts

### Risks

🔴 **Geometric Accuracy Risk**
- If we guess center positions, channels may look wrong
- **Mitigation:** Phase 1 research MUST complete before Phase 2

🟡 **Browser Compatibility**
- Older browsers may render SVG differently
- **Mitigation:** Test on Chrome, Firefox, Safari; document requirements

🟢 **Data Model Changes**
- Visualization models decoupled from calculation models
- **Mitigation:** Changes to `RawBodyGraph` won't break visualizations

## Alternatives Considered

### Alternative 1: Server-Side Rendering (SVG Generation in Python)

**Rejected because:**
- Python SVG libraries (e.g., svgwrite) lack D3's data binding elegance
- No interactivity (hover, zoom, toggle layers)
- Harder to apply CSS theming

### Alternative 2: Canvas Rendering

**Rejected because:**
- Harder to maintain geometric precision
- No DOM for CSS styling
- Worse accessibility (no semantic SVG elements)

**When to reconsider:** If composite charts with 10+ people become slow in SVG

### Alternative 3: Pre-rendered Images from 64keys

**Rejected because:**
- No control over aesthetic (can't apply Rebecca Energy theme)
- Can't highlight emergent channels in composites
- Copyright concerns

## Open Questions

1. **What are the exact SVG coordinates for the 9 centers?**
   - Answer in Phase 1 research
   
2. **How should channel paths curve? Straight lines or Bezier curves?**
   - Inspect 64keys rendering for answer
   
3. **Should we support zooming/panning for large charts?**
   - Defer to Phase 4, use D3 zoom behavior if needed
   
4. **How to handle mobile rendering?**
   - SVG viewBox scales automatically, but may need simplified view for small screens

## Next Steps

1. **Research Phase (Strand 2, Sprint 1):**
   - Inspect 64keys.com bodygraph rendering
   - Extract center positions, channel paths
   - Document in `docs/64keys-rendering-analysis.md`

2. **Backend Implementation (Sprint 2):**
   - Create visualization Pydantic models
   - Implement `/api/bodygraph/{id}/visualization` endpoint
   - Write tests with known chart data

3. **Frontend Implementation (Sprint 3):**
   - Build D3.js `BodygraphRenderer` component
   - Apply Rebecca Energy theme CSS
   - Integrate with existing web UI

4. **Composite Support (Sprint 4):**
   - Extend visualization models for composite layers
   - Implement `/api/bodygraph/composite/visualization` endpoint
   - Add layer toggle UI controls

## References

- [D3.js Documentation](https://d3js.org/)
- [SVG Specification](https://www.w3.org/TR/SVG2/)
- Existing codebase: `src/human_design/models/bodygraph.py`, `composite.py`
- 64keys.com: https://www.64keys.com/chart (requires research)

---

**Decision Maker:** Architect Agent (Pydantic-trained)  
**Review Status:** Awaiting stakeholder review  
**Implementation Owner:** TBD (Strand 2 team)
