# Actionable Agent Training Enhancements

**Date**: 2025-05-XX  
**Status**: Ready for Implementation  
**Priority**: HIGH (Pydantic v2), MEDIUM (pytest fixtures), LOW (D3 v7 examples)

---

## Quick Reference: What to Add to Each Agent

| Agent | Critical Addition | Lines to Add | Priority |
|-------|------------------|--------------|----------|
| **Implementer** | Pydantic v2 validator examples | 50-80 | **HIGH** |
| **Test Engineer** | pytest fixture patterns + mocking | 50-80 | **HIGH** |
| **D3 Specialist** | D3 v7 side-by-side comparisons | 30-50 | LOW |
| **Python Linguist** | No changes needed | 0 | N/A |

---

## 1. Implementer Agent Enhancement

**File**: `src/human_design/agents/implementer.py`  
**Current Lines**: 100 (system prompt ends line 100)  
**Target Lines**: 250-300  

### Add After Line 43 (Code Quality Standards section)

```python
## PYDANTIC V2 VALIDATION PATTERNS (2026 Best Practices)

**Field Validators** (validate individual fields):

```python
# ✅ 2026 Pattern (Pydantic v2)
from pydantic import BaseModel, field_validator

class GateSemantics(BaseModel):
    lines: list[LineSemantics]
    
    @field_validator('lines')  # v2 decorator
    @classmethod  # Required in v2
    def validate_lines(cls, lines: list[LineSemantics]) -> list[LineSemantics]:
        if len(lines) != 6:
            raise ValueError(f'Gate must have exactly 6 lines, got {len(lines)}')
        return lines

# ❌ LEGACY (Pydantic v1 - AVOID)
from pydantic import BaseModel, validator

class GateSemantics(BaseModel):
    lines: list[LineSemantics]
    
    @validator('lines')  # ❌ Old decorator
    def validate_lines(cls, lines):  # ❌ Missing type hints
        if len(lines) != 6:
            raise ValueError(f'Gate must have exactly 6 lines, got {len(lines)}')
        return lines
```

**Model Validators** (cross-field validation):

```python
# ✅ 2026 Pattern (Pydantic v2)
from pydantic import BaseModel, model_validator
from typing import Self

class BodyGraphInput(BaseModel):
    birth_date: date
    birth_time: time
    location: str
    
    @model_validator(mode='after')  # v2 syntax
    def validate_date_range(self) -> Self:
        if self.birth_date.year < 1900:
            raise ValueError('Birth date must be after 1900')
        return self

# ❌ LEGACY (Pydantic v1 - AVOID)
from pydantic import BaseModel, root_validator

class BodyGraphInput(BaseModel):
    birth_date: date
    birth_time: time
    location: str
    
    @root_validator  # ❌ Old decorator
    def validate_date_range(cls, values):
        if values['birth_date'].year < 1900:
            raise ValueError('Birth date must be after 1900')
        return values
```

**ConfigDict** (model configuration):

```python
# ✅ 2026 Pattern (Pydantic v2)
from pydantic import BaseModel, ConfigDict

class Person(BaseModel):
    model_config = ConfigDict(
        frozen=True,  # Immutable
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )
    
    name: str
    bodygraph: RawBodyGraph

# ❌ LEGACY (Pydantic v1 - AVOID)
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    bodygraph: RawBodyGraph
    
    class Config:  # ❌ Nested Config class
        frozen = True
        arbitrary_types_allowed = True
        validate_assignment = True
```

**Annotated Types** (reusable field constraints):

```python
# ✅ 2026 Pattern (Pydantic v2)
from typing import Annotated
from pydantic import Field, AfterValidator

def validate_gate_number(v: int) -> int:
    if not 1 <= v <= 64:
        raise ValueError(f'Gate number must be 1-64, got {v}')
    return v

GateNumber = Annotated[int, AfterValidator(validate_gate_number), Field(ge=1, le=64)]

class GateActivation(BaseModel):
    gate: GateNumber  # Validation automatically applied
    line: int
```

**When to Use Each**:
- `@field_validator`: Validate single field (gate numbers, line ranges)
- `@model_validator(mode='after')`: Cross-field validation (birth date consistency)
- `@model_validator(mode='before')`: Pre-processing raw input
- `Annotated` types: Reusable constraints across models
```

### Add After Line 93 (Anti-Patterns section)

```python
## COMMON PYDANTIC V2 MISTAKES

❌ Using `@validator` instead of `@field_validator`
❌ Forgetting `@classmethod` on field validators
❌ Using nested `class Config` instead of `model_config = ConfigDict(...)`
❌ Using `@root_validator` instead of `@model_validator(mode='after')`
❌ Missing `-> Self` return type on model validators
❌ Not importing from `pydantic` (e.g., `from pydantic_core import ...` instead)

## DOMAIN-SPECIFIC VALIDATION EXAMPLES

**Gate Number Validation**:
```python
@field_validator('gate_number')
@classmethod
def validate_gate(cls, v: int) -> int:
    if not 1 <= v <= 64:
        raise ValueError(f'Gate number must be 1-64, got {v}')
    return v
```

**Line Number Validation**:
```python
@field_validator('line_number')
@classmethod
def validate_line(cls, v: int) -> int:
    if v not in {1, 2, 3, 4, 5, 6}:
        raise ValueError(f'Line number must be 1-6, got {v}')
    return v
```

**Channel Formation Validation**:
```python
@model_validator(mode='after')
def validate_channel(self) -> Self:
    """Ensure channel has exactly two gates."""
    if len(self.gates) != 2:
        raise ValueError(f'Channel must have 2 gates, got {len(self.gates)}')
    return self
```
```

---

## 2. Test Engineer Agent Enhancement

**File**: `src/human_design/agents/test_engineer.py`  
**Current Lines**: 107 (system prompt ends line 107)  
**Target Lines**: 250-300  

### Add After Line 51 (Test Coverage Goals section)

```python
## PYTEST FIXTURE PATTERNS (2026 Best Practices)

**Fixture Scoping** (control setup/teardown frequency):

```python
# Session scope (once per test session)
@pytest.fixture(scope="session")
def semantic_loader():
    """Load semantic systems once for all tests."""
    loader = SemanticLoader()
    loader.load_all_systems()  # Expensive operation
    return loader

# Function scope (default - once per test function)
@pytest.fixture
def sandy_bodygraph():
    """Create fresh bodygraph for each test."""
    return RawBodyGraph(
        gates={42: 3, 53: 5},
        channels=["42-53"],
        defined_centers=["LIFEFORCE", "EMOTION"],
    )

# Module scope (once per test file)
@pytest.fixture(scope="module")
def database_connection():
    """Share database connection across all tests in file."""
    conn = connect_db()
    yield conn
    conn.close()
```

**Fixture Dependencies** (fixtures can use other fixtures):

```python
@pytest.fixture
def person_store(tmp_path):
    """Create temporary person storage."""
    store = PersonStore(storage_path=tmp_path)
    return store

@pytest.fixture
def sandy(person_store):
    """Create Sandy using person store."""
    person = Person(name="Sandy", birth_date=date(1990, 1, 1))
    person_store.save(person)
    return person

def test_person_retrieval(person_store, sandy):
    """Test uses both fixtures automatically."""
    retrieved = person_store.get("Sandy")
    assert retrieved.name == sandy.name
```

**Parametrize + Fixtures** (combine for powerful test matrices):

```python
@pytest.mark.parametrize("person_name", ["sandy", "heath", "morgan"])
def test_bodygraph_calculation(person_name, person_store):
    """Test multiple people using shared fixture."""
    person = person_store.get(person_name)
    bodygraph = calculate_bodygraph(person.birth_info)
    assert bodygraph is not None
    assert len(bodygraph.gates) > 0
```

**Autouse Fixtures** (automatic setup for all tests):

```python
@pytest.fixture(autouse=True)
def reset_semantic_cache():
    """Reset semantic cache before each test."""
    SemanticLoader.clear_cache()
    yield
    # Teardown runs after test
```

## MOCKING EXTERNAL DEPENDENCIES

**Monkeypatch** (pytest built-in mocking):

```python
def test_api_call_success(monkeypatch):
    """Mock 64keys API response."""
    def mock_get(*args, **kwargs):
        return MockResponse({"id": 123, "gates": [1, 42]})
    
    monkeypatch.setattr('requests.get', mock_get)
    
    result = fetch_person_from_64keys(123)
    assert result.gates == [1, 42]

def test_api_call_failure(monkeypatch):
    """Test API error handling."""
    def mock_get(*args, **kwargs):
        raise ConnectionError("API unavailable")
    
    monkeypatch.setattr('requests.get', mock_get)
    
    with pytest.raises(ConnectionError):
        fetch_person_from_64keys(123)
```

**Fixture-Based Mocking** (reusable mocks):

```python
@pytest.fixture
def mock_geocoding(monkeypatch):
    """Mock geocoding API for all tests."""
    def mock_geocode(location: str):
        return {"lat": 40.7128, "lon": -74.0060}  # New York
    
    monkeypatch.setattr('human_design.geocoding.geocode', mock_geocode)
    return mock_geocode

def test_location_parsing(mock_geocoding):
    """Test uses mocked geocoding automatically."""
    location = parse_location("New York, NY")
    assert location.latitude == 40.7128
```

**Pytest-Mock Plugin** (if installed):

```python
def test_api_call_with_mock(mocker):
    """Use pytest-mock for more powerful mocking."""
    mock_api = mocker.patch('human_design.api.fetch_person')
    mock_api.return_value = Person(name="Test", gates=[1, 42])
    
    result = get_person(123)
    
    assert result.name == "Test"
    mock_api.assert_called_once_with(123)
```

## FIXTURE BEST PRACTICES

✅ Use `scope="session"` for expensive one-time setup
✅ Use `scope="function"` (default) for test isolation
✅ Use `yield` for setup/teardown in single fixture
✅ Name fixtures descriptively (e.g., `sandy_bodygraph`, not `bg1`)
✅ Keep fixtures simple (one responsibility)
✅ Use `autouse=True` sparingly (only for global setup)

❌ Don't overuse `scope="session"` (breaks test isolation)
❌ Don't modify fixture data in tests (creates side effects)
❌ Don't create fixture dependencies >2 levels deep
❌ Don't use fixtures for simple constants (just use variables)
```

### Add After Line 100 (Testing Best Practices section)

```python
## COMMON PYTEST FIXTURE MISTAKES

❌ Using `scope="session"` with mutable data (tests contaminate each other)
❌ Forgetting `yield` in fixtures with teardown logic
❌ Hardcoding test data in fixtures (use parametrize instead)
❌ Mocking too broadly (breaks unrelated tests)
❌ Not cleaning up after fixtures (database connections, files)

## HUMAN DESIGN TEST SCENARIOS

**Test Fixture: Sample Bodygraphs**:
```python
@pytest.fixture
def sandy_bodygraph():
    return RawBodyGraph(
        gates={42: 3, 53: 5, 21: 2, 45: 1},
        channels=["42-53", "21-45"],
        defined_centers=["LIFEFORCE", "EMOTION", "WILLPOWER", "EXPRESSION"],
        type="Specialist",
        authority="Emotional",
    )

@pytest.fixture
def heath_bodygraph():
    return RawBodyGraph(
        gates={42: 4, 27: 3, 50: 2},
        channels=["42-27"],
        defined_centers=["LIFEFORCE", "DRIVE"],
        type="Builder",
        authority="Sacral",
    )

@pytest.mark.parametrize("person_fixture", ["sandy_bodygraph", "heath_bodygraph"])
def test_type_determination(person_fixture, request):
    bodygraph = request.getfixturevalue(person_fixture)
    assert bodygraph.type in ["Builder", "Specialist", "Coordinator", "Initiator", "Observer"]
```

**Test Interaction Charts**:
```python
def test_interaction_emergent_channels(sandy_bodygraph, heath_bodygraph):
    """Test that interaction creates emergent channels."""
    interaction = sandy_bodygraph + heath_bodygraph
    
    # Sandy has gate 42, Heath has gate 53 -> emergent channel 42-53
    assert "42-53" in interaction.emergent_channels
    
    # Both have gate 42 in different lines -> not emergent
    assert interaction.gates[42] == {3, 4}  # Sandy line 3, Heath line 4
```
```

---

## 3. D3 Specialist Agent Enhancement (Optional)

**File**: `src/human_design/agents/d3_specialist.py`  
**Current Lines**: 149 (system prompt ends line 149)  
**Target Lines**: 200-250  

### Add After Line 93 (Interactive Overlays section)

```python
## D3 V7 VS LEGACY PATTERNS (2021+ vs 2015 Patterns)

**Why This Matters**: D3 v7 (2021) introduced `.join()` to replace the verbose
`.enter()/.update()/.exit()` pattern. Model training data likely has legacy patterns,
so we explicitly teach v7 modern syntax.

**Basic Data Binding** (centers, channels, gates):

```javascript
// ✅ D3 v7 Pattern (2021+) - USE THIS
const centers = svg.selectAll('.center')
  .data(bodygraphData.centers, d => d.name)  // key function for object constancy
  .join('g')  // Modern join API (enter/update/exit handled automatically)
  .attr('class', 'center')
  .attr('transform', d => `translate(${d.x}, ${d.y})`);

// ❌ D3 v3/v4/v5 Legacy Pattern - AVOID
const centers = svg.selectAll('.center')
  .data(bodygraphData.centers);

const centerEnter = centers.enter().append('g')  // ❌ Verbose enter/exit pattern
  .attr('class', 'center');

centers.merge(centerEnter)  // ❌ Manual merge step
  .attr('transform', d => `translate(${d.x}, ${d.y})`);

centers.exit().remove();  // ❌ Manual exit handling
```

**With Transitions** (enter/update/exit callbacks):

```javascript
// ✅ D3 v7 Pattern with Fine-Grained Control
const centers = svg.selectAll('.center')
  .data(bodygraphData.centers, d => d.name)
  .join(
    // Enter: new elements
    enter => enter.append('g')
      .attr('class', 'center')
      .attr('opacity', 0)
      .attr('transform', d => `translate(${d.x}, ${d.y})`)
      .call(enter => enter.transition().duration(500).attr('opacity', 1)),
    
    // Update: existing elements
    update => update
      .attr('class', d => d.defined ? 'center defined' : 'center undefined')
      .call(update => update.transition().duration(300)
        .attr('transform', d => `translate(${d.x}, ${d.y})`)),
    
    // Exit: removed elements
    exit => exit
      .call(exit => exit.transition().duration(500)
        .attr('opacity', 0)
        .remove())
  );

// ❌ D3 v5 Legacy Pattern - AVOID
const centers = svg.selectAll('.center')
  .data(bodygraphData.centers, d => d.name);

const centerEnter = centers.enter().append('g')
  .attr('class', 'center')
  .attr('opacity', 0);

centerEnter.transition().duration(500).attr('opacity', 1);

centers.merge(centerEnter)
  .attr('class', d => d.defined ? 'center defined' : 'center undefined')
  .transition().duration(300)
  .attr('transform', d => `translate(${d.x}, ${d.y})`);

centers.exit()
  .transition().duration(500)
  .attr('opacity', 0)
  .remove();
```

**Bodygraph-Specific Example** (channels as paths):

```javascript
// ✅ D3 v7 Pattern for Channels
const channels = svg.selectAll('.channel')
  .data(bodygraphData.channels, d => d.id)  // Use channel ID as key
  .join('path')
  .attr('class', d => d.defined ? 'channel active' : 'channel inactive')
  .attr('d', d => generateChannelPath(d.fromCenter, d.toCenter))
  .attr('stroke', d => d.emergent ? '#DAA520' : '#8B4513')  // Goldenrod for emergent
  .attr('stroke-width', 2);

// ❌ Legacy Pattern - AVOID
const channels = svg.selectAll('.channel')
  .data(bodygraphData.channels, d => d.id);

channels.enter().append('path')
  .attr('class', 'channel');

channels
  .attr('class', d => d.defined ? 'channel active' : 'channel inactive')
  .attr('d', d => generateChannelPath(d.fromCenter, d.toCenter))
  .attr('stroke', d => d.emergent ? '#DAA520' : '#8B4513')
  .attr('stroke-width', 2);

channels.exit().remove();
```

**Why v7 is Better**:
- ✅ Less code (single `.join()` call)
- ✅ Object constancy built-in (key function)
- ✅ Clearer intent (enter/update/exit semantics explicit)
- ✅ Better performance (D3 optimizes internally)
- ✅ Easier to reason about (functional style)

**When to Use Callbacks**:
- Need fine-grained control over transitions
- Different behavior for enter/update/exit
- Complex animation sequences

**When to Use Simple `.join()`**:
- Standard data binding (most cases)
- No special enter/update/exit behavior
- Performance is critical
```

---

## 4. Implementation Checklist

### Phase 1: Update System Prompts (This Sprint)

- [ ] Add Pydantic v2 section to Implementer (50-80 lines)
- [ ] Add pytest fixture section to Test Engineer (50-80 lines)
- [ ] (Optional) Add D3 v7 section to D3 Specialist (30-50 lines)
- [ ] Test prompts with sample tasks

### Phase 2: Validation (Next Sprint)

- [ ] Create `tests/test_agent_training.py`
- [ ] Write test to verify required keywords in prompts
- [ ] Generate sample code from each agent
- [ ] Verify code follows 2026 patterns (no v1 Pydantic, no D3 v3 `.enter()`)

### Phase 3: Code-as-Ontology (Backlog)

- [ ] Create `src/human_design/agents/training/` module
- [ ] Define `Pattern` and `AntiPattern` Pydantic models
- [ ] Extract examples from prompts into `training/pydantic_v2.py`
- [ ] Extract examples into `training/pytest_patterns.py`
- [ ] Generate system prompts from code modules
- [ ] Add Python Linguist query for "detect Pydantic v1 usage"

---

## 5. Expected Outcomes

### Before Enhancement

```python
# Agent generates Pydantic v1 pattern (model training default)
@validator('lines')
def validate_lines(cls, lines):
    if len(lines) != 6:
        raise ValueError(f'Gate must have exactly 6 lines, got {len(lines)}')
    return lines
```

### After Enhancement

```python
# Agent generates Pydantic v2 pattern (system prompt overrides model default)
@field_validator('lines')
@classmethod
def validate_lines(cls, lines: list[LineSemantics]) -> list[LineSemantics]:
    if len(lines) != 6:
        raise ValueError(f'Gate must have exactly 6 lines, got {len(lines)}')
    return lines
```

---

## 6. Testing the Enhancements

```python
# tests/test_agent_training.py

@pytest.mark.parametrize("agent_name,required_patterns", [
    ("implementer", [
        "@field_validator",
        "@model_validator",
        "ConfigDict",
        "mode='after'",
        "@classmethod",
        "-> Self",
    ]),
    ("test_engineer", [
        "@pytest.fixture",
        "scope=",
        "monkeypatch",
        "yield",
        "autouse",
    ]),
    ("d3_specialist", [
        ".join(",
        "D3 v7",
        "selection.enter()",  # Should be present as anti-pattern
        "❌",
    ]),
])
def test_agent_prompt_includes_2026_patterns(agent_name, required_patterns):
    """Verify agent system prompts include 2026 best practices."""
    agent_module = importlib.import_module(f"human_design.agents.{agent_name}")
    system_prompt = getattr(agent_module, f"{agent_name.upper()}_SYSTEM_PROMPT")
    
    for pattern in required_patterns:
        assert pattern in system_prompt, f"{agent_name} missing pattern: {pattern}"


def test_implementer_generates_pydantic_v2():
    """Test that implementer generates Pydantic v2 code."""
    agent = ImplementerAgent(config)
    result = agent.implement("Create a GateSemantics model with line validation")
    
    code = result['implementation']
    
    # Should use v2 patterns
    assert "@field_validator" in code
    assert "@classmethod" in code
    assert "-> Self" in code or "-> list[" in code
    
    # Should NOT use v1 patterns
    assert "@validator" not in code
    assert "class Config:" not in code


def test_test_engineer_generates_fixtures():
    """Test that test engineer generates pytest fixtures."""
    agent = TestEngineerAgent(config)
    result = agent.create_tests("Create test for bodygraph calculation")
    
    tests = result['tests']
    
    # Should use fixture patterns
    assert "@pytest.fixture" in tests
    assert "scope=" in tests or "scope" in tests
    
    # Should use parametrize
    assert "@pytest.mark.parametrize" in tests
```

---

## 7. Rollout Plan

### Week 1: Implementer Enhancement
- Monday: Add Pydantic v2 section to implementer.py
- Tuesday: Test with sample implementation tasks
- Wednesday: Iterate based on results
- Thursday: Review with team
- Friday: Merge to main

### Week 2: Test Engineer Enhancement
- Monday: Add pytest fixture section to test_engineer.py
- Tuesday: Test with sample test generation tasks
- Wednesday: Iterate based on results
- Thursday: Review with team
- Friday: Merge to main

### Week 3: Validation
- Monday: Create test_agent_training.py
- Tuesday: Run validation tests
- Wednesday: Fix any gaps found
- Thursday: Document results
- Friday: Update training documentation

---

## Questions? Issues?

**Q: Why not just increase system prompt length to 500+ lines?**  
A: Length is less important than content quality. 250-350 lines with concrete examples is better than 500 lines of abstract guidance.

**Q: Should we enhance Python Linguist?**  
A: No immediate need. It's already well-trained (1082 lines, comprehensive). Future enhancement: add Human Design ontology query examples.

**Q: What about D3 Specialist?**  
A: Current prompt already teaches D3 v7. Enhancement is optional (adds side-by-side legacy comparison for clarity).

**Q: How do we prevent regression?**  
A: Add validation tests (`test_agent_training.py`) to CI pipeline. Tests verify required keywords in system prompts and agent-generated code.

**Q: What's the code-as-ontology vision?**  
A: Long-term: System prompts generated from Pydantic models in `training/` module. Training examples are executable tests. Python Linguist can detect anti-patterns in codebase.

---

**Status**: Ready for implementation. Start with Implementer agent (highest priority).
