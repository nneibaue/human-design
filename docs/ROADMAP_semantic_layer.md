# Semantic Adapter Layer: Implementation Roadmap

**Related ADR**: `docs/architecture/ADR_semantic_adapter_layer.md`  
**Status**: IN PROGRESS  
**Target Completion**: 3 weeks (Phases 1-3)

---

## Overview

This roadmap implements the **semantic adapter layer** that separates deterministic Human Design calculations from interpretation systems (64keys, Ra Traditional, Jolly Alchemy).

**Architecture**: Raw coordinates → Semantic layer → Interpreted descriptions

---

## Phase 1: Extract Core from Semantics (Week 1)

### Goal
Split `HD_ONTOLOGY_complete.json` into:
- **Core** (immutable calculation data): Gate coordinates, channel topology
- **64keys semantics** (interpretation data): Names, descriptions, meanings

### Tasks

#### 1.1 Create Core Ontology Structure
- [ ] Create directory: `ontology/core/`
- [ ] Extract gate zodiac ranges → `ontology/core/gates_coordinates.yaml`
  ```yaml
  # gates_coordinates.yaml (NO semantic names, only coordinates)
  - gate_number: 1
    complement: 2
    coordinate_range:
      start_deg: 216.0
      end_deg: 221.25
  ```
- [ ] Extract channel pairs → `ontology/core/channels_topology.yaml`
  ```yaml
  # channels_topology.yaml (topology only, no names/descriptions)
  - id: "1-8"
    gate1: 1
    gate2: 8
    center_a: IDENTITY
    center_b: EXPRESSION
  ```
- [ ] Extract center-gate memberships → `ontology/core/centers_gates.yaml`
  ```yaml
  # centers_gates.yaml (structure only)
  - center: LIFEFORCE
    gates: [3, 5, 9, 14, 27, 29, 34, 42, 59]
  ```

**Validation**: `grep -i "64keys\|description\|name" ontology/core/*.yaml` returns nothing (no semantics in core)

#### 1.2 Create 64keys Semantic Structure
- [ ] Create directory: `ontology/semantics/64keys/`
- [ ] Create `ontology/semantics/64keys/manifest.yaml`
  ```yaml
  system_id: 64keys
  version: "1.0.0"
  author: "Richard Rudd / 64keys.com"
  license: "Used with permission"
  description: |
    64keys interpretation system with modern terminology
    (Initiator, Builder, Specialist, Coordinator, Observer)
  ```
- [ ] Extract types → `ontology/semantics/64keys/types.yaml`
  ```yaml
  - type_code: sacral_motor_throat
    display_name: "Specialist"
    traditional_name: "Manifesting Generator"
    strategy: "Respond and inform before acting"
    signature: "Satisfaction and peace"
    not_self_theme: "Frustration and anger"
    description: |
      Specialists have both generator energy and manifestor speed...
  ```
- [ ] Extract authorities → `ontology/semantics/64keys/authorities.yaml`
- [ ] Extract centers → `ontology/semantics/64keys/centers.yaml`
- [ ] Extract profiles → `ontology/semantics/64keys/profiles.yaml`
- [ ] Extract gates → `ontology/semantics/64keys/gates/gate_01.yaml` through `gate_64.yaml`

**Source**: Scrape from `GateAPI.get_gate_summary()` calls or parse `HD_ONTOLOGY_complete.json`

**Validation**: Load with `SemanticLoader.load("64keys")` → all 64 gates present, all fields validated

#### 1.3 Deprecate Old Ontology
- [ ] Rename `HD_ONTOLOGY_complete.json` → `HD_ONTOLOGY_complete.json.deprecated`
- [ ] Add README in `ontology/` explaining new structure
- [ ] Update `.gitignore` to mark deprecated file

---

## Phase 2: Build Semantic Schema (Week 1-2)

### Goal
Implement type-safe Pydantic models and loader for semantic systems.

### Tasks

#### 2.1 Define Semantic Models
- [x] **DONE**: Created `src/human_design/models/semantic.py` with:
  - [x] `GateSemantics`, `LineSemantics` models
  - [x] `TypeSemantics`, `AuthoritySemantics` models
  - [x] `CenterSemantics`, `ProfileSemantics` models
  - [x] `SemanticInterpretation` container model
  - [x] `SemanticProvider` protocol
  - [x] Field validators (6 lines per gate, 64 gates total, etc.)

#### 2.2 Build Semantic Loader
- [x] **DONE**: Implemented `SemanticLoader` class in `semantic.py`:
  - [x] `load(system_id)` method with `@lru_cache`
  - [x] `_load_gates()` for individual or aggregated YAML
  - [x] `_load_yaml_dict()` helper
  - [x] `list_available_systems()` for discovery
  - [x] Error handling with helpful messages

#### 2.3 Write Tests
- [ ] Create `tests/test_semantic_loader.py`
  ```python
  def test_load_64keys():
      semantics = SemanticLoader.load("64keys")
      assert semantics.system_id == "64keys"
      assert len(semantics.gates) == 64
      assert len(semantics.types) >= 5  # 5 core types
      assert len(semantics.authorities) == 7
  
  def test_gate_has_six_lines():
      semantics = SemanticLoader.load("64keys")
      gate42 = semantics.gates[42]
      assert len(gate42.lines) == 6
      assert gate42.get_line(3).line_number == 3
  
  def test_missing_system_error():
      with pytest.raises(FileNotFoundError):
          SemanticLoader.load("nonexistent_system")
  ```
- [ ] Create `tests/test_semantic_validation.py`
  ```python
  def test_gate_missing_lines_fails():
      """Gate with <6 lines should fail validation."""
      with pytest.raises(ValidationError):
          GateSemantics(
              gate_number=1,
              name="Test",
              summary="Test",
              description="Test",
              lines=[LineSemantics(line_number=1, title="Test", text="Test")]
          )
  ```
- [ ] Run mypy: `mypy src/human_design/models/semantic.py` → no errors

---

## Phase 3: Refactor Existing Code (Week 2)

### Goal
Migrate `GateAPI` and models to use semantic adapter layer.

### Tasks

#### 3.1 Refactor GateAPI
- [ ] Update `src/human_design/api.py`:
  ```python
  class GateAPI:
      def __init__(self, semantic_system: str | None = None):
          """
          Initialize API client with semantic interpretation system.
          
          Args:
              semantic_system: "64keys", "ra_traditional", etc.
                              If None, uses HD_SEMANTIC_SYSTEM env var.
          """
          self.session = requests.Session()
          self.is_authenticated = False
          self._gate_cache: dict[int, GateSummary64Keys] = {}
          
          # Load semantic interpretation
          system_id = semantic_system or get_default_semantic_system()
          self.semantics = SemanticLoader.load(system_id)
      
      def bodygraph_to_summary(
          self,
          raw_bodygraph: RawBodyGraph,
          semantic_override: str | None = None
      ) -> BodyGraphSummary:
          """Convert RawBodyGraph using semantic layer."""
          semantics = self.semantics
          if semantic_override:
              semantics = SemanticLoader.load(semantic_override)
          
          # Use semantics to interpret raw data
          conscious_summaries = [
              self._interpret_activation(act, semantics)
              for act in raw_bodygraph.conscious_activations
          ]
          # ... similar for unconscious
  ```
- [ ] Add `_interpret_activation()` method
- [ ] Update `get_gate_summary()` to return generic `GateSemantics` instead of `GateSummary64Keys`

#### 3.2 Create Generic Summary Model
- [ ] Create `src/human_design/models/summary.py`:
  ```python
  class ActivationSummary(BaseModel):
      """Generic activation summary (system-agnostic)."""
      planet: PlanetField
      gate: GateSemantics  # From semantic layer
      line: LineSemantics  # From semantic layer
  
  class BodyGraphSummary(BaseModel):
      """Generic bodygraph summary (system-agnostic)."""
      birth_info: BirthInfo
      conscious_activations: list[ActivationSummary]
      unconscious_activations: list[ActivationSummary]
      type: TypeSemantics  # From semantic layer
      authority: AuthoritySemantics  # From semantic layer
      profile: ProfileSemantics  # From semantic layer
      
      # Metadata
      semantic_system: str  # Which system was used
  ```

#### 3.3 Deprecate 64keys-Specific Models
- [ ] Add deprecation warnings to `summaries_64keys.py`:
  ```python
  import warnings
  
  class GateSummary64Keys(GateDefinition):
      def __init__(self, **kwargs):
          warnings.warn(
              "GateSummary64Keys is deprecated. Use GateSemantics from semantic layer.",
              DeprecationWarning,
              stacklevel=2
          )
          super().__init__(**kwargs)
  ```
- [ ] Update docstrings: "DEPRECATED: Use `BodyGraphSummary` with `semantic_system='64keys'`"
- [ ] Add migration guide: `docs/MIGRATION_SEMANTIC_LAYER.md`

#### 3.4 Update Type/Authority Enums
- [ ] Refactor `src/human_design/models/type_authority.py`:
  ```python
  class HDType(str, Enum):
      """Internal type codes (system-agnostic)."""
      NO_DEFINITION = "no_definition"
      SACRAL_DEFINED = "sacral_defined_no_motor_throat"
      SACRAL_MOTOR_THROAT = "sacral_motor_throat"
      MOTOR_THROAT = "motor_throat_no_sacral"
      OTHER_DEFINITION = "other_definition"
      
      def display_name(self, semantic_system: str = "64keys") -> str:
          """Get display name from semantic system."""
          semantics = SemanticLoader.load(semantic_system)
          return semantics.types[self.value].display_name
  ```
- [ ] Similar for `Authority` enum

---

## Phase 4: Add Ra Traditional System (Week 3)

### Goal
Prove hot-swappability with a second semantic system.

### Tasks

#### 4.1 Create Ra Traditional Structure
- [ ] Create directory: `ontology/semantics/ra_traditional/`
- [ ] Create `manifest.yaml`:
  ```yaml
  system_id: ra_traditional
  version: "1.0.0"
  author: "Ra Uru Hu"
  license: "Educational use"
  description: |
    Traditional Human Design terminology from Ra Uru Hu and Jovian Archive.
  ```

#### 4.2 Map Ra Terminology
- [ ] Create `types.yaml`:
  ```yaml
  - type_code: sacral_motor_throat
    display_name: "Manifesting Generator"
    traditional_name: "Manifesting Generator"  # Same
    # ... (strategy, signature, etc.)
  
  - type_code: sacral_defined_no_motor_throat
    display_name: "Generator"
    traditional_name: "Generator"
    # ...
  
  - type_code: motor_throat_no_sacral
    display_name: "Manifestor"
    traditional_name: "Manifestor"
    # ...
  ```
- [ ] Create `authorities.yaml`:
  ```yaml
  - authority_code: emotional
    display_name: "Solar Plexus Authority"
    traditional_name: "Solar Plexus Authority"
    # ...
  ```
- [ ] Create `centers.yaml`:
  ```yaml
  - center_name: LIFEFORCE
    display_name: "Sacral Center"
    traditional_name: "Sacral Center"
    # ... (Ra's descriptions)
  
  - center_name: EMOTION
    display_name: "Solar Plexus"
    traditional_name: "Solar Plexus"
    # ...
  ```
- [ ] Create `gates/` with Ra's gate names and I Ching hexagram references

**Source**: Jovian Archive materials, Human Design textbooks

#### 4.3 Test Hot-Swap
- [ ] Write test:
  ```python
  def test_semantic_hot_swap():
      raw = RawBodyGraph(birth_info=BirthInfo(...))
      
      # 64keys interpretation
      api_64keys = GateAPI(semantic_system="64keys")
      summary_64keys = api_64keys.bodygraph_to_summary(raw)
      
      # Ra interpretation
      api_ra = GateAPI(semantic_system="ra_traditional")
      summary_ra = api_ra.bodygraph_to_summary(raw)
      
      # Same topology, different terminology
      assert summary_64keys.type.type_code == summary_ra.type.type_code
      assert summary_64keys.type.display_name == "Specialist"
      assert summary_ra.type.display_name == "Manifesting Generator"
  ```

---

## Phase 5: Jolly Alchemy Placeholder (Week 3)

### Goal
Stub Rebecca's custom semantic system for future content.

### Tasks

#### 5.1 Create Jolly Alchemy Structure
- [ ] Create directory: `ontology/semantics/jolly_alchemy/`
- [ ] Create `manifest.yaml`:
  ```yaml
  system_id: jolly_alchemy
  version: "0.1.0"  # Pre-release
  author: "Rebecca Energy"
  license: "Proprietary"
  description: |
    Jolly Alchemy interpretation system emphasizing energetic alchemy
    and transformation. Custom terminology and descriptions by Rebecca.
  ```

#### 5.2 Create Placeholder Content
- [ ] Create `types.yaml` with Rebecca's type names:
  ```yaml
  - type_code: sacral_motor_throat
    display_name: "The Energized Catalyst"
    traditional_name: "Manifesting Generator"
    strategy: "Alchemize response into swift action"
    signature: "Satisfaction and catalytic impact"
    not_self_theme: "Frustration and scattered energy"
    description: |
      [PLACEHOLDER: Rebecca to fill in her interpretation]
  ```
- [ ] Create `centers.yaml` with Rebecca's center names:
  ```yaml
  - center_name: LIFEFORCE
    display_name: "Source Well"
    traditional_name: "Sacral"
    function: "Renewable life force and creative power"
    defined_description: |
      [PLACEHOLDER: Rebecca's interpretation]
    undefined_description: |
      [PLACEHOLDER: Rebecca's interpretation]
  ```
- [ ] Create placeholder gates (copy from 64keys, mark as TODO)

#### 5.3 Document Extension Process
- [x] **DONE**: Created `docs/SEMANTIC_EXTENSION_GUIDE.md` with:
  - [x] Quick start guide
  - [x] File structure reference
  - [x] Schema reference (all YAML formats)
  - [x] Validation checklist
  - [x] Examples (minimalist, maximalist, Jolly Alchemy)
  - [x] Publishing options
  - [x] FAQ

#### 5.4 Rebecca Handoff
- [ ] Share `docs/SEMANTIC_EXTENSION_GUIDE.md` with Rebecca
- [ ] Walk through `ontology/semantics/jolly_alchemy/` structure
- [ ] Define review process for content updates
- [ ] Set target date for v1.0.0 (Rebecca's content complete)

---

## Validation Checklist

After each phase, validate:

### Phase 1 Validation
- [ ] Core ontology has NO semantic content (no names/descriptions)
- [ ] 64keys semantics load successfully: `SemanticLoader.load("64keys")`
- [ ] All 64 gates present with 6 lines each
- [ ] All 5 types, 7 authorities, 9 centers, 12 profiles present

### Phase 2 Validation
- [ ] Mypy passes: `mypy src/human_design/models/semantic.py`
- [ ] Tests pass: `pytest tests/test_semantic_loader.py`
- [ ] Pydantic validation catches incomplete data
- [ ] `@lru_cache` prevents redundant file I/O

### Phase 3 Validation
- [ ] Existing API still works: `api = GateAPI(); api.bodygraph_to_summary(raw)`
- [ ] Deprecation warnings appear (but don't break)
- [ ] New API works: `api = GateAPI(semantic_system="64keys")`
- [ ] Type safety: `summary.type.display_name` autocompletes in IDE

### Phase 4 Validation
- [ ] Ra system loads: `SemanticLoader.load("ra_traditional")`
- [ ] Hot-swap works: Same raw bodygraph, different interpretations
- [ ] Terminology differences visible: "Specialist" vs "Manifesting Generator"

### Phase 5 Validation
- [ ] Jolly Alchemy loads: `SemanticLoader.load("jolly_alchemy")`
- [ ] Rebecca can edit YAML files without touching code
- [ ] Extension guide is clear and complete

---

## Success Criteria

### Must Have (MVP)
- [x] Core ontology separated from semantics
- [x] Type-safe semantic schema (Pydantic models)
- [x] Semantic loader with validation
- [ ] 64keys system fully migrated
- [ ] Existing API backward compatible
- [ ] Tests pass

### Should Have (Full Implementation)
- [ ] Ra Traditional system complete
- [ ] Jolly Alchemy placeholder ready
- [ ] Extension guide published
- [ ] Migration guide for users
- [ ] Deprecation warnings in place

### Nice to Have (Future)
- [ ] CLI tool: `hd-semantic validate my_system`
- [ ] Web UI for editing semantic configs
- [ ] Community semantic systems (Gene Keys, etc.)

---

## Risk Mitigation

### Risk: Breaking Changes for Existing Users
**Mitigation**: 
- Keep old models working with deprecation warnings
- Provide 2-version grace period
- Detailed migration guide

### Risk: Incomplete Semantic Systems
**Mitigation**:
- Pydantic validation ensures completeness
- Template directory with all required files
- Clear error messages: "Missing gate 42"

### Risk: Rebecca's Content Delayed
**Mitigation**:
- Placeholder system works immediately
- Rebecca fills in descriptions incrementally
- Version 0.1.0 → 1.0.0 when complete

---

## Timeline

| Phase | Duration | Completion Date |
|-------|----------|----------------|
| Phase 1: Extract Core | 3-4 days | 2025-02-07 |
| Phase 2: Build Schema | 2-3 days | 2025-02-10 |
| Phase 3: Refactor Code | 4-5 days | 2025-02-14 |
| Phase 4: Ra Traditional | 3-4 days | 2025-02-18 |
| Phase 5: Jolly Alchemy Stub | 1-2 days | 2025-02-21 |
| **Total** | **~3 weeks** | **2025-02-21** |

---

## Next Actions

1. **Nathan**: Start Phase 1 (extract core ontology from HD_ONTOLOGY_complete.json)
2. **Nathan**: Complete Phase 2 tests (semantic loader validation)
3. **Rebecca**: Review `docs/SEMANTIC_EXTENSION_GUIDE.md`
4. **Rebecca**: Begin defining Jolly Alchemy terminology (types, centers, authorities)
5. **Nathan**: Begin Phase 3 (refactor GateAPI to use semantic layer)

---

**Last Updated**: 2025-01-31  
**Owner**: Nathan Neibauer  
**Reviewers**: Rebecca Energy (content), Community (feedback)
