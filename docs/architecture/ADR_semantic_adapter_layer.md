# ADR: Semantic Adapter Layer for Ontological Interpretation Systems

**Status**: PROPOSED  
**Date**: 2025-01-31  
**Decision**: Design a type-safe, hot-swappable semantic adapter layer that separates deterministic Human Design calculations from interpretation systems (64keys, Ra Uru Hu traditional, Jolly Alchemy custom)

---

## Context

### Current Architecture State

The Human Design codebase has **excellent separation** between:
1. **Deterministic calculations** (Swiss Ephemeris, gate/line mappings, channel formation)
2. **Semantic interpretations** (64keys terminology, descriptions, line meanings)

```
RawBodyGraph (calculations) → GateAPI → BodyGraphSummary64Keys (64keys semantics)
```

**However**, the semantic layer is currently:
- ❌ **Hardcoded to 64keys** (`summaries_64keys.py`, `GateAPI`)
- ❌ **Mixed with raw structures** (`ontology/HD_ONTOLOGY_complete.json` contains both coordinates AND 64keys names)
- ❌ **Not extensible** (Rebecca's Jolly Alchemy flavor requires new semantic layer)
- ❌ **Terminology baked in** (Initiator/Builder vs Manifestor/Generator requires code changes)

### Core Insight: Sheens Over Coordinates

The same **coordinate system** produces the same **structural data**:
- Gate 42, Line 3 (coordinates)
- Channel 42-53 (structure)
- Centers defined: LIFEFORCE, EMOTION, EXPRESSION (topology)

But different **semantic sheens** interpret these coordinates differently:

| Coordinate | 64keys | Ra Traditional | Jolly Alchemy |
|-----------|---------|----------------|---------------|
| Type with Sacral + Motor-to-Throat | **Specialist** | **Manifesting Generator** | **The Energized Catalyst** |
| Center: LIFEFORCE | "Life Force Center" | "Sacral Center" | "Source Well" |
| Gate 42 | "Maturation" | "Increase/Growth" | "The Harvest Cycle" |
| Authority: EMOTION | "Emotional Authority" | "Solar Plexus Authority" | "Wave Wisdom" |

**All systems agree on topology, differ on terminology and meaning.**

---

## Decision

We will implement a **three-layer architecture**:

### Layer 1: Core Calculations (UNCHANGED)
- **Immutable**: Gate numbers, line numbers, channel IDs, center topology
- **No semantic knowledge**: Coordinates only
- **Already implemented**: `RawBodyGraph`, `BodyGraphDefinition`, `ChannelRegistry`

```python
# Core layer produces coordinates
RawBodyGraph:
  conscious_activations: [RawActivation(planet=SUN, gate=42, line=3)]
  active_channels: [ChannelDefinition(id="42-53", ...)]
  defined_centers: {"LIFEFORCE", "EMOTION", "EXPRESSION"}
```

### Layer 2: Semantic Schema (NEW)
- **Type-safe ontology definition** (Pydantic models)
- **Interpretation-agnostic interface** (protocols)
- **Hot-swappable via config** (YAML/JSON)

```python
# Semantic schema defines structure
class SemanticInterpretation(BaseModel):
    """Base interface for all interpretation systems."""
    system_id: Literal["64keys", "ra_traditional", "jolly_alchemy"]
    version: str
    
    gates: dict[GateNumber, GateSemantics]
    centers: dict[CenterName, CenterSemantics]
    types: dict[str, TypeSemantics]
    authorities: dict[str, AuthoritySemantics]
    
    # Mapping functions
    def interpret_activation(self, raw: RawActivation) -> ActivationSummary: ...
    def interpret_type(self, type_code: str) -> TypeDescription: ...
```

### Layer 3: Interpretation Loaders (NEW)
- **Plugin architecture**: Load semantic systems from YAML/JSON
- **Factory pattern**: `SemanticLoader.load("64keys")` → `SemanticInterpretation`
- **Validation**: Pydantic ensures all required fields present

```python
# Usage: Client code chooses semantic system
api = GateAPI(semantic_system="64keys")  # or "ra_traditional" or "jolly_alchemy"
summary = api.bodygraph_to_summary(raw_bodygraph)

# Backend loads appropriate semantic config
semantics = SemanticLoader.load("64keys")  # or from env var: SEMANTIC_SYSTEM
summary = semantics.interpret(raw_bodygraph)
```

---

## Architecture Design

### Ontology File Structure

```
ontology/
├── core/                          # Immutable calculation definitions
│   ├── gates_coordinates.yaml     # Gate → zodiac ranges (NEVER changes)
│   ├── channels_topology.yaml     # Channel pairs (42-53, 19-49, etc.)
│   └── centers_gates.yaml         # Center → gate membership
│
├── semantics/                     # Hot-swappable interpretation systems
│   ├── 64keys/
│   │   ├── manifest.yaml          # System metadata
│   │   ├── types.yaml             # Initiator, Builder, Specialist, etc.
│   │   ├── authorities.yaml       # Emotional, Sacral, Splenic, etc.
│   │   ├── centers.yaml           # LIFEFORCE → "Life Force Center"
│   │   ├── gates/                 # Gate-by-gate descriptions
│   │   │   ├── gate_01.yaml
│   │   │   ├── gate_02.yaml
│   │   │   └── ...
│   │   └── profiles.yaml          # 1/3, 2/4, etc.
│   │
│   ├── ra_traditional/
│   │   ├── manifest.yaml
│   │   ├── types.yaml             # Manifestor, Generator, etc.
│   │   └── ...
│   │
│   └── jolly_alchemy/
│       ├── manifest.yaml          # Rebecca's custom system
│       ├── types.yaml             # Energized Catalyst, etc.
│       └── ...
│
└── HD_ONTOLOGY_complete.json      # DEPRECATED: Will be split into core + 64keys
```

### Type-Safe Schema Models

```python
# models/semantic.py
from typing import Protocol, runtime_checkable

@runtime_checkable
class SemanticProvider(Protocol):
    """Protocol for all semantic interpretation systems."""
    
    def get_gate_meaning(self, gate: GateNumber, line: GateLineNumber) -> GateLineSummary: ...
    def get_type_description(self, type_code: str) -> TypeDescription: ...
    def get_authority_description(self, authority_code: str) -> AuthorityDescription: ...
    def get_center_meaning(self, center: CenterName, defined: bool) -> CenterDescription: ...


class GateSemantics(BaseModel):
    """Semantic interpretation of a gate."""
    gate_number: GateNumber
    name: str                      # 64keys: "Maturation", Ra: "Increase"
    quarter: str | None = None     # 64keys-specific
    summary: str                   # One-line essence
    description: str               # Full meaning
    strive: str | None = None      # 64keys-specific
    lines: list[LineSemantics]     # Line-by-line interpretations
    
    # Custom fields per system
    extra: dict[str, Any] = Field(default_factory=dict)


class TypeSemantics(BaseModel):
    """Type interpretation with terminology mapping."""
    type_code: str                 # Internal: "sacral_motor_throat"
    display_name: str              # 64keys: "Specialist", Ra: "Manifesting Generator"
    traditional_name: str | None   # Cross-reference
    strategy: str
    signature: str
    not_self_theme: str
    description: str
    
    # Topology requirements (system-agnostic)
    requires_defined: set[CenterName]
    requires_motor_throat: bool


class SemanticInterpretation(BaseModel):
    """Complete semantic system."""
    system_id: str
    version: str
    author: str | None = None
    
    gates: dict[GateNumber, GateSemantics]
    types: dict[str, TypeSemantics]
    authorities: dict[str, AuthoritySemantics]
    centers: dict[CenterName, CenterSemantics]
    profiles: dict[str, ProfileSemantics]
    
    class Config:
        # Allow extra fields for system-specific extensions
        extra = "allow"
```

### Semantic Loader Factory

```python
# semantic_loader.py
from pathlib import Path
import yaml
from functools import lru_cache

class SemanticLoader:
    """Factory for loading semantic interpretation systems."""
    
    ONTOLOGY_ROOT = Path(__file__).parent / "ontology" / "semantics"
    
    @classmethod
    @lru_cache(maxsize=10)
    def load(cls, system_id: str) -> SemanticInterpretation:
        """
        Load a semantic interpretation system from ontology files.
        
        Args:
            system_id: "64keys", "ra_traditional", "jolly_alchemy"
            
        Returns:
            Validated SemanticInterpretation model
            
        Raises:
            FileNotFoundError: If system_id directory doesn't exist
            ValidationError: If YAML files are malformed
        """
        system_dir = cls.ONTOLOGY_ROOT / system_id
        if not system_dir.exists():
            raise FileNotFoundError(f"Semantic system not found: {system_id}")
        
        # Load manifest
        manifest = yaml.safe_load((system_dir / "manifest.yaml").read_text())
        
        # Load gates (from individual files or aggregated)
        gates = cls._load_gates(system_dir)
        
        # Load other components
        types = yaml.safe_load((system_dir / "types.yaml").read_text())
        authorities = yaml.safe_load((system_dir / "authorities.yaml").read_text())
        centers = yaml.safe_load((system_dir / "centers.yaml").read_text())
        profiles = yaml.safe_load((system_dir / "profiles.yaml").read_text())
        
        return SemanticInterpretation(
            system_id=system_id,
            version=manifest["version"],
            author=manifest.get("author"),
            gates=gates,
            types=types,
            authorities=authorities,
            centers=centers,
            profiles=profiles,
        )
    
    @classmethod
    def _load_gates(cls, system_dir: Path) -> dict[GateNumber, GateSemantics]:
        """Load gate semantics from individual files or aggregated YAML."""
        gates_dir = system_dir / "gates"
        if gates_dir.exists():
            # Load from individual gate files (gate_01.yaml, gate_02.yaml, ...)
            gates = {}
            for gate_file in sorted(gates_dir.glob("gate_*.yaml")):
                gate_num = int(gate_file.stem.split("_")[1])
                gate_data = yaml.safe_load(gate_file.read_text())
                gates[gate_num] = GateSemantics(**gate_data)
            return gates
        else:
            # Load from aggregated gates.yaml
            gates_data = yaml.safe_load((system_dir / "gates.yaml").read_text())
            return {g["gate_number"]: GateSemantics(**g) for g in gates_data}


# Environment-based default
def get_default_semantic_system() -> str:
    """Get semantic system from environment or default to 64keys."""
    return os.getenv("HD_SEMANTIC_SYSTEM", "64keys")
```

### Updated API Client

```python
# api.py (REFACTORED)
class GateAPI:
    """64keys.com API Client with semantic interpretation."""
    
    def __init__(self, semantic_system: str | None = None):
        """
        Initialize API client with semantic interpretation system.
        
        Args:
            semantic_system: "64keys", "ra_traditional", "jolly_alchemy"
                            If None, uses HD_SEMANTIC_SYSTEM env var or defaults to "64keys"
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
        """
        Convert RawBodyGraph to semantic summary.
        
        Args:
            raw_bodygraph: Raw calculated bodygraph
            semantic_override: Temporarily use different semantic system
            
        Returns:
            BodyGraphSummary with semantic interpretations applied
        """
        semantics = self.semantics
        if semantic_override:
            semantics = SemanticLoader.load(semantic_override)
        
        # Convert activations using semantic layer
        conscious_summaries = [
            semantics.interpret_activation(act) 
            for act in raw_bodygraph.conscious_activations
        ]
        
        unconscious_summaries = [
            semantics.interpret_activation(act)
            for act in raw_bodygraph.unconscious_activations
        ]
        
        return BodyGraphSummary(
            birth_info=raw_bodygraph.birth_info,
            conscious_activations=conscious_summaries,
            unconscious_activations=unconscious_summaries,
            type=semantics.interpret_type(raw_bodygraph.type),
            authority=semantics.interpret_authority(raw_bodygraph.authority),
            profile=semantics.interpret_profile(raw_bodygraph.profile),
        )
```

---

## Implementation Plan

### Phase 1: Extract Core from Semantics (Week 1)
**Goal**: Split `HD_ONTOLOGY_complete.json` into immutable core + 64keys semantics

1. **Create `ontology/core/` directory**
   - Extract gate coordinates → `gates_coordinates.yaml`
   - Extract channel topology → `channels_topology.yaml`
   - Extract center-gate memberships → `centers_gates.yaml`
   - **These files NEVER contain semantic names/descriptions**

2. **Create `ontology/semantics/64keys/` directory**
   - Extract 64keys terminology → `types.yaml` (Initiator, Builder, etc.)
   - Extract 64keys authority names → `authorities.yaml`
   - Extract 64keys gate descriptions → `gates/gate_01.yaml`, etc.
   - Extract 64keys center descriptions → `centers.yaml`
   - Create `manifest.yaml` with version, author

3. **Validation**: Verify no semantic content remains in core files

### Phase 2: Build Semantic Schema (Week 1-2)
**Goal**: Type-safe Pydantic models for semantic interpretation

1. **Define protocol** (`models/semantic.py`)
   - `SemanticProvider` protocol (interface)
   - `GateSemantics`, `TypeSemantics`, `AuthoritySemantics` models
   - `SemanticInterpretation` container model

2. **Build loader factory** (`semantic_loader.py`)
   - YAML parsing with validation
   - Caching with `@lru_cache`
   - Error handling for missing systems

3. **Tests**
   - Load 64keys system → validate all gates present
   - Schema validation catches missing fields
   - Type safety (mypy passes)

### Phase 3: Refactor Existing Code (Week 2)
**Goal**: Migrate `GateAPI` and models to use semantic layer

1. **Refactor `GateAPI`**
   - Accept `semantic_system` parameter
   - Load semantic interpretation in `__init__`
   - Replace hardcoded 64keys logic with semantic adapter

2. **Deprecate `summaries_64keys.py`**
   - Mark `BodyGraphSummary64Keys` as deprecated
   - Create generic `BodyGraphSummary` (system-agnostic)
   - Maintain backward compatibility for 2 versions

3. **Update `type_authority.py`**
   - Enum values become internal codes
   - Display names from semantic layer
   - Traditional name mapping optional

### Phase 4: Add Ra Traditional System (Week 3)
**Goal**: Prove hot-swappability with second semantic system

1. **Create `ontology/semantics/ra_traditional/`**
   - Map types: Manifestor, Generator, MG, Projector, Reflector
   - Map authorities: Solar Plexus, Sacral, Splenic, Ego, G, Mental, Lunar
   - Map center names: Sacral (not LIFEFORCE), Solar Plexus (not EMOTION)
   - Source: Ra Uru Hu's original terminology from Jovian Archive

2. **Test hot-swap**
   ```python
   # Same bodygraph, different interpretation
   api_64keys = GateAPI(semantic_system="64keys")
   api_ra = GateAPI(semantic_system="ra_traditional")
   
   summary_64keys = api_64keys.bodygraph_to_summary(raw)
   summary_ra = api_ra.bodygraph_to_summary(raw)
   
   # Topology identical, terminology different
   assert summary_64keys.type.code == summary_ra.type.code  # "sacral_motor_throat"
   assert summary_64keys.type.display_name == "Specialist"
   assert summary_ra.type.display_name == "Manifesting Generator"
   ```

### Phase 5: Jolly Alchemy Placeholder (Week 3)
**Goal**: Stub Rebecca's custom semantic system

1. **Create `ontology/semantics/jolly_alchemy/`**
   - Manifest with Rebecca as author
   - Placeholder types: "Energized Catalyst", etc. (Rebecca defines)
   - Placeholder center names: "Source Well", "Wave Wisdom", etc.
   - **Rebecca fills in descriptions later**

2. **Document extension guide** (`docs/SEMANTIC_EXTENSION_GUIDE.md`)
   - How to create custom semantic system
   - Required YAML structure
   - Validation requirements
   - Examples from 64keys/Ra systems

---

## Benefits

### Type Safety
✅ **Static type checking catches errors**
- Pydantic validates all semantic configs at load time
- Type hints everywhere: `def interpret_type(self, type_code: str) -> TypeDescription`
- Mypy ensures semantic providers implement full protocol

### Ergonomics
✅ **Simple, intuitive API**
```python
# One line to switch semantic systems
api = GateAPI(semantic_system="jolly_alchemy")

# Or environment variable
export HD_SEMANTIC_SYSTEM=ra_traditional
api = GateAPI()  # Automatically loads Ra system
```

### Production Ready
✅ **Performance via caching**
- `@lru_cache` on `SemanticLoader.load()` (singleton per system)
- Gate descriptions cached in memory
- No performance regression from abstraction

✅ **Clear error messages**
```
FileNotFoundError: Semantic system not found: jolly_alchemy
  Available systems: ['64keys', 'ra_traditional']
  Directory: /path/to/ontology/semantics/jolly_alchemy
```

### Extensibility
✅ **Plugin architecture**
- Add new system: Drop YAML files in `ontology/semantics/<new_system>/`
- No code changes required (loader discovers automatically)
- Validation ensures completeness

✅ **Backward compatible**
- Existing `GateAPI(semantic_system="64keys")` behavior unchanged
- Deprecated models emit warnings but still work
- Migration guide for users

---

## Alternatives Considered

### Alternative 1: Subclass per System
```python
class GateAPI64Keys(GateAPIBase): ...
class GateAPIRaTraditional(GateAPIBase): ...
```
**Rejected**: Code duplication, no runtime swapping, harder to maintain.

### Alternative 2: Database Table for Semantics
```sql
CREATE TABLE gate_meanings (
    system_id VARCHAR,
    gate_number INT,
    name VARCHAR,
    description TEXT
);
```
**Rejected**: Overkill for 3-4 systems, complicates deployment, no version control.

### Alternative 3: Plugin System with Entry Points
```python
# setup.py
entry_points={
    "hd_semantics": [
        "64keys = hd_semantics_64keys:SemanticProvider64Keys",
    ]
}
```
**Rejected**: Over-engineered for current needs. YAML configs simpler and sufficient.

---

## Consequences

### Positive
- ✅ Clean separation of concerns (calculations never know about semantics)
- ✅ Hot-swappable interpretation systems (YAML-based)
- ✅ Type-safe semantic schema (Pydantic validation)
- ✅ Rebecca can define Jolly Alchemy flavor without touching code
- ✅ Community can contribute semantic systems (Ra, Gene Keys, etc.)
- ✅ Backward compatible (existing API unchanged)

### Negative
- ⚠️ More files to maintain (3 semantic systems × ~5 YAML files each)
- ⚠️ Ontology changes require updating all semantic systems (e.g., new gate discovered)
- ⚠️ Initial migration effort (~3 weeks to extract and refactor)

### Neutral
- ↔️ YAML vs JSON (chose YAML for readability, comments)
- ↔️ Individual gate files vs aggregated (chose individual for easier editing)

---

## Implementation Guidance

### For Nathan (Code Implementation)
1. Start with Phase 1 (extract core ontology)
2. Use `pydantic-settings` for semantic system env var
3. Write tests for `SemanticLoader` first (TDD)
4. Deprecate `summaries_64keys.py` gradually (not immediately)

### For Rebecca (Content Creation)
1. Review `ontology/semantics/64keys/` structure after Phase 1
2. Define Jolly Alchemy terminology in Phase 5
3. Collaborate on `docs/SEMANTIC_EXTENSION_GUIDE.md`

### For Community (Extension Guide)
See `docs/SEMANTIC_EXTENSION_GUIDE.md` (to be created in Phase 5)

---

## References

- **Pydantic Protocols**: https://docs.pydantic.dev/latest/concepts/protocols/
- **Architectural Pattern**: Strategy Pattern (GoF) + Plugin Architecture
- **Prior Art**: i18n/l10n systems (translations as data, not code)
- **Related ADRs**: 
  - ADR: Channel Formation Logic (references core topology)
  - ADR: Multi-Chart Composition (uses semantic layer for interaction charts)

---

**Decision Made By**: Nathan + Rebecca  
**Review Date**: 2025-02-07 (after Phase 1 completion)  
**Status Tracking**: Will move to ACCEPTED after Phase 1 implementation validates approach
