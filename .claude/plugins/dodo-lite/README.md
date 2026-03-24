# DODO-Lite Plugin

Workspace-local embedded multi-agent investigation system for Human Design.

## What is DODO-Lite?

DODO-Lite is an embedded multi-agent investigation system inspired by Neal Stephenson's "The Rise and Fall of D.O.D.O."

**DODO**: Distributed Ontology-Driven Operations

Embedded directly in the Human Design codebase (`src/human_design/strands/`), it provides self-sufficient strand execution without external dependencies.

## Architecture

```
src/human_design/strands/
├── __init__.py           # Public API
├── models.py             # StrandDefinition, StrandResult, StrandStatus
├── builder.py            # Strand execution orchestration
├── agent_factory.py      # Hardcoded agent loading
└── convenience.py        # create_strand() wrapper
```

## Available Agents

### Embedded Agents (Always Available)
- **implementer** - Feature implementation with tool integration
- **test_engineer** - Test suite creation and validation
- **d3_specialist** - D3.js visualization design and implementation
- **python_linguist** - Code quality and LibCST-based introspection

### External Agents (Requires DODO)
- **researcher** - Codebase analysis
- **architect** - Architecture design
- **coordinator** - Multi-agent synthesis
- **fair_witness** - Validation and correctness checking

## Usage

### Direct Python API

```python
from human_design.strands import create_strand

# Create and execute strand
strand = create_strand(
    problem="Implement bodygraph caching layer",
    agents=["implementer", "test_engineer"],
    strand_type="implementation"
)

result = await strand.run()
print(result.findings)
```

### Via Skills

```bash
# Refine code using multi-agent analysis
/refine d3_specialist agent

# Implement feature
/implement bodygraph caching

# Create D3 visualization
/visualize interactive bodygraph with hover states
```

## Skills

### `/refine`
Analyze and improve code/agents using embedded multi-agent investigation.

**Agents Used**: `python_linguist` + `implementer` (or custom composition)

**Example**:
```bash
/refine d3_specialist agent
/refine bodygraph calculation logic
```

### `/implement`
Implement features using test-driven development workflow.

**Agents Used**: `implementer` + `test_engineer`

**Example**:
```bash
/implement bodygraph caching layer
/implement composite chart calculation
```

### `/visualize`
Create D3.js visualizations for bodygraphs.

**Agents Used**: `d3_specialist`

**Example**:
```bash
/visualize interactive bodygraph with hover
/visualize composite chart overlay
```

## Configuration

See `plugin.json` for available agents and configuration options.

## Why DODO-Lite?

**Problem**: Using external DODO creates coupling and deployment complexity.

**Solution**: Embed minimal strand system directly in Human Design codebase.

**Benefits**:
- ✅ Self-sufficient (no external dependencies)
- ✅ Hardcoded agents (no ontology lookup)
- ✅ Breaks bootstrap problem (agents can use strands)
- ✅ Fallback to DODO for advanced agents
- ✅ Simple API (`create_strand()` → `await strand.run()`)

## See Also

- `src/human_design/strands/` - DODO-Lite implementation
- `.claude/plugins/dodo-lite/skills/` - Skill implementations
- `CLAUDE.md` - Workspace-specific instructions
