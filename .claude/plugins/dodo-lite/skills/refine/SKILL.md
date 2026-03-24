# /refine

Refine code/agents using embedded multi-agent investigation system (DODO-Lite).

## Usage

```bash
/refine <target> [options]
```

**Examples**:
```bash
/refine d3_specialist agent
/refine bodygraph calculation logic
/refine channel formation algorithm
/refine --agents python_linguist,implementer src/human_design/models/bodygraph.py
```

## How It Works

1. **Problem Analysis**: Parse user request to understand refinement target
2. **Agent Selection**: Choose appropriate agents (defaults: `python_linguist`, `implementer`)
3. **Strand Execution**: Create and run multi-agent investigation
4. **Results Presentation**: Show findings and recommendations

## Default Agent Composition

```python
agents = ["python_linguist", "implementer"]
```

**python_linguist**: Analyzes code structure, identifies patterns, suggests improvements
**implementer**: Proposes concrete implementation changes

## Options

- `--agents <list>` - Override default agents (comma-separated)
- `--type <type>` - Strand type (default: "refinement")
- `--context <json>` - Additional context for agents

## Example Output

```
🔍 Refining: d3_specialist agent

📊 Analysis Phase (python_linguist):
  - Current implementation: 235 lines
  - Tool registration: Placeholder (TODO)
  - System prompt: 149 lines (conceptual examples)
  - Missing: Custom @agent.tool methods

🛠️ Implementation Recommendations (implementer):
  1. Add tool registration (dodo shared tools)
  2. Implement 3 custom tools:
     - convert_bodygraph_to_d3_data
     - generate_d3_visualization_code
     - validate_svg_geometry
  3. Enhance system prompt with RawBodyGraph examples

📁 Files Generated:
  - strand-results/active/REFINEMENT_ANALYSIS.md
  - strand-results/active/IMPLEMENTATION_RECOMMENDATIONS.md

✅ Refinement complete. Apply recommendations? [Y/n]
```

## Implementation

Uses embedded DODO-Lite system:

```python
from human_design.strands import create_strand

strand = create_strand(
    problem=f"Refine {target}",
    agents=["python_linguist", "implementer"],
    strand_type="refinement"
)

result = await strand.run()
```

## See Also

- `/implement` - Implement features with TDD
- `/visualize` - Create D3 visualizations
- `src/human_design/strands/` - DODO-Lite implementation
