# Actionable Recommendations: Python-First Agent Training (Iteration 3)

**Date**: 2025-01-XX  
**Priority**: CRITICAL → LOW (ordered by impact)  
**Total Estimated Effort**: 6 hours to reach A+ grade

---

## CRITICAL (Fix Immediately - 15 minutes)

### 1. Fix Config Class Inconsistency

**Problem**: Agents teach Pydantic v2 `model_config = ConfigDict()` but use legacy v1 `class Config:` in their own code.

**This is a "do as I say, not as I do" anti-pattern that undermines training credibility.**

**Impact**: 
- Grade: C → A+ (consistency)
- Confidence: High (0.95)
- Developer confusion
- Contradicts explicit training

**Solution**:

Replace this pattern:
```python
class ImplementerConfig(BaseModel):
    workspace_root: Path = Field(...)
    model: str = Field(default="claude-sonnet-4-5-20250929")
    
    class Config:  # ❌ LEGACY
        arbitrary_types_allowed = True
```

With this pattern:
```python
class ImplementerConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)  # ✅ CORRECT
    
    workspace_root: Path = Field(...)
    model: str = Field(default="claude-sonnet-4-5-20250929")
```

**Files to modify**:
1. `src/human_design/agents/implementer.py` (lines 340-341)
2. `src/human_design/agents/test_engineer.py` (lines 295-296)
3. `src/human_design/agents/d3_specialist.py` (lines 159-160)

**Steps**:
```bash
# 1. Edit implementer.py
# Replace lines 340-341:
#     class Config:
#         arbitrary_types_allowed = True
# With:
#     model_config = ConfigDict(arbitrary_types_allowed=True)

# 2. Add import if not present:
from pydantic import BaseModel, Field, ConfigDict

# 3. Repeat for test_engineer.py and d3_specialist.py

# 4. Verify with mypy:
mypy src/human_design/agents/

# 5. Run tests:
pytest tests/
```

**Validation**:
- [ ] All 3 Config classes use `model_config = ConfigDict()`
- [ ] No `class Config:` remains in agent modules
- [ ] mypy passes
- [ ] Consistency audit shows A+ grade

**Effort**: 5 minutes per file = 15 minutes total  
**Blocked by**: Nothing  
**Blocks**: Credibility of training system

---

## HIGH PRIORITY (Do This Week - 2 hours)

### 2. Run Validation Tests on Training Effectiveness

**Problem**: Training quality unverified - need empirical evidence agents learned v2 patterns.

**Impact**:
- Confidence in training effectiveness
- Early detection of gaps
- Validation of iteration 2 additions

**Tests to Run**:

#### Test 1: Pydantic v2 Code Generation
```bash
# Prompt implementer agent:
"Generate a Pydantic v2 model for a Human Design channel with:
- Field validators for gate pair validation (gates 1-64)
- Model validator checking gate pair is in valid channels list
- ConfigDict with frozen=True
- Type hints on all validators
- @classmethod decorator on field validators"

# Success criteria:
# ✅ Uses @field_validator (not @validator)
# ✅ Uses @model_validator(mode='after') (not @root_validator)
# ✅ Includes model_config = ConfigDict(frozen=True)
# ✅ All validators have type hints
# ✅ @classmethod present on field validators
# ❌ No Pydantic v1 patterns (@validator, nested Config class)
```

#### Test 2: @computed_field Understanding
```bash
# Prompt implementer agent:
"Generate a BodyGraph model with personality_gates and design_gates lists.
Add a computed field all_gates that returns the combined list.
Explain why @computed_field is needed instead of plain @property."

# Success criteria:
# ✅ Uses @computed_field + @property together
# ✅ Explains serialization behavior (included in model_dump())
# ✅ Shows side-by-side comparison with plain @property
# ❌ Does NOT use plain @property alone for serialized fields
```

#### Test 3: Semantic Separation Principle
```bash
# Prompt implementer agent:
"Explain why we separate coordinates from semantic interpretations in Human Design.
Provide code examples showing correct vs incorrect patterns."

# Success criteria:
# ✅ References hot-swappable semantic systems (64keys, Ra Traditional, Jolly Alchemy)
# ✅ Explains deterministic layer vs interpretive layer
# ✅ Shows ✅ CORRECT vs ❌ WRONG code patterns
# ✅ Mentions "never hardcode semantic content in coordinate layer"
# ✅ Demonstrates semantic adapter pattern
```

#### Test 4: pytest.mark.parametrize Mastery
```bash
# Prompt test_engineer agent:
"Create a parametrized test suite for gate number validation (1-64).
Test edge cases: 0, -1, 65, 64, 1.
Use pytest.param with id parameter for readable test names."

# Success criteria:
# ✅ Uses @pytest.mark.parametrize
# ✅ Tests valid cases (1, 64)
# ✅ Tests invalid cases (0, -1, 65)
# ✅ Uses pytest.param(id='...') for test naming
# ✅ Type hints on test parameters
# ✅ Single test function handles all cases
```

**Execution**:
```bash
# Create validation script:
cat > tests/validate_agent_training.py << 'EOF'
import pytest
from human_design.agents import ImplementerAgent, TestEngineerAgent

# Test prompts here...
EOF

# Run validation:
pytest tests/validate_agent_training.py -v
```

**Effort**: 30 minutes to write tests + 1 hour to run and analyze  
**Blocked by**: Config class fix (should fix first for clean results)  
**Blocks**: Confidence in deployment

---

### 3. Complete Tool Registration for All Agents

**Problem**: 3 agents have TODO comments for tool registration, limiting capabilities.

**Current State**:
- ✅ Python Linguist: Has working tool integration
- ❌ Implementer: TODO comments (line 376)
- ❌ Test Engineer: TODO comments (line 331)
- ❌ D3 Specialist: TODO comments (line 195)

**Impact**:
- Agents cannot read/write files
- Agents cannot search codebase
- Agents cannot perform git operations
- Grade: B → A (tool integration)

**Solution**: Follow python_linguist.py pattern

**Code to add to implementer.py** (around line 376):
```python
from ..agent_tools import (
    register_filesystem_tools,
    register_code_search_tools,
    FileSystemDeps,
    CodeSearchDeps,
)

def create_implementer_agent(deps: ImplementerDeps, model: str | None = None) -> Agent:
    """Create an Implementer agent with registered tools."""
    agent = Agent(
        model=model or "claude-sonnet-4-20250514",
        system_prompt=IMPLEMENTER_SYSTEM_PROMPT,
        deps_type=ImplementerDeps,
    )
    
    # Register shared tools
    register_filesystem_tools(agent, deps.workspace_root)
    register_code_search_tools(agent, deps.workspace_root)
    
    return agent
```

**Files to modify**:
1. `src/human_design/agents/implementer.py`
2. `src/human_design/agents/test_engineer.py`
3. `src/human_design/agents/d3_specialist.py`

**Steps**:
```bash
# 1. Copy pattern from python_linguist.py (lines 26-31)
# 2. Add imports to each agent
# 3. Add register_*_tools calls to create_agent functions
# 4. Remove TODO comments
# 5. Test tool registration:
pytest tests/test_agent_tools.py -v
```

**Validation**:
- [ ] All 3 agents import agent_tools
- [ ] All create_agent functions call register_*_tools
- [ ] No TODO comments remain
- [ ] Agents can read files when run
- [ ] Agents can search code when run

**Effort**: 30 minutes per agent = 1.5 hours total  
**Blocked by**: Nothing  
**Blocks**: Practical agent usage

---

## MEDIUM PRIORITY (This Month - 3 hours)

### 4. Document DODO Agent Architecture Pattern

**Problem**: "DODO agent architecture pattern" referenced throughout but not defined.

**Impact**:
- Onboarding confusion
- Architectural decisions unclear
- Pattern replication uncertain

**What needs documentation**:
- What is DODO agent architecture?
- Why Python-first vs JSON-based agent loading?
- Pattern structure (system prompt, config, deps, factory, interface)
- Benefits (version control, type safety, IDE support, testing)
- When to use this pattern vs alternatives
- Comparison to other agent architectures

**Solution**: Create ADR

**File to create**: `docs/ADRs/ADR-XXX-DODO-agent-architecture.md`

**Template**:
```markdown
# ADR-XXX: DODO Agent Architecture Pattern

## Status
Accepted

## Context
Multi-agent systems need consistent architecture for maintainability and type safety.

## Decision
Adopt DODO agent architecture pattern:

1. **Python-first definitions** (not JSON specs)
   - System prompts as Python string constants
   - Agents defined in .py modules
   - Version-controlled with code

2. **Pydantic v2 configuration**
   - Config classes extend BaseModel
   - Field annotations with Field()
   - model_config = ConfigDict() (not nested Config)

3. **Dataclass dependencies**
   - @dataclass for runtime dependencies
   - __post_init__ validation
   - Separate from configuration

4. **Factory functions**
   - create_agent() returns pydantic_ai.Agent
   - Takes deps and optional model
   - Registers tools

5. **High-level interfaces**
   - Wrapper classes for async task execution
   - Domain-specific method names
   - Type-safe results

## Consequences

**Benefits**:
- System prompts version-controlled in code
- Type-safe configuration with Pydantic validation
- IDE support (autocomplete, type checking, jump-to-definition)
- Direct testing (import and test agents)
- Integration with DODO strand execution

**Drawbacks**:
- More verbose than JSON specs
- Python knowledge required for configuration
- Agent definitions tied to code deployment

## Alternatives Considered

1. **JSON-based agent loading**: Rejected due to lack of type safety, version control issues
2. **YAML-based configs**: Rejected due to no validation, runtime errors
3. **Hardcoded agents**: Rejected due to inflexibility

## Examples

See: implementer.py, test_engineer.py, d3_specialist.py, python_linguist.py
```

**Steps**:
```bash
# 1. Create ADR file
touch docs/ADRs/ADR-XXX-DODO-agent-architecture.md

# 2. Fill in template with details from synthesis
# 3. Add diagrams showing pattern structure
# 4. Link from main README.md
# 5. Review with team
```

**Effort**: 2 hours (writing + review)  
**Blocked by**: Nothing  
**Blocks**: Architectural understanding

---

### 5. Create Automated Training Validation Suite

**Problem**: Training quality verified manually, not continuously.

**Impact**:
- Training drift undetected
- Regressions in agent output quality
- Manual validation time-consuming

**Solution**: Create `tests/test_agent_training.py`

**Test Cases**:

```python
import pytest
from human_design.agents import ImplementerAgent, TestEngineerAgent

class TestImplementerTraining:
    """Validate Implementer agent learned Pydantic v2 patterns."""
    
    @pytest.mark.parametrize("prompt,expected_keywords", [
        (
            "Generate a Pydantic v2 model with field validator",
            ["@field_validator", "@classmethod", "cls,", "->"],
        ),
        (
            "Create a model with ConfigDict",
            ["model_config", "ConfigDict("],
        ),
        (
            "Add a computed field to a model",
            ["@computed_field", "@property"],
        ),
    ])
    async def test_pydantic_v2_patterns(self, prompt, expected_keywords):
        """Verify agent generates v2 patterns."""
        agent = ImplementerAgent(workspace_root=Path.cwd())
        result = await agent.implement(task=prompt, context={})
        
        code = result.get("code", "")
        for keyword in expected_keywords:
            assert keyword in code, f"Missing {keyword} in generated code"
        
        # Check no legacy patterns
        assert "@validator" not in code, "Legacy @validator found"
        assert "class Config:" not in code, "Legacy nested Config found"
    
    async def test_semantic_separation_understanding(self):
        """Verify agent understands HD architectural principle."""
        agent = ImplementerAgent(workspace_root=Path.cwd())
        result = await agent.implement(
            task="Explain semantic separation principle",
            context={}
        )
        
        explanation = result.get("explanation", "")
        required_concepts = [
            "hot-swappable",
            "semantic systems",
            "coordinates",
            "deterministic",
        ]
        for concept in required_concepts:
            assert concept.lower() in explanation.lower()

class TestTestEngineerTraining:
    """Validate Test Engineer learned pytest patterns."""
    
    async def test_parametrize_with_ids(self):
        """Verify agent uses pytest.param with id parameter."""
        agent = TestEngineerAgent(workspace_root=Path.cwd())
        result = await agent.create_tests(
            task="Create parametrized test for gate validation",
            context={}
        )
        
        code = result.get("code", "")
        assert "@pytest.mark.parametrize" in code
        assert "pytest.param(" in code
        assert "id=" in code
```

**Steps**:
```bash
# 1. Create test file
cat > tests/test_agent_training.py << 'EOF'
# Test cases here...
EOF

# 2. Add to CI/CD:
# .github/workflows/test.yml:
#   - name: Validate agent training
#     run: pytest tests/test_agent_training.py -v

# 3. Run locally:
pytest tests/test_agent_training.py -v
```

**Effort**: 1 hour to write tests + 30 minutes to integrate CI/CD  
**Blocked by**: Tool registration (agents need to be functional)  
**Blocks**: Continuous quality assurance

---

## LOW PRIORITY (Nice to Have - Future)

### 6. Add Fixture Composition to Test Engineer Training

**Problem**: Test Engineer training lacks fixture-depending-on-fixture pattern.

**Current State**: Training shows isolated fixtures (scope, factories, autouse)  
**Missing**: Fixtures that depend on other fixtures

**Impact**: Grade A- → A (test engineer)

**Solution**: Add 10-15 lines to test_engineer.py system prompt

**Content to add** (insert around line 185):
```python
**Fixture Composition** (fixtures depending on fixtures):

```python
# ✅ CORRECT (fixture calls another fixture)
@pytest.fixture
def sample_birth_data():
    return {'date': '1990-01-15', 'time': '14:30', 'location': 'NYC'}

@pytest.fixture
def sample_bodygraph(sample_birth_data):
    '''Fixture depends on another fixture - pytest injects it.'''
    return calculate_bodygraph(**sample_birth_data)

@pytest.fixture
def sample_semantic_summary(sample_bodygraph):
    '''Multi-level fixture composition.'''
    return create_semantic_summary(sample_bodygraph, system='64keys')

def test_bodygraph_has_gates(sample_bodygraph):
    assert len(sample_bodygraph.gates) > 0

def test_summary_includes_type(sample_semantic_summary):
    assert sample_semantic_summary.type in ['Initiator', 'Builder', ...]
```

**Why**: Fixture composition enables modular test setup and reduces duplication.
```

**Effort**: 30 minutes  
**Blocked by**: Nothing  
**Blocks**: A grade for test engineer

---

### 7. Create Training Coverage Metric Dashboard

**Problem**: Training quality measured by line count, not coverage of codebase patterns.

**Impact**: 
- False confidence (many lines but missing patterns)
- Gaps invisible until manual audit
- No quantitative quality metric

**Solution**: Automated pattern coverage analysis

**Approach**:
```python
# scripts/calculate_training_coverage.py

import ast
from pathlib import Path
from collections import Counter

def find_patterns_in_codebase(src_dir: Path) -> set[str]:
    """Scan codebase for Pydantic/pytest patterns."""
    patterns = set()
    
    for py_file in src_dir.rglob("*.py"):
        source = py_file.read_text()
        tree = ast.parse(source)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if node.id in ["field_validator", "model_validator", "computed_field"]:
                    patterns.add(node.id)
            if isinstance(node, ast.Attribute):
                if node.attr in ["model_dump", "model_dump_json", "model_validate"]:
                    patterns.add(node.attr)
    
    return patterns

def find_patterns_in_training(agent_file: Path) -> set[str]:
    """Scan system prompt for pattern examples."""
    content = agent_file.read_text()
    
    patterns = set()
    if "@field_validator" in content:
        patterns.add("field_validator")
    if "@model_validator" in content:
        patterns.add("model_validator")
    if "@computed_field" in content:
        patterns.add("computed_field")
    if "model_dump()" in content:
        patterns.add("model_dump")
    # ... etc
    
    return patterns

def calculate_coverage(codebase_patterns: set, training_patterns: set) -> float:
    """Coverage = patterns in training / patterns in codebase."""
    if not codebase_patterns:
        return 1.0
    return len(training_patterns & codebase_patterns) / len(codebase_patterns)

# Run analysis:
codebase = find_patterns_in_codebase(Path("src/human_design"))
training = find_patterns_in_training(Path("src/human_design/agents/implementer.py"))
coverage = calculate_coverage(codebase, training)

print(f"Training coverage: {coverage:.1%}")
print(f"Missing patterns: {codebase - training}")
```

**Dashboard Output**:
```
Training Coverage Report
========================

Implementer Agent: 95% coverage
  ✅ field_validator (in codebase, in training)
  ✅ model_validator (in codebase, in training)
  ✅ computed_field (in codebase, in training)
  ✅ model_dump (in codebase, in training)
  ✅ ConfigDict (in codebase, in training)
  ❌ AfterValidator (in codebase, NOT in training)
  
Test Engineer Agent: 90% coverage
  ✅ pytest.mark.parametrize (in codebase, in training)
  ✅ pytest.param (in codebase, in training)
  ✅ fixture scopes (in codebase, in training)
  ❌ pytest-asyncio (in codebase, NOT in training)
```

**Effort**: 4-5 hours (script + dashboard + CI integration)  
**Blocked by**: Nothing  
**Blocks**: Quantitative quality metrics

---

## ARCHITECTURAL (Long-term - Months)

### 8. Implement Code-as-Ontology Training Architecture

**Problem**: Training is static text, not executable, self-maintaining code.

**Vision**: Training examples ARE executable tests that validate themselves.

**Approach**:
```python
# src/human_design/agents/training/pydantic_v2_patterns.py

from pydantic import BaseModel, field_validator, computed_field, ConfigDict
from typing import Annotated
from pydantic import Field

class TrainingExample(BaseModel):
    """Base class for training examples (executable, testable)."""
    
    pattern_name: str
    code_example: str
    explanation: str
    tags: list[str]
    
    def validate(self) -> bool:
        """Verify this example is valid code."""
        try:
            compile(self.code_example, '<string>', 'exec')
            return True
        except SyntaxError:
            return False

# Examples as executable code:
field_validator_example = TrainingExample(
    pattern_name="field_validator",
    code_example='''
from pydantic import BaseModel, field_validator

class GateSemantics(BaseModel):
    lines: list[LineSemantics]
    
    @field_validator('lines')
    @classmethod
    def validate_lines(cls, lines: list[LineSemantics]) -> list[LineSemantics]:
        if len(lines) != 6:
            raise ValueError(f'Gate must have exactly 6 lines, got {len(lines)}')
        return lines
    ''',
    explanation="Use @field_validator + @classmethod for field validation in Pydantic v2",
    tags=["pydantic", "v2", "validation"],
)

# Generate system prompt from examples:
def generate_system_prompt(examples: list[TrainingExample]) -> str:
    """Generate system prompt from training examples."""
    sections = []
    
    for example in examples:
        assert example.validate(), f"Invalid example: {example.pattern_name}"
        sections.append(f"**{example.pattern_name}**\n\n{example.explanation}\n\n```python\n{example.code_example}\n```")
    
    return "\n\n".join(sections)

# System prompt becomes generated artifact:
IMPLEMENTER_SYSTEM_PROMPT = generate_system_prompt([
    field_validator_example,
    model_validator_example,
    # ...
])
```

**Benefits**:
- Training examples are executable (can run as tests)
- System prompts generated from examples (single source of truth)
- Pattern changes auto-update training
- Examples validate themselves
- Code IS ontology (introspectable)

**Effort**: Weeks to months (architectural change)  
**Blocked by**: Nothing (can start incrementally)  
**Blocks**: Self-maintaining training system

---

## Summary: Path to A+ Grade

### Current Grade: A- (0.90 confidence)

**Blockers**:
1. Config class inconsistency (CRITICAL)
2. Tool registration incomplete (MEDIUM)
3. Training validation untested (HIGH)

### Path to A+ (6 hours total)

```
Week 1:
  Day 1 (30 min):
    ✅ Fix Config class inconsistency → A (consistency)
    ✅ Run validation tests → Confidence +0.05
  
  Day 2 (2 hours):
    ✅ Complete tool registration → A (capabilities)
    ✅ Create validation test suite → Continuous QA
  
  Week 2 (3 hours):
    ✅ Document DODO architecture → Clarity
    ✅ Add fixture composition → A (test engineer)
    
  Result: A+ grade achieved
```

### Metrics

| Action | Effort | Grade Impact | Confidence Impact |
|--------|--------|--------------|-------------------|
| Fix Config classes | 15 min | C → A+ (consistency) | +0.03 |
| Run validation tests | 1.5 hrs | Evidence of effectiveness | +0.05 |
| Complete tool registration | 1.5 hrs | B → A (capabilities) | +0.02 |
| Document DODO pattern | 2 hrs | Architectural clarity | N/A |
| Add fixture composition | 30 min | A- → A (test engineer) | N/A |

**Total to A+**: 6 hours  
**Final Grade**: A+ (0.95 confidence)

---

## Validation Checklist

After completing recommendations:

- [ ] All Config classes use `model_config = ConfigDict()`
- [ ] No `class Config:` in agent modules
- [ ] All agents have tool registration
- [ ] Validation tests pass (Pydantic v2, @computed_field, semantic separation)
- [ ] DODO architecture ADR exists
- [ ] Test engineer has fixture composition
- [ ] Training coverage metric available
- [ ] CI/CD runs training validation tests

**When all checked**: Training system is A+ quality, self-validating, and production-ready.
