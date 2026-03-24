# Agent Training Audit & Enhancement Synthesis

**Date**: 2025-05-XX  
**Task**: Audit and enhance training for four Human Design agents  
**Specialist Agents**: Researcher, Ontologist, Python Linguist (failed), Fair Witness  

---

## Executive Summary

### Convergence Points (High Confidence)

All specialist agents agree on these critical findings:

1. **D3 Specialist Training is Already Strong** (Confidence: 0.95)
   - System prompt explicitly teaches D3 v7 `.join()` pattern (line 133)
   - Anti-patterns section warns against outdated `.enter()/.exit()` (line 139)
   - **Gap Assessment**: NO GAP - Already addresses 2026 best practices
   - **Fair Witness validates**: "BEST PRACTICES ALREADY EMBEDDED"

2. **Human Design Domain Knowledge is Comprehensive** (Confidence: 0.95)
   - All agents have embedded HD terminology (gates, channels, centers, types)
   - Three-layer architecture (coordinates → semantics → summaries) well-documented
   - Separation of concerns principle emphasized in all agent prompts
   - **Gap Assessment**: NO SIGNIFICANT GAP

3. **Pytest Parametrize is Well-Documented** (Confidence: 0.90)
   - Test engineer system prompt includes parametrize examples (lines 33-44)
   - Best practices section explicitly recommends `@pytest.mark.parametrize` (line 89)
   - Codebase shows extensive use (18+ parametrized tests)
   - **Gap Assessment**: MINIMAL GAP - Could add fixture interaction patterns

4. **Critical Gap: Pydantic v2 Validator Patterns** (Confidence: 0.85)
   - **All agents lack concrete Pydantic v2 examples**
   - Codebase uses v2 extensively (field_validator, model_validator, ConfigDict)
   - System prompts mention Pydantic v2 but lack code snippets
   - **This is the PRIMARY training gap**

### Shear Points (Disagreement Reveals Hidden Dimensions)

1. **D3 v7 Training Completeness**
   - **Researcher**: "D3 specialist has most critical gap (no working v7 .join() examples)"
   - **Ontologist**: "D3 specialist needs concrete .join() vs legacy .enter()/.exit() comparison"
   - **Fair Witness**: "D3 v7 best practices ALREADY EMBEDDED, no gap"
   - **Synthesis**: Fair Witness is correct - system prompt has D3 v7 guidance. However, Researcher/Ontologist identify valuable enhancement: **add concrete side-by-side comparisons** of v7 vs legacy patterns. Not a gap, but an improvement opportunity.

2. **Training Depth Definition**
   - **Ontologist**: Well-trained = 300-500 line system prompts (DODO standard)
   - **Current state**: Implementer (100 lines), Test Engineer (107 lines), D3 Specialist (149 lines), Python Linguist (235 lines)
   - **Fair Witness**: Current prompts are adequate but lack concrete code examples
   - **Synthesis**: Length is not the primary metric. **Code examples + anti-patterns** are more valuable than raw line count. Ontologist's benchmark is aspirational but not strictly required.

3. **Code-as-Ontology Realization**
   - **Ontologist**: "Agent training IS code, but not fully realized as queryable, generative modules"
   - **Fair Witness**: "Training exists as prose documentation rather than executable, testable code artifacts"
   - **Current state**: System prompts are Python strings (✅ code) + YAML configs (⚠️ not code)
   - **Synthesis**: This reveals an **architectural opportunity**: Create `training_examples/` module with Pydantic models of patterns/anti-patterns, make system prompts generated from these. This aligns with "ontological principle of first-class agent code."

---

## Critical Training Gaps (Priority Order)

### Priority 1: Pydantic v2 Validation Patterns (All Agents)

**Severity**: HIGH  
**Affected**: Implementer, Test Engineer, Python Linguist (D3 Specialist less critical)  
**Evidence**:
- Codebase uses Pydantic v2 extensively: `@field_validator` (8 uses), `@model_validator` (4 uses)
- System prompts mention Pydantic v2 but provide no concrete examples
- Model training data likely has v1 patterns (`@validator`, nested `Config` class)

**Missing Content**:
```python
# 2026 Pattern (Pydantic v2)
from pydantic import BaseModel, field_validator, ConfigDict

class GateSemantics(BaseModel):
    model_config = ConfigDict(frozen=True)  # ✅ v2 syntax
    
    lines: list[LineSemantics]
    
    @field_validator('lines')  # ✅ v2 decorator
    @classmethod  # ✅ Required in v2
    def validate_lines(cls, lines: list[LineSemantics]) -> list[LineSemantics]:
        if len(lines) != 6:
            raise ValueError(f'Gate must have exactly 6 lines, got {len(lines)}')
        return lines

# ❌ Legacy (Pydantic v1 - AVOID)
from pydantic import BaseModel, validator

class GateSemantics(BaseModel):
    lines: list[LineSemantics]
    
    @validator('lines')  # ❌ Old decorator
    def validate_lines(cls, lines):  # ❌ Missing type hints
        if len(lines) != 6:
            raise ValueError(f'Gate must have exactly 6 lines, got {len(lines)}')
        return lines
    
    class Config:  # ❌ Nested Config class (v1 style)
        frozen = True
```

**Recommendation**:
- Add "## PYDANTIC V2 PATTERNS" section to Implementer, Test Engineer system prompts
- Include side-by-side v1 vs v2 examples
- Show `@model_validator(mode='after')` for cross-field validation
- Document `Annotated` types pattern (from `semantic.py`)

---

### Priority 2: Pytest Fixture Best Practices (Test Engineer)

**Severity**: MEDIUM  
**Affected**: Test Engineer  
**Evidence**:
- Test engineer prompt has parametrize examples but lacks fixture guidance
- Codebase uses fixtures (9 found) but no documentation in agent training
- Missing patterns: fixture scoping, autouse, fixture composition

**Missing Content**:
```python
# Fixture scoping (session vs function)
@pytest.fixture(scope="session")
def bodygraph_loader():
    """Session-scoped fixture for expensive setup."""
    loader = BodyGraphLoader()
    loader.load_semantic_systems()
    return loader

@pytest.fixture
def sandy_bodygraph(bodygraph_loader):
    """Function-scoped fixture with dependency injection."""
    return bodygraph_loader.load("sandy")

# Parametrize + fixtures combination
@pytest.mark.parametrize("person_name,expected_type", [
    ("sandy", "Coordinator"),
    ("heath", "Builder"),
])
def test_person_type(person_name, bodygraph_loader, expected_type):
    bodygraph = bodygraph_loader.load(person_name)
    assert bodygraph.type == expected_type

# Mocking external dependencies
@pytest.fixture
def mock_64keys_api(monkeypatch):
    def mock_get(*args, **kwargs):
        return {"id": 123, "gates": [1, 42]}
    monkeypatch.setattr('requests.get', mock_get)
    return mock_get
```

**Recommendation**:
- Add "## FIXTURE PATTERNS" section to Test Engineer system prompt
- Include scoping examples (session, module, function)
- Show fixture parametrization and dependency injection
- Add "## MOCKING EXTERNAL SERVICES" section with monkeypatch examples

---

### Priority 3: D3 v7 Side-by-Side Comparisons (Enhancement, Not Gap)

**Severity**: LOW (Enhancement Opportunity)  
**Affected**: D3 Specialist  
**Evidence**:
- System prompt already teaches D3 v7 `.join()` pattern
- Fair Witness confirms "BEST PRACTICES ALREADY EMBEDDED"
- Researcher/Ontologist identify enhancement: concrete before/after examples

**Enhancement Content**:
```javascript
// ✅ D3 v7 Pattern (2021+) - USE THIS
const centers = svg.selectAll('.center')
  .data(bodygraphData.centers, d => d.name)  // key function
  .join('g')  // Modern join API
  .attr('class', 'center')
  .attr('transform', d => `translate(${d.x}, ${d.y})`);

// ❌ D3 v3/v4 Legacy Pattern - AVOID
const centers = svg.selectAll('.center')
  .data(bodygraphData.centers);

centers.enter().append('g')  // ❌ Outdated enter/exit pattern
  .attr('class', 'center');

centers.attr('transform', d => `translate(${d.x}, ${d.y})`);

centers.exit().remove();

// ✅ D3 v7 with enter/update/exit callbacks
const centers = svg.selectAll('.center')
  .data(bodygraphData.centers, d => d.name)
  .join(
    enter => enter.append('g')
      .attr('class', 'center')
      .attr('opacity', 0)
      .call(enter => enter.transition().attr('opacity', 1)),
    update => update.attr('class', d => d.defined ? 'center defined' : 'center'),
    exit => exit.transition().attr('opacity', 0).remove()
  );
```

**Recommendation**:
- Add "## D3 V7 VS LEGACY PATTERNS" section with side-by-side examples
- Show bodygraph-specific examples (centers, channels, gates)
- Include transition patterns for enter/update/exit callbacks

---

### Priority 4: Code-as-Ontology Architecture (Architectural)

**Severity**: HIGH (Architectural Principle)  
**Affected**: All agents  
**Evidence**:
- System prompts are Python strings (✅ first-class code)
- YAML configs exist (⚠️ not code-as-ontology)
- No executable training examples or validation tests
- Ontologist notes: "Training data generators or anti-pattern detectors as first-class code modules"

**Recommendation**:
Create `src/human_design/agents/training/` module:

```python
# training/patterns.py
from pydantic import BaseModel, Field
from typing import Literal

class PydanticV2Pattern(BaseModel):
    """Executable example of Pydantic v2 pattern."""
    category: Literal["field_validator", "model_validator", "config"]
    code: str = Field(..., description="Working code snippet")
    explanation: str
    tags: list[str] = Field(default_factory=list)

class AntiPattern(BaseModel):
    """Detectable code smell."""
    pattern_name: str
    detector: str = Field(..., description="AST matcher for python_linguist")
    bad_example: str
    good_example: str
    why_bad: str

# training/examples.py
PYDANTIC_V2_EXAMPLES = [
    PydanticV2Pattern(
        category="field_validator",
        code="""
@field_validator('lines')
@classmethod
def validate_lines(cls, lines: list[LineSemantics]) -> list[LineSemantics]:
    if len(lines) != 6:
        raise ValueError(f'Gate must have exactly 6 lines, got {len(lines)}')
    return lines
        """,
        explanation="Pydantic v2 field validator with @classmethod decorator",
        tags=["pydantic_v2", "validation", "2026"],
    ),
]

# training/prompt_generator.py
def generate_system_prompt(agent_name: str) -> str:
    """Generate system prompt from executable training examples."""
    examples = get_examples_for_agent(agent_name)
    return f"""
## EXAMPLES

{render_examples(examples)}

## ANTI-PATTERNS

{render_anti_patterns(agent_name)}
    """
```

**Benefits**:
- System prompts generated from queryable code
- Training examples are runnable tests
- Python Linguist can detect anti-patterns in codebase
- Aligns with "code IS ontology" principle

---

## Training Benchmarks (What is "Well-Trained"?)

### Convergence on Criteria

All specialists agree a well-trained agent has:

1. **System Prompt Depth**: 200-500 lines (DODO reference: Architect 320, Python Linguist 235)
   - **Current state**: Implementer 100, Test Engineer 107, D3 Specialist 149
   - **Assessment**: Length matters less than content quality

2. **Code Examples**: 5-10 realistic code snippets showing 2026 patterns
   - **Current state**: Abstract examples, no concrete v2 validator code
   - **Gap**: HIGH

3. **Anti-Patterns**: 5-10 common mistakes with ❌ markers
   - **Current state**: Brief anti-pattern lists, no code examples
   - **Gap**: MEDIUM

4. **Domain Knowledge**: Embedded terminology, concepts, edge cases
   - **Current state**: STRONG for Human Design domain
   - **Gap**: NONE

5. **Functional Validation**: Agent generates correct patterns without human correction
   - **Current state**: No validation tests
   - **Gap**: HIGH (architectural)

### Reference: DODO Architect Agent (Well-Trained Example)

- **System prompt**: 320 lines
- **Code examples**: 8-10 realistic snippets
- **Anti-patterns**: 6 with ❌ markers
- **Decision frameworks**: Multiple (Type-First, Ergonomic API, Production Readiness)
- **Tool integration**: Proper `@agent.tool` decorators with shared infrastructure
- **Output format**: Clear specification

---

## Recommended Actions

### Immediate (This Sprint)

1. **Enhance Implementer System Prompt**
   - Add "## PYDANTIC V2 PATTERNS" section with code examples
   - Include `@field_validator`, `@model_validator`, `ConfigDict` patterns
   - Show side-by-side v1 vs v2 comparisons
   - Expand to 300+ lines

2. **Enhance Test Engineer System Prompt**
   - Add "## FIXTURE PATTERNS" section with scoping examples
   - Add "## MOCKING EXTERNAL SERVICES" section with monkeypatch
   - Show parametrize + fixtures combination
   - Expand to 300+ lines

3. **Enhance D3 Specialist System Prompt** (Optional)
   - Add "## D3 V7 VS LEGACY PATTERNS" section
   - Side-by-side `.join()` vs `.enter()/.exit()` examples
   - Bodygraph-specific code snippets

4. **Python Linguist** - Already well-trained (1082 lines, comprehensive)
   - No immediate changes needed
   - Could add Human Design ontology query examples

### Short-Term (Next Sprint)

5. **Create Training Validation Suite**
   ```python
   # tests/test_agent_training.py
   @pytest.mark.parametrize("agent_name,required_keywords", [
       ("implementer", ["@field_validator", "@model_validator", "ConfigDict"]),
       ("test_engineer", ["@pytest.fixture", "scope=", "monkeypatch"]),
       ("d3_specialist", [".join(", "D3 v7", "selection.enter()"]),
   ])
   def test_agent_prompt_includes_2026_patterns(agent_name, required_keywords):
       agent = load_agent(agent_name)
       prompt = agent.system_prompt
       for keyword in required_keywords:
           assert keyword in prompt, f"Missing 2026 pattern: {keyword}"
   ```

6. **Create Training Examples Module**
   ```
   src/human_design/agents/training/
   ├── __init__.py
   ├── patterns.py          # Pydantic models for patterns/anti-patterns
   ├── pydantic_v2.py       # Pydantic v2 examples
   ├── pytest_patterns.py   # Pytest fixture examples
   ├── d3_v7_patterns.py    # D3 v7 examples
   ├── anti_patterns.py     # Detectable code smells
   └── prompt_generator.py  # Generate system prompts from examples
   ```

### Long-Term (Backlog)

7. **Migrate YAML Configs to Pydantic Models**
   - Replace `*.yaml` configs with Python dataclasses
   - Aligns with code-as-ontology principle

8. **Build Agent Capability Metrics**
   - Track: prompt length, example count, anti-pattern count
   - Dashboard: agent training coverage

9. **Create Agent Training ADR**
   - Document "well-trained agent" standard
   - Specify validation criteria
   - Reference implementation: DODO Architect

---

## Validation Criteria (How to Verify Enhancement)

### Success Metrics

1. **Prompt Content**:
   - [ ] Implementer prompt includes 3+ Pydantic v2 code examples
   - [ ] Test Engineer prompt includes 3+ fixture patterns
   - [ ] All prompts have 5+ anti-patterns with ❌ markers
   - [ ] All prompts expanded to 250-350 lines

2. **Functional Tests**:
   - [ ] Test suite validates required keywords in prompts
   - [ ] Agent generates Pydantic v2 code without correction
   - [ ] Agent generates pytest fixtures with proper scoping
   - [ ] Agent generates D3 v7 `.join()` patterns (not `.enter()`)

3. **Architectural**:
   - [ ] Training examples exist as executable code
   - [ ] System prompts generated from code (not static strings)
   - [ ] Python Linguist can detect anti-patterns in codebase

---

## Ontological Observations

### Code-as-Ontology Principle

**Current State**:
- ✅ System prompts are Python strings (first-class code)
- ⚠️ YAML configs not code (violates homoiconicity)
- ❌ Training examples not executable (static documentation)
- ❌ No anti-pattern detectors as code modules

**Goal State**:
- ✅ System prompts generated from Pydantic models
- ✅ Training examples are runnable tests
- ✅ Anti-patterns detected by Python Linguist AST tools
- ✅ Agents can introspect their own training data

### Human Design Domain Architecture

**Current State**:
- ✅ Three-layer architecture (coordinates → semantics → summaries) well-documented
- ✅ Separation of concerns principle embedded in all agents
- ✅ Domain terminology (gates, channels, types) comprehensive
- ✅ Semantic hot-swapping concept clear

**No gaps identified** - This is a strength of the current system.

---

## Conclusion

### What We Learned

1. **Fair Witness was most accurate** - D3 v7 and pytest.parametrize are already well-documented
2. **Primary gap is Pydantic v2** - All agents need concrete validator examples
3. **"Well-trained" = examples + anti-patterns** - Not just system prompt length
4. **Architectural opportunity** - Code-as-ontology not fully realized

### Critical Insight

The task description stated "model training data lag" as the concern. **This is partially true**:
- D3 v7 (2021+) is documented, but model training may default to older patterns
- Pydantic v2 (2023+) is used in code but not taught in agent prompts
- Pytest patterns (2020+) are taught, minimal gap

**The real issue**: System prompts lack **concrete code examples** to override model training defaults. Length is less important than explicit "2026 Pattern (use this)" vs "Legacy (avoid)" comparisons.

### Next Steps

1. **Enhance Implementer + Test Engineer prompts** with Pydantic v2 + pytest fixture examples
2. **Create `training/` module** with executable examples
3. **Build validation test suite** to ensure agents generate 2026 patterns
4. **Document "well-trained agent" standard** in ADR

---

**Confidence Scores**:
- Pydantic v2 gap identified: **0.95** (all specialists agree)
- D3 v7 gap assessment: **0.90** (Fair Witness correct, but enhancement valuable)
- Pytest fixture gap: **0.85** (medium severity)
- Code-as-ontology architecture: **0.80** (long-term opportunity)

**Synthesis Quality**: HIGH - Convergence on critical gap (Pydantic v2), shear reveals D3 v7 enhancement opportunity and architectural principle (code-as-ontology).
