# D3 Specialist Agent - Implementation Plan

**Date**: 2026-03-23
**Status**: Ready for Implementation
**Priority**: HIGH
**Estimated Effort**: 1-2 days (HIGH priority items), 3-5 days (complete refinement)

## Overview

This plan provides step-by-step implementation guidance for refining the d3_specialist agent based on analysis findings and the refined implementation provided.

## Files Generated

1. **`D3_SPECIALIST_REFINEMENT_ANALYSIS.md`** - Comprehensive analysis of current state and gaps
2. **`D3_SPECIALIST_REFINED.py`** - Complete refined implementation (ready to use)
3. **`D3_SPECIALIST_IMPLEMENTATION_PLAN.md`** - This file

## Implementation Phases

### Phase 1: Core Refinements (HIGH Priority - Day 1)

#### 1.1 Replace Existing Agent Implementation

**Action**: Replace `src/human_design/agents/d3_specialist.py` with refined version

```bash
# Backup current implementation
cp src/human_design/agents/d3_specialist.py src/human_design/agents/d3_specialist.py.backup

# Copy refined implementation
cp strand-results/active/D3_SPECIALIST_REFINED.py src/human_design/agents/d3_specialist.py
```

**Changes**:
- ✅ Added tool registration structure (placeholder for dodo tools)
- ✅ Implemented 3 custom @agent.tool methods:
  - `convert_bodygraph_to_d3_data()`
  - `generate_d3_visualization_code()`
  - `validate_svg_geometry()`
- ✅ Enhanced system prompt with RawBodyGraph examples
- ✅ Improved D3SpecialistDeps validation (creates missing directories)
- ✅ Added error handling to design_visualization()

**Testing**:
```python
# Test agent initialization
from human_design.agents.d3_specialist import D3SpecialistAgent, D3SpecialistConfig
from pathlib import Path

config = D3SpecialistConfig(
    workspace_root=Path.cwd(),
    static_directory=Path("static")
)
agent = D3SpecialistAgent(config)
print("✅ Agent initialized successfully")
```

#### 1.2 Import dodo Shared Tools

**Action**: Uncomment and configure tool registration in `create_d3_specialist_agent()`

```python
# In d3_specialist.py, uncomment:
from dodo.agent_tools import (
    register_filesystem_tools,
    register_code_search_tools,
    register_git_history_tools,
)

def create_d3_specialist_agent(deps: D3SpecialistDeps, model: str | None = None) -> Agent:
    agent = Agent(...)

    # UNCOMMENT THESE:
    register_filesystem_tools(agent)      # read_file, write_file, list_directory
    register_code_search_tools(agent)     # grep, glob
    register_git_history_tools(agent)     # git_log, git_diff

    _register_d3_tools(agent)
    return agent
```

**Verification**:
```python
# Check tools are registered
agent = create_d3_specialist_agent(deps)
print(f"Registered tools: {len(agent.tools)}")
# Should show: filesystem (3) + code_search (2) + git_history (2) + d3_custom (3) = 10+ tools
```

#### 1.3 Update Config YAML

**Action**: Update `src/human_design/agents/configs/d3_specialist.yaml` with new tool references

```yaml
# Add to existing config
tools:
  # Shared tools (from dodo)
  - read_file
  - write_file
  - list_directory
  - grep
  - glob
  - git_log
  - git_diff

  # Custom D3 tools
  - convert_bodygraph_to_d3_data
  - generate_d3_visualization_code
  - validate_svg_geometry

# Add tool descriptions
tool_descriptions:
  convert_bodygraph_to_d3_data: "Convert RawBodyGraph dict to D3-friendly JSON"
  generate_d3_visualization_code: "Generate D3.js v7 visualization code"
  validate_svg_geometry: "Validate SVG geometry for accuracy"
```

**Duration**: 2-3 hours

---

### Phase 2: Integration Testing (HIGH Priority - Day 1)

#### 2.1 Create Test Fixtures

**Action**: Create `tests/test_d3_specialist.py` with fixtures

```python
import pytest
from pathlib import Path
from human_design.agents.d3_specialist import (
    D3SpecialistAgent,
    D3SpecialistConfig,
    create_d3_specialist_agent,
)
from human_design.models.bodygraph import RawBodyGraph, PlanetActivation
from human_design.models.core import Planet, HDType, Authority, Profile

@pytest.fixture
def test_bodygraph():
    """Create test bodygraph for agent testing."""
    return RawBodyGraph(
        personality={
            Planet.SUN: PlanetActivation(gate=42, line=3, longitude=264.5),
            Planet.EARTH: PlanetActivation(gate=32, line=3, longitude=84.5),
        },
        design={
            Planet.SUN: PlanetActivation(gate=53, line=1, longitude=177.2),
            Planet.EARTH: PlanetActivation(gate=54, line=1, longitude=357.2),
        },
        defined_centers={'LIFEFORCE', 'EMOTION'},
        defined_channels=[],
        hd_type=HDType.BUILDER,
        authority=Authority.EMOTIONAL,
        profile=Profile.PROFILE_6_2
    )

@pytest.fixture
def d3_agent(tmp_path):
    """Create D3 specialist agent for testing."""
    config = D3SpecialistConfig(
        workspace_root=tmp_path,
        static_directory=Path("static")
    )
    return D3SpecialistAgent(config)
```

#### 2.2 Unit Tests for Custom Tools

**Action**: Test each @agent.tool method

```python
@pytest.mark.asyncio
async def test_convert_bodygraph_to_d3_data(d3_agent, test_bodygraph):
    """Test bodygraph to D3 JSON conversion."""
    # Convert via agent tool
    result = await d3_agent.agent.run(
        "Convert this bodygraph to D3 data",
        deps=d3_agent.deps,
        message_history=[
            {"role": "user", "content": f"Bodygraph: {test_bodygraph.dict()}"}
        ]
    )

    # Verify structure
    assert "centers" in result.data
    assert "gates" in result.data
    assert "type" in result.data
    assert result.data["type"] == "BUILDER"

@pytest.mark.asyncio
async def test_generate_d3_code(d3_agent):
    """Test D3 code generation."""
    schema = {
        "centers": [{"name": "LIFEFORCE", "x": 200, "y": 400}],
        "channels": [],
        "gates": []
    }

    result = await d3_agent.agent.run(
        f"Generate D3 code for this schema with hover interaction: {schema}",
        deps=d3_agent.deps
    )

    # Verify D3 v7 patterns
    code = result.data
    assert "d3.select" in code
    assert ".join(" in code  # D3 v7
    assert "mouseover" in code  # Hover interaction

@pytest.mark.asyncio
async def test_validate_svg_geometry(d3_agent):
    """Test SVG geometry validation."""
    positions = {
        "INSPIRATION": (200, 50),
        "MIND": (200, 100),
        # ... all 9 centers
    }
    paths = {
        "42-53": "M 200 400 L 180 300"
    }

    result = await d3_agent.agent.run(
        f"Validate geometry: positions={positions}, paths={paths}",
        deps=d3_agent.deps
    )

    validation = result.data
    assert "valid" in validation
    assert "errors" in validation
    assert "warnings" in validation
```

#### 2.3 Integration Test

**Action**: Test complete agent workflow

```python
@pytest.mark.asyncio
async def test_agent_end_to_end(d3_agent, test_bodygraph):
    """Test complete visualization design workflow."""
    result = await d3_agent.design_visualization(
        feature="bodygraph_with_hover_and_click",
        context={
            "bodygraph": test_bodygraph.dict(),
            "interactions": ["hover", "click"]
        }
    )

    assert result["status"] == "completed"
    assert result["agent"] == "d3_specialist"
    assert "design" in result
```

**Duration**: 3-4 hours

---

### Phase 3: Documentation (MEDIUM Priority - Day 2)

#### 3.1 Update README

**Action**: Add D3 specialist section to project README

```markdown
## Bodygraph Visualization

The `d3_specialist` agent handles D3.js visualization design and implementation.

### Usage

```python
from human_design.agents.d3_specialist import D3SpecialistAgent, D3SpecialistConfig

# Initialize agent
config = D3SpecialistConfig(
    workspace_root=Path.cwd(),
    static_directory=Path("static")
)
agent = D3SpecialistAgent(config)

# Design visualization
result = await agent.design_visualization(
    feature="interactive_bodygraph",
    context={
        "bodygraph": raw_bodygraph.dict(),
        "interactions": ["hover", "click", "zoom"]
    }
)
```

### Available Tools

- **convert_bodygraph_to_d3_data** - Transform RawBodyGraph to D3 JSON
- **generate_d3_visualization_code** - Generate D3.js v7 code
- **validate_svg_geometry** - Validate SVG geometry

### Rebecca Energy Aesthetic

The agent uses warm, cozy colors:
- Defined centers: `#8B4513` (saddle brown)
- Undefined centers: `#F5F5DC` (beige)
- Conscious: `#4A5D23` (dark olive green)
- Unconscious: `#8B0000` (dark red)
```

#### 3.2 Create Agent Usage Guide

**Action**: Create `docs/agents/d3_specialist_guide.md`

**Content**:
- Tool reference
- Example workflows
- Integration patterns
- Troubleshooting

**Duration**: 2-3 hours

---

### Phase 4: SVG Geometry Research (MEDIUM Priority - Day 2-3)

**Critical**: The refined agent has placeholder positions. Real geometry needs extraction from 64keys.com.

#### 4.1 Extract Actual Center Positions

**Action**: Follow `docs/bodygraph-visualization-implementation-guide.md` Phase 1

**Steps**:
1. Inspect 64keys.com chart SVG
2. Extract center (x, y) coordinates
3. Update `convert_bodygraph_to_d3_data()` with real positions
4. Document center shapes (triangle vs square vs diamond)

**Example**:
```python
CENTER_POSITIONS = {
    "INSPIRATION": (200, 50),     # Head/Crown - diamond
    "MIND": (200, 100),            # Ajna - triangle
    "EXPRESSION": (200, 180),      # Throat - square
    "IDENTITY": (200, 280),        # G-Center - diamond
    "WILLPOWER": (150, 280),       # Ego - triangle
    "EMOTION": (180, 350),         # Solar Plexus - triangle
    "DRIVE": (220, 450),           # Sacral - square
    "LIFEFORCE": (200, 520),       # Root - square
    "INTUITION": (250, 350),       # Spleen - triangle
}
```

#### 4.2 Extract Channel Paths

**Action**: Extract SVG path strings for all 36 channels

**Output**: `src/human_design/visualization/channel_paths.py`

```python
CHANNEL_PATHS = {
    "1-8": "M 200 520 L 200 280",   # LIFEFORCE → IDENTITY
    "42-53": "M 200 520 L 180 350", # LIFEFORCE → EMOTION
    # ... all 36 channels
}
```

**Duration**: 4-6 hours (research-heavy)

---

### Phase 5: Production Hardening (LOW Priority - Week 2+)

#### 5.1 Error Handling Enhancement

**Action**: Add retries, fallbacks, detailed logging

```python
async def design_visualization(self, feature: str, context: dict) -> dict:
    """Design D3 visualization with retry logic."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = await self.agent.run(...)
            return {
                "design": result.data,
                "status": "completed",
                "agent": "d3_specialist",
            }
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                logger.error(f"All retries exhausted: {e}")
                return {
                    "design": None,
                    "status": "failed",
                    "error": str(e),
                    "agent": "d3_specialist",
                }
```

#### 5.2 Performance Optimization

**Action**: Cache D3 code templates, optimize data transformations

#### 5.3 Accessibility Audit

**Action**: Ensure ARIA labels, keyboard navigation, screen reader support

**Duration**: 5-8 hours

---

## Rollout Strategy

### Step 1: Deploy to Development
```bash
# Replace agent
cp strand-results/active/D3_SPECIALIST_REFINED.py src/human_design/agents/d3_specialist.py

# Run tests
pytest tests/test_d3_specialist.py -v

# Commit if tests pass
git add src/human_design/agents/d3_specialist.py
git commit -m "refine: d3 specialist agent with tool registration and custom tools

- Add convert_bodygraph_to_d3_data @agent.tool
- Add generate_d3_visualization_code @agent.tool
- Add validate_svg_geometry @agent.tool
- Enhance system prompt with RawBodyGraph examples
- Improve dependency validation (auto-create directories)
- Add error handling to design_visualization()

Ref: strand-results/active/D3_SPECIALIST_REFINEMENT_ANALYSIS.md"
```

### Step 2: Integration Testing
```bash
# Test with real bodygraph
python -c "
from human_design.agents.d3_specialist import D3SpecialistAgent, D3SpecialistConfig
from human_design.models.bodygraph import calculate_bodygraph
from human_design.models.core import BirthInfo

# Calculate test bodygraph
birth_info = BirthInfo(date='1990-01-15', time='09:13', location='Albuquerque, NM')
bodygraph = calculate_bodygraph(birth_info)

# Test agent
agent = D3SpecialistAgent(D3SpecialistConfig(workspace_root=Path.cwd()))
result = await agent.design_visualization('test', {'bodygraph': bodygraph.dict()})
print(result)
"
```

### Step 3: Document & Deploy
```bash
# Update docs
vim docs/agents/d3_specialist_guide.md

# Tag release
git tag -a agent/d3-specialist/v2.0 -m "Refined d3 specialist with tool integration"
git push --tags
```

---

## Success Criteria

### HIGH Priority (Must Have - Week 1)
- ✅ Tool registration working (dodo shared tools)
- ✅ Custom @agent.tool methods functional
- ✅ System prompt has RawBodyGraph examples
- ✅ Dependency validation improved
- ✅ Unit tests passing
- ✅ Integration test passing

### MEDIUM Priority (Should Have - Week 2)
- ⏳ Actual SVG geometry from 64keys.com
- ⏳ Complete documentation (README, usage guide)
- ⏳ Channel path extraction
- ⏳ Center shape definitions

### LOW Priority (Nice to Have - Week 3+)
- ⏳ Error handling with retries
- ⏳ Performance optimization
- ⏳ Accessibility audit
- ⏳ Example notebooks

---

## Risks & Mitigation

### Risk 1: dodo Tool Registration Fails
**Mitigation**: Tool imports are isolated; agent works without them (degraded mode)

### Risk 2: SVG Geometry Extraction Takes Longer Than Expected
**Mitigation**: Use placeholder positions initially; iterate in Phase 4

### Risk 3: D3 Code Generation Quality
**Mitigation**: Start with templates, refine iteratively based on testing

---

## Timeline Summary

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 1: Core Refinements | 2-3 hours | ✅ Ready to implement |
| Phase 2: Integration Testing | 3-4 hours | ⏳ Depends on Phase 1 |
| Phase 3: Documentation | 2-3 hours | ⏳ Parallel with Phase 2 |
| Phase 4: SVG Geometry | 4-6 hours | ⏳ Week 2 |
| Phase 5: Hardening | 5-8 hours | ⏳ Week 3+ |
| **Total** | **1-2 days (HIGH)** | **3-5 days (complete)** |

---

## Next Steps

1. **Immediate (Day 1 AM)**:
   - Replace d3_specialist.py with refined version
   - Uncomment tool registration
   - Run initial tests

2. **Day 1 PM**:
   - Complete integration tests
   - Update config YAML
   - Start documentation

3. **Day 2**:
   - Finish documentation
   - Begin SVG geometry extraction
   - Deploy to development

4. **Week 2+**:
   - Complete geometry research
   - Production hardening
   - Accessibility audit

---

## Contact & Support

**Questions**: Refer to `D3_SPECIALIST_REFINEMENT_ANALYSIS.md` for detailed rationale

**Issues**: Create GitHub issue tagged `agent:d3_specialist`, `priority:high`

**Feedback**: After implementation, run `/dodo:postmortem` to capture learnings
