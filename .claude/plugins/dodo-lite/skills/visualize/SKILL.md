# /visualize

Create D3.js visualizations using d3_specialist agent.

## Usage

```bash
/visualize <visualization_description>
```

**Examples**:
```bash
/visualize interactive bodygraph with hover states
/visualize composite chart overlay for family penta
/visualize transit visualization with current sky
/visualize --features hover,click,zoom bodygraph with Rebecca Energy aesthetic
```

## How It Works

1. **Visualization Specification**: Parse user request for visualization requirements
2. **Agent Execution**: Use `d3_specialist` for D3.js implementation
3. **Strand Execution**: Agent designs and implements visualization:
   - Converts RawBodyGraph data to D3-friendly JSON
   - Generates D3.js v7 code
   - Creates Rebecca Energy styling
4. **Results**: Working D3 visualization code ready to integrate

## Default Agent

```python
agents = ["d3_specialist"]
```

**d3_specialist**: D3.js visualization design and implementation
- Understands bodygraph geometry (9 centers, 36 channels, 64 gates)
- Uses Rebecca Energy aesthetic (warm, cozy, magical)
- Generates modern D3 v7 code
- Creates interactive features (hover, click, zoom)

## Options

- `--features <list>` - Interaction features (comma-separated: hover, click, zoom)
- `--style <name>` - Style preset (default: rebecca_energy)
- `--agents <list>` - Add additional agents (e.g., implementer for backend integration)

## Example Output

```
🎨 Creating visualization: interactive bodygraph with hover states

📊 Design Phase (d3_specialist):
  - Data structure: RawBodyGraph → D3 JSON
  - Features: hover tooltips, responsive layout
  - Style: Rebecca Energy palette
  - Technology: D3.js v7, SVG

🔨 Implementation Phase (d3_specialist):
  ✓ Created data transformation: convert_bodygraph_to_d3_data()
  ✓ Generated D3 code: renderBodygraph()
  ✓ Added hover interactions
  ✓ Applied Rebecca Energy styling

📁 Files Generated:
  - static/js/d3-bodygraph.js (NEW)
  - static/css/bodygraph-styles.css (NEW)
  - strand-results/active/VISUALIZATION_SPEC.md

✅ Visualization complete. Preview in browser? [Y/n]
```

## Rebecca Energy Aesthetic

All visualizations use Rebecca Energy color palette:

```css
--defined-center: #8B4513;      /* Saddle brown */
--undefined-center: #F5F5DC;    /* Beige */
--conscious: #4A5D23;           /* Dark olive green */
--unconscious: #8B0000;         /* Dark red */
--emergent: #DAA520;            /* Goldenrod */
--background: #2C1810;          /* Deep brown */
--text: #F5E6D3;                /* Warm cream */
```

## D3.js v7 Patterns

Generated code uses modern D3 v7 patterns:

```javascript
// Data binding with .join()
const centers = svg.selectAll('.center')
  .data(bodygraphData.centers, d => d.name)
  .join('g')
  .attr('class', 'center')
  .attr('transform', d => `translate(${d.x}, ${d.y})`);

// Interactive overlays
centers.on('mouseover', (event, d) => {
  tooltip
    .style('opacity', 1)
    .html(`<strong>${d.name}</strong>`)
    .style('left', event.pageX + 'px')
    .style('top', event.pageY + 'px');
});
```

## Implementation

Uses embedded DODO-Lite system:

```python
from human_design.strands import create_strand

strand = create_strand(
    problem=f"Create visualization: {description}",
    agents=["d3_specialist"],
    strand_type="visualization",
    context={
        "features": ["hover", "click"],
        "style": "rebecca_energy"
    }
)

result = await strand.run()
```

## Integration with Backend

For full-stack implementations, add `implementer`:

```bash
/visualize --agents d3_specialist,implementer bodygraph API endpoint
```

This will:
1. `d3_specialist`: Create frontend D3 visualization
2. `implementer`: Create FastAPI endpoint to serve bodygraph data

## See Also

- `/implement` - Implement features with TDD
- `/refine` - Refine existing code
- `src/human_design/agents/d3_specialist.py` - D3 specialist agent
- `docs/bodygraph-visualization-implementation-guide.md` - Visualization guide
