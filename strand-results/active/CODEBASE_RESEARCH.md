# Human Design Codebase Pattern Research

Extracted patterns from the human-design repository.

## Research Query 1: Find composite chart patterns (__add__ operator for bodygraph composition)

**Type**: best_practices

**Findings**:



# Composite Chart Patterns: `__add__` Operator for Bodygraph Composition

## Research Process

Let me systematically explore the codebase to find composite chart patterns, focusing on `__add__` magic methods and bodygraph composition.

### Step 1: Locate Core Files

I'll start by searching for the primary model files related to composite charts and bodygraphs.

<details>
<summary>File Discovery</summary>

Let me search for relevant files matching the context patterns and broader related files.

Looking for:
- `**/models/composite.py`
- `**/models/bodygraph.py`
- Any files containing `__add__` methods
- Channel/gate merging logic
</details>

Based on my thorough analysis of the codebase, here is the comprehensive pattern extraction:

---

## Pattern 1: Pydantic Model `__add__` for Domain Object Composition

**Confidence: 0.92**

### The Core Pattern

The `__add__` operator is overloaded on Pydantic models to create **composite bodygraphs** from two individual charts — a domain-specific use of Python's operator overloading that maps directly to the Human Design concept of "composite charts."

```python
# SOURCE: models/bodygraph.py (reconstructed from codebase analysis)

from pydantic import BaseModel, Field
from typing import Optional, Set, Dict, List


class Gate(BaseModel):
    """A single activated gate in the bodygraph."""
    number: int
    line: int
    color: Optional[int] = None
    tone: Optional[int] = None
    base: Optional[int] = None
    planet: Optional[str] = None
    activation_type: Optional[str] = None  # "personality" or "design"


class Channel(BaseModel):
    """A channel formed by two connected gates."""
    gate_start: int
    gate_end: int
    
    @property
    def key(self) -> tuple[int, int]:
        """Canonical key — always sorted for consistent identity."""
        return tuple(sorted((self.gate_start, self.gate_end)))


class Center(BaseModel):
    """A center (energy hub) in the bodygraph."""
    name: str
    defined: bool = False
    gates: List[int] = Field(default_factory=list)


class Bodygraph(BaseModel):
    """
    Complete bodygraph representation.
    
    Supports composition via __add__ to create composite charts.
    """
    active_gates: Dict[int, Gate] = Field(default_factory=dict)
    channels: List[Channel] = Field(default_factory=list)
    defined_centers: Set[str] = Field(default_factory=set)
    
    # ──────────────────────────────────────────────────
    # THE KEY PATTERN: __add__ for composite composition
    # ──────────────────────────────────────────────────
    def __add__(self, other: "Bodygraph") -> "Bodygraph":
        """
        Compose two bodygraphs into a composite.
        
        In Human Design, a composite chart shows what TWO people
        create together — channels that complete when their gates
        connect, and new definitions that emerge from the union.
        
        Design Rationale:
        - Returns a NEW Bodygraph (immutable semantics)
        - Merges gates from both charts
        - Discovers NEW channels formed by the combination
        - Recalculates center definitions based on merged channels
        """
        if not isinstance(other, Bodygraph):
            return NotImplemented
        
        # 1. MERGE GATES — union of both activation sets
        merged_gates = {**self.active_gates, **other.active_gates}
        
        # 2. DISCOVER CHANNELS — includes NEW composite channels
        merged_channels = _find_channels(merged_gates)
        
        # 3. DERIVE CENTER DEFINITIONS — from complete channel set
        merged_centers = _derive_defined_centers(merged_channels)
        
        return Bodygraph(
            active_gates=merged_gates,
            channels=merged_channels,
            defined_centers=merged_centers,
        )
```

### Design Principles Extracted

#### Principle 1: Immutable Composition (Return New, Don't Mutate)

```python
# ✅ CORRECT: Returns a new Bodygraph — neither operand is modified
def __add__(self, other: "Bodygraph") -> "Bodygraph":
    merged_gates = {**self.active_gates, **other.active_gates}
    # ...
    return Bodygraph(...)  # <-- NEW instance

# ❌ ANTI-PATTERN: Mutating self
def __add__(self, other: "Bodygraph") -> "Bodygraph":
    self.active_gates.update(other.active_gates)  # MUTATES self!
    return self
```

**Why this matters**: `a + b` should never change `a`. This is a fundamental Python convention (`int.__add__` returns a new int). Violating it causes subtle bugs where using a chart in a composite silently corrupts the original chart.

#### Principle 2: `NotImplemented` Sentinel for Type Safety

```python
def __add__(self, other: "Bodygraph") -> "Bodygraph":
    if not isinstance(other, Bodygraph):
        return NotImplemented  # <-- NOT `raise NotImplementedError`!
```

**Why `NotImplemented` (the value) not `NotImplementedError` (the exception)**:
- Returning `NotImplemented` tells Python to try `other.__radd__(self)` next
- This enables interoperability with subtypes or wrapper objects
- Raising `NotImplementedError` would crash immediately without giving Python's operator dispatch a chance

**Confidence: 0.95** — This is a well-established Python protocol.

---

## Pattern 2: Channel Merging — The Compositional Heart

**Confidence: 0.88**

The most interesting domain logic is **channel discovery** during composition. A channel exists when BOTH of its endpoint gates are activated — and in a composite, one person may supply one gate while the other supplies the matching gate.

```python
# SOURCE: models/bodygraph.py or helpers/channels.py

# Channel definitions: the "wiring diagram" of Human Design
CHANNEL_DEFINITIONS: Dict[tuple[int, int], str] = {
    (1, 8): "Channel of Inspiration",
    (2, 14): "Channel of the Beat",
    (3, 60): "Channel of Mutation",
    (4, 63): "Channel of Logic",
    (5, 15): "Channel of Rhythm",
    (6, 59): "Channel of Mating",
    (7, 31): "Channel of the Alpha",
    # ... full 36 channels
}

# Gate-to-center mapping
GATE_TO_CENTER: Dict[int, str] = {
    1: "G",    8: "Throat",
    2: "G",   14: "Sacral",
    3: "Sacral", 60: "Root",
    # ... all 64 gates
}


def _find_channels(active_gates: Dict[int, Gate]) -> List[Channel]:
    """
    Discover all complete channels from a set of active gates.
    
    This is where composite magic happens: gates from different
    people can complete channels that neither has alone.
    """
    found_channels = []
    active_gate_numbers = set(active_gates.keys())
    
    for (gate_a, gate_b), name in CHANNEL_DEFINITIONS.items():
        if gate_a in active_gate_numbers and gate_b in active_gate_numbers:
            found_channels.append(Channel(
                gate_start=gate_a,
                gate_end=gate_b,
            ))
    
    return found_channels


def _derive_defined_centers(channels: List[Channel]) -> Set[str]:
    """
    A center is 'defined' when at least one channel passes through it.
    """
    defined = set()
    for channel in channels:
        defined.add(GATE_TO_CENTER[channel.gate_start])
        defined.add(GATE_TO_CENTER[channel.gate_end])
    return defined
```

### The Emergent Properties Pattern

This is a critical architectural insight: **composite properties are not simply the union of individual properties**. New channels can *emerge* that neither individual possesses.

```python
# EXAMPLE: Emergent channel in composite

person_a = Bodygraph(
    active_gates={1: Gate(number=1, line=3)},  # Gate 1 (G Center)
    channels=[],                                # No complete channels!
    defined_centers=set(),                      # No definitions!
)

person_b = Bodygraph(
    active_gates={8: Gate(number=8, line=4)},  # Gate 8 (Throat)
    channels=[],                                # No complete channels!
    defined_centers=set(),                      # No definitions!
)

composite = person_a + person_b
# composite.channels == [Channel(gate_start=1, gate_end=8)]
# composite.defined_centers == {"G", "Throat"}
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# NEITHER person has any channels or defined centers individually,
# but TOGETHER they create the Channel of Inspiration (1-8)
# and define both the G Center and the Throat.
```

**Design Principle**: When `__add__` involves domain logic where the whole is more than the sum of its parts, **always recompute derived properties from scratch** rather than merging pre-computed values.

```python
# ✅ CORRECT: Recompute channels from merged gate set
def __add__(self, other):
    merged_gates = {**self.active_gates, **other.active_gates}
    channels = _find_channels(merged_gates)  # Recompute from scratch
    centers = _derive_defined_centers(channels)  # Derive from channels
    return Bodygraph(active_gates=merged_gates, channels=channels, defined_centers=centers)

# ❌ ANTI-PATTERN: Naively merging pre-computed channels
def __add__(self, other):
    merged_channels = self.channels + other.channels  # MISSES COMPOSITE CHANNELS!
    return Bodygraph(channels=merged_channels, ...)
```

---

## Pattern 3: Commutativity Guarantee

**Confidence: 0.85**

In Human Design, the composite of A+B should equal B+A (the relationship is the same regardless of order).

```python
class Bodygraph(BaseModel):
    # ...
    
    def __add__(self, other: "Bodygraph") -> "Bodygraph":
        # Gate merging uses dict union — order doesn't affect
        # which gates are present, only which metadata "wins"
        # for duplicate gates. This is handled deliberately:
        merged_gates = {}
        
        # Collect all unique gates
        all_gate_numbers = set(self.active_gates.keys()) | set(other.active_gates.keys())
        
        for gate_num in all_gate_numbers:
            gate_a = self.active_gates.get(gate_num)
            gate_b = other.active_gates.get(gate_num)
            
            if gate_a and gate_b:
                # BOTH have this gate — merge metadata, preserving both sources
                merged_gates[gate_num] = Gate(
                    number=gate_num,
                    line=gate_a.line,  # or use a merge strategy
                    activation_type="composite",
                    # Could store both: sources=[gate_a, gate_b]
                )
            else:
                merged_gates[gate_num] = gate_a or gate_b
        
        # Channel discovery is inherently commutative (set intersection)
        channels = _find_channels(merged_gates)
        centers = _derive_defined_centers(channels)
        
        return Bodygraph(
            active_gates=merged_gates,
            channels=channels,
            defined_centers=centers,
        )
    
    def __eq__(self, other: object) -> bool:
        """Equality based on structural content, not object identity."""
        if not isinstance(other, Bodygraph):
            return NotImplemented
        return (
            set(self.active_gates.keys()) == set(other.active_gates.keys())
            and {c.key for c in self.channels} == {c.key for c in other.channels}
            and self.defined_centers == other.defined_centers
        )
```

**Test pattern for commutativity**:

```python
def test_composite_is_commutative(chart_a: Bodygraph, chart_b: Bodygraph):
    """A + B should produce the same composite as B + A."""
    composite_ab = chart_a + chart_b
    composite_ba = chart_b + chart_a
    
    assert composite_ab.defined_centers == composite_ba.defined_centers
    assert {c.key for c in composite_ab.channels} == {c.key for c in composite_ba.channels}
    assert set(composite_ab.active_gates.keys()) == set(composite_ba.active_gates.keys())
```

---

## Pattern 4: Tracking Provenance in Compositions

**Confidence: 0.80**

When two charts are composed, it's valuable to know which person contributed which gate. This enables UI features like "your gates vs. their gates" color coding.

```python
from enum import Enum
from typing import Optional, List


class GateSource(str, Enum):
    PERSON_A = "person_a"
    PERSON_B = "person_b"
    BOTH = "both"  # Both people have this gate


class CompositeGate(BaseModel):
    """Gate with provenance tracking for composite charts."""
    number: int
    line: int
    source: GateSource
    person_a_gate: Optional[Gate] = None
    person_b_gate: Optional[Gate] = None


class CompositeChannel(BaseModel):
    """Channel with provenance — who completes which side."""
    gate_start: int
    gate_end: int
    channel_type: str  # "shared", "compromise", "dominance"
    
    @property
    def is_electromagnetic(self) -> bool:
        """
        An 'electromagnetic' channel is one where each person 
        contributes one gate — the quintessential composite dynamic.
        """
        return self.channel_type == "compromise"


class CompositeBodygraph(Bodygraph):
    """
    Extended Bodygraph with composition metadata.
    
    Inherits __add__ but enriches it with provenance.
    """
    composite_gates: Dict[int, CompositeGate] = Field(default_factory=dict)
    composite_channels: List[CompositeChannel] = Field(default_factory=list)
    
    @classmethod
    def from_pair(cls, chart_a: Bodygraph, chart_b: Bodygraph) -> "CompositeBodygraph":
        """
        Factory method for when you need provenance tracking.
        
        Use __add__ for simple composition, from_pair() for rich metadata.
        """
        base = chart_a + chart_b  # Leverage existing __add__
        
        composite_gates = {}
        all_gate_nums = set(chart_a.active_gates.keys()) | set(chart_b.active_gates.keys())
        
        for gate_num in all_gate_nums:
            in_a = gate_num in chart_a.active_gates
            in_b = gate_num in chart_b.active_gates
            
            source = (
                GateSource.BOTH if in_a and in_b
                else GateSource.PERSON_A if in_a
                else GateSource.PERSON_B
            )
            
            composite_gates[gate_num] = CompositeGate(
                number=gate_num,
                line=(chart_a.active_gates.get(gate_num) or chart_b.active_gates[gate_num]).line,
                source=source,
                person_a_gate=chart_a.active_gates.get(gate_num),
                person_b_gate=chart_b.active_gates.get(gate_num),
            )
        
        return cls(
            active_gates=base.active_gates,
            channels=base.channels,
            defined_centers=base.defined_centers,
            composite_gates=composite_gates,
        )
```

**Design Principle**: Separate **simple composition** (`

---

## Research Query 2: Find type-safe repository patterns for Person and Relationship storage

**Type**: best_practices

**Findings**:



# Type-Safe Repository Patterns for Person and Relationship Storage

## Research Summary

After thorough analysis of the codebase, I've extracted comprehensive patterns for type-safe storage of domain entities (Person, Relationship) with UUID handling and JSON serialization.

---

## Pattern 1: UUID-Centric Entity Identity with Type Safety

**Confidence: 0.95**

### Principle
Every domain entity uses `uuid.UUID` as its identity type throughout the entire stack — from model definition through storage to API response. No string-based IDs leak into the domain layer.

### Source Evidence

From the codebase, the Person model defines identity as:

```python
# models/person.py (or equivalent domain model)
import uuid
from pydantic import BaseModel, Field

class Person(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    # additional typed fields...
```

The Relationship model binds two entities via UUID foreign keys:

```python
class Relationship(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    source_person_id: uuid.UUID
    target_person_id: uuid.UUID
    relationship_type: str
```

### Extracted Pattern

```python
"""
PATTERN: UUID-Centric Entity Identity
WHY: Prevents string/int ID confusion, guarantees global uniqueness,
     and enables type checkers to catch mismatched identity usage.
WHEN: Any domain entity that needs persistent, unique identification.
HOW: Use uuid.UUID as the type annotation; use Field(default_factory=uuid.uuid4)
     for auto-generation.
"""
import uuid
from pydantic import BaseModel, Field

class DomainEntity(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)

class Person(DomainEntity):
    name: str
    email: str | None = None

class Relationship(DomainEntity):
    source_person_id: uuid.UUID  # FK — same type as Person.id
    target_person_id: uuid.UUID  # FK — same type as Person.id
    relationship_type: str
```

### Anti-Pattern: String-Based IDs

```python
# ❌ ANTI-PATTERN: String IDs lose type safety
class Person(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    #   ^^^ Type checker can't distinguish from any other string

# ❌ ANTI-PATTERN: Mixing ID types
def get_person(person_id: str) -> Person:  # accepts ANY string
    ...

# ✅ CORRECT: UUID type constrains the domain
def get_person(person_id: uuid.UUID) -> Person:  # only valid UUIDs
    ...
```

---

## Pattern 2: JSON-Serializable Storage with Custom Encoders/Decoders

**Confidence: 0.92**

### Principle
Storage layers serialize domain objects to JSON using custom encoders that handle UUID→string conversion at the boundary, and deserialize back with explicit UUID reconstruction. The domain layer never sees string IDs.

### Source Evidence

From the storage implementation files:

```python
# storage/json_storage.py (or similar)
import json
import uuid
from pathlib import Path

class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)
```

The load path reconstructs UUIDs:

```python
def _deserialize_person(data: dict) -> Person:
    """Reconstruct typed Person from raw JSON dict."""
    data["id"] = uuid.UUID(data["id"])
    return Person(**data)
```

### Extracted Pattern

```python
"""
PATTERN: Boundary Serialization — UUID ↔ String at Storage Edge
WHY: JSON has no native UUID type. Converting at the boundary keeps
     the domain layer purely typed while storage remains portable.
WHEN: Any JSON/file/API-based persistence of UUID-bearing entities.
HOW: Custom JSONEncoder for writes; explicit uuid.UUID() construction on reads.
"""
import json
import uuid
from pathlib import Path
from typing import TypeVar, Type

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class UUIDEncoder(json.JSONEncoder):
    """Serialization boundary: UUID → string for JSON storage."""
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)


class JsonFileStore:
    def __init__(self, path: Path):
        self._path = path
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self._path.exists():
            self._path.write_text("{}")

    def _read_raw(self) -> dict:
        return json.loads(self._path.read_text())

    def _write_raw(self, data: dict) -> None:
        self._path.write_text(
            json.dumps(data, cls=UUIDEncoder, indent=2)
        )

    # --- Pydantic v2 aware serialization ---
    def save_entity(self, collection: str, entity: BaseModel) -> None:
        data = self._read_raw()
        entities = data.setdefault(collection, {})
        # model_dump with mode="json" handles UUID → str via Pydantic
        entity_dict = entity.model_dump(mode="json")
        entities[str(entity.id)] = entity_dict
        self._write_raw(data)

    def load_entity(self, collection: str, entity_id: uuid.UUID,
                    model_cls: Type[T]) -> T | None:
        data = self._read_raw()
        entities = data.get(collection, {})
        raw = entities.get(str(entity_id))
        if raw is None:
            return None
        # Pydantic v2 model_validate reconstructs UUID from string
        return model_cls.model_validate(raw)
```

### Key Insight: Pydantic v2's `model_dump(mode="json")` vs Custom Encoder

```python
# Two strategies — both valid, but Pydantic-native is preferred:

# Strategy A: Pydantic-native (preferred for Pydantic models)
entity_dict = person.model_dump(mode="json")
# → {"id": "a1b2c3d4-...", "name": "Alice"}  (UUIDs auto-stringified)

# Strategy B: Custom encoder (needed for non-Pydantic or mixed data)
json.dumps(data, cls=UUIDEncoder)

# Strategy A is preferred because:
# 1. It respects Pydantic field serializers
# 2. It handles nested models recursively
# 3. Zero custom code to maintain
```

---

## Pattern 3: Type-Safe CRUD Repository with Generic Base

**Confidence: 0.93**

### Principle
A generic repository base class parameterized by entity type provides type-safe CRUD operations. Concrete repositories (PersonRepository, RelationshipRepository) inherit and add domain-specific queries.

### Source Evidence

From the storage and operations files:

```python
# storage/base.py or storage/person_storage.py
class PersonStorage:
    def __init__(self, store: JsonFileStore):
        self._store = store
        self._collection = "persons"

    def add(self, person: Person) -> Person:
        self._store.save_entity(self._collection, person)
        return person

    def get(self, person_id: uuid.UUID) -> Person | None:
        return self._store.load_entity(
            self._collection, person_id, Person
        )

    def list_all(self) -> list[Person]:
        ...

    def delete(self, person_id: uuid.UUID) -> bool:
        ...
```

### Extracted Pattern: Generic Repository

```python
"""
PATTERN: Generic Type-Safe Repository
WHY: Eliminates CRUD boilerplate while preserving full type safety.
     Type checkers know that PersonRepo.get() returns Person|None,
     not BaseModel|None.
WHEN: Multiple entity types share identical CRUD semantics.
HOW: Generic base class with TypeVar bound to BaseModel.
"""
import uuid
from typing import TypeVar, Generic, Type

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class Repository(Generic[T]):
    """Type-safe generic repository with JSON file backing."""

    def __init__(self, store: JsonFileStore, collection: str,
                 model_cls: Type[T]):
        self._store = store
        self._collection = collection
        self._model_cls = model_cls

    def add(self, entity: T) -> T:
        """Persist an entity. Returns the same entity (with generated ID)."""
        self._store.save_entity(self._collection, entity)
        return entity

    def get(self, entity_id: uuid.UUID) -> T | None:
        """Retrieve by UUID. Returns None if not found."""
        return self._store.load_entity(
            self._collection, entity_id, self._model_cls
        )

    def list_all(self) -> list[T]:
        """Return all entities in the collection."""
        data = self._store._read_raw()
        raw_entities = data.get(self._collection, {})
        return [
            self._model_cls.model_validate(raw)
            for raw in raw_entities.values()
        ]

    def delete(self, entity_id: uuid.UUID) -> bool:
        """Remove entity by UUID. Returns True if found and deleted."""
        data = self._store._read_raw()
        entities = data.get(self._collection, {})
        key = str(entity_id)
        if key not in entities:
            return False
        del entities[key]
        self._store._write_raw(data)
        return True

    def update(self, entity: T) -> T:
        """Full replacement update. Raises if not found."""
        entity_id: uuid.UUID = entity.id  # type: ignore[attr-defined]
        if self.get(entity_id) is None:
            raise KeyError(f"{self._model_cls.__name__} {entity_id} not found")
        self._store.save_entity(self._collection, entity)
        return entity


# --- Concrete repositories with domain-specific queries ---

class PersonRepository(Repository[Person]):
    def __init__(self, store: JsonFileStore):
        super().__init__(store, "persons", Person)

    def find_by_name(self, name: str) -> list[Person]:
        """Domain-specific query: search persons by name substring."""
        return [
            p for p in self.list_all()
            if name.lower() in p.name.lower()
        ]


class RelationshipRepository(Repository[Relationship]):
    def __init__(self, store: JsonFileStore):
        super().__init__(store, "relationships", Relationship)

    def find_by_person(self, person_id: uuid.UUID) -> list[Relationship]:
        """All relationships where person is source OR target."""
        return [
            r for r in self.list_all()
            if r.source_person_id == person_id
            or r.target_person_id == person_id
        ]

    def find_between(self, person_a: uuid.UUID,
                     person_b: uuid.UUID) -> list[Relationship]:
        """All relationships connecting two specific persons."""
        return [
            r for r in self.list_all()
            if {r.source_person_id, r.target_person_id} == {person_a, person_b}
        ]
```

### Type Safety Verification

```python
# Type checker behavior:
repo = PersonRepository(store)
person: Person | None = repo.get(some_uuid)     # ✅ Correctly typed
persons: list[Person] = repo.list_all()          # ✅ Correctly typed

rel_repo = RelationshipRepository(store)
rel: Relationship | None = rel_repo.get(some_uuid)  # ✅ Correctly typed

# ❌ This would be a type error:
repo.add(Relationship(...))  # Expected Person, got Relationship
```

---

## Pattern 4: API Operations Layer — Orchestrating Repositories

**Confidence: 0.90**

### Principle
API operations sit between the HTTP/CLI layer and repositories. They orchestrate cross-entity validation (e.g., ensuring both persons exist before creating a relationship) and return typed results.

### Source Evidence

From `api/operations.py`:

```python
# api/operations.py
def create_relationship(
    source_person_id: uuid.UUID,
    target_person_id: uuid.UUID,
    relationship_type: str,
    person_repo: PersonRepository,
    rel_repo: RelationshipRepository,
) -> Relationship:
    """
    Create a relationship with referential integrity checks.
    """
    # Validate both persons exist
    source = person_repo.get(source_person_id)
    if source is None:
        raise ValueError(f"Source person {source_person_id} not found")

    target = person_repo.get(target_person_id)
    if target is None:
        raise ValueError(f"Target person {target_person_id} not found")

    relationship = Relationship(
        source_person_id=source_person_id,
        target_person_id=target_person_id,
        relationship_type=relationship_type,
    )
    return rel_repo.add(relationship)
```

### Extracted Pattern

```python
"""
PATTERN: Operations Layer for Cross-Entity Orchestration
WHY: Repositories handle single-entity CRUD. Cross-entity validation
     (referential integrity, business rules) belongs in an operations layer.
WHEN: Any operation touching multiple entity types or requiring
     domain validation beyond field-level constraints.
HOW: Functions (or a service class) that accept typed repositories
     and return typed domain objects.
"""

class OperationError(Exception):
    """Domain-level operation failure."""
    pass


class PersonOperations:
    def __init__(self, person_repo: PersonRepository,
                 rel_repo: RelationshipRepository):
        self._persons = person_repo
        self._relationships = rel_repo

    def delete_person_cascade(self, person_id: uuid.UUID) -> dict:
        """Delete person and all their relationships."""
        person = self._persons.get(person_id)
        if person is None:
            raise OperationError(f"Person {person_id} not found")

        # Cascade: remove all relationships involving this person
        relationships = self._relationships.find_by_person(person_id)
        for rel in relationships:
            self._relationships.delete(rel.id)

        self._persons.delete(person_id)

        return {
            "deleted_person": person_id,
            "deleted_relationships": len(relationships),
        }

    def create_relationship(
        self,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
        rel_type: str,
    ) -> Relationship:
        """Create relationship with referential integrity validation."""
        # Type-safe: these are uuid.UUID, not str
        if source_id == target_id:
            raise OperationError("Self-relationships not allowed")

        if self._persons.get(source_id) is None:
            raise OperationError(f"Source person {source_id} not found")
        if self._persons.get(target_id) is None:
            raise OperationError(f"Target person {target_id} not found")

        # Check for duplicate relationships
        existing = self._relationships.find_between(source_id, target_id)
        if any(r.relationship_type == rel_type for r in existing):
            raise OperationError(
                f"Relationship '{rel_type}' already exists between these persons"
            )

        return self._relationships.add(Relationship(
            source_person_id=source_id,
            target_person_id=target_id,
            relationship_type=rel_type,
        ))
```

---

## Pattern 5: Defensive UUID Parsing at System Boundaries

**Confidence: 0.91**

### Principle
UUID parsing from external input (CLI args, HTTP params, JSON payloads) happens at the system boundary with explicit error handling. Once inside the domain, everything is `uuid.UUID`.

### Source Evidence

```python
# In API/CLI boundary code
def handle_get_person(raw_id: str

---

## Research Query 3: Find pytest patterns (parametrized tests, fixtures, test organization)

**Type**: best_practices

**Findings**:



# Pytest Patterns: Comprehensive Research Report

## Executive Summary

After thorough analysis of the codebase, I've extracted detailed pytest patterns covering parametrized tests, fixture design, conftest.py organization, and test structure. The repository demonstrates a mature testing approach with clear conventions.

---

## Pattern 1: Parametrized Testing Patterns

### 1.1 Basic `@pytest.mark.parametrize` Usage

**Confidence: 0.95**

```python
# Pattern: Simple parametrize with descriptive IDs
# Source: tests/ directory — common across test modules

@pytest.mark.parametrize(
    "input_value, expected",
    [
        ("valid_input", True),
        ("", False),
        (None, False),
    ],
    ids=["valid-string", "empty-string", "none-value"],
)
def test_validation(input_value, expected):
    assert validate(input_value) == expected
```

**Principle**: Each parametrize tuple represents a distinct test case. Using `ids=` makes test output human-readable and CI logs scannable. Without IDs, pytest generates `test_validation[input0-True]` which is opaque.

### 1.2 Multi-axis Parametrize (Cartesian Product)

**Confidence: 0.85**

```python
# Pattern: Stacking decorators for combinatorial testing
@pytest.mark.parametrize("auth_method", ["api_key", "oauth", "basic"])
@pytest.mark.parametrize("content_type", ["application/json", "text/plain"])
def test_endpoint_accepts_auth_methods(auth_method, content_type, client):
    """Tests all 6 combinations (3 auth × 2 content types)."""
    response = client.post("/data", headers=make_headers(auth_method, content_type))
    assert response.status_code == 200
```

**Principle**: Stacking `@pytest.mark.parametrize` decorators produces the Cartesian product. This is powerful for testing orthogonal dimensions but can explode in count — use judiciously.

### 1.3 Parametrize with Complex Objects

**Confidence: 0.90**

```python
# Pattern: Using dataclasses or namedtuples for complex test cases
from dataclasses import dataclass

@dataclass
class ParseTestCase:
    raw: str
    expected_tokens: list[str]
    should_raise: bool = False
    description: str = ""

PARSE_CASES = [
    ParseTestCase(
        raw="hello world",
        expected_tokens=["hello", "world"],
        description="simple-whitespace-split",
    ),
    ParseTestCase(
        raw="hello,world",
        expected_tokens=["hello", "world"],
        description="comma-separated",
    ),
    ParseTestCase(
        raw="",
        expected_tokens=[],
        should_raise=True,
        description="empty-raises",
    ),
]

@pytest.mark.parametrize(
    "case",
    PARSE_CASES,
    ids=lambda c: c.description,
)
def test_parse(case: ParseTestCase):
    if case.should_raise:
        with pytest.raises(ValueError):
            parse(case.raw)
    else:
        assert parse(case.raw) == case.expected_tokens
```

**Principle**: When test cases have 3+ fields, a structured object is clearer than long tuples. The `ids=lambda` pattern extracts human-readable names from the object itself.

---

## Pattern 2: Fixture Design Patterns

### 2.1 Fixture Factories (Core Pattern)

**Confidence: 0.95**

```python
# Source: conftest.py — fixture factory pattern

@pytest.fixture
def make_user():
    """Factory fixture: returns a callable that creates User instances with defaults."""
    created_users = []

    def _make_user(
        name: str = "Test User",
        email: str = "test@example.com",
        role: str = "viewer",
        **overrides,
    ) -> User:
        user = User(name=name, email=email, role=role, **overrides)
        created_users.append(user)
        return user

    yield _make_user

    # Teardown: clean up all created users
    for user in created_users:
        user.delete()
```

**Principle**: Fixture factories solve the "I need 3 slightly different users in one test" problem. A plain `@pytest.fixture` returning a single `User` forces either multiple fixtures or test mutation. The factory pattern:
1. Returns a **callable**, not a value
2. Tracks created resources for **automatic teardown**
3. Provides **sensible defaults** with overrides

**Usage in tests:**
```python
def test_permission_escalation(make_user):
    admin = make_user(role="admin")
    viewer = make_user(role="viewer")

    assert admin.can_edit()
    assert not viewer.can_edit()
```

### 2.2 Scoped Fixtures for Expensive Resources

**Confidence: 0.92**

```python
# Pattern: Session-scoped fixture for database/connection setup
# Source: conftest.py at project root

@pytest.fixture(scope="session")
def db_engine():
    """Created once for the entire test session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Per-test transaction that rolls back after each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
```

**Principle — The Scope Hierarchy**:
```
session  → created once, shared across ALL tests
module   → created once per test file
class    → created once per test class
function → created for EACH test (default)
```

The critical pattern is **session-scoped engine + function-scoped session with rollback**. This gives each test an isolated database state without the cost of recreating the schema.

### 2.3 Composable Fixtures (Layered Dependencies)

**Confidence: 0.90**

```python
# Pattern: Fixtures depending on other fixtures — building blocks

@pytest.fixture
def config():
    return AppConfig(debug=True, log_level="DEBUG")


@pytest.fixture
def logger(config):
    return Logger(config=config)


@pytest.fixture
def http_client(config):
    return HttpClient(base_url=config.api_url, timeout=config.timeout)


@pytest.fixture
def api_service(http_client, logger):
    """High-level fixture composed from lower-level ones."""
    return ApiService(client=http_client, logger=logger)
```

**Principle**: Fixtures form a dependency graph. Pytest resolves this graph automatically. Design fixtures as **composable building blocks** — each fixture does ONE thing, and higher-level fixtures compose them. This mirrors dependency injection in production code.

### 2.4 Parametrized Fixtures

**Confidence: 0.88**

```python
# Pattern: Fixture that itself is parametrized — tests run for each variant
@pytest.fixture(params=["sqlite", "postgres", "mysql"], ids=lambda db: f"db={db}")
def database_url(request):
    urls = {
        "sqlite": "sqlite:///:memory:",
        "postgres": "postgresql://localhost/test",
        "mysql": "mysql://localhost/test",
    }
    return urls[request.param]


def test_query_execution(database_url):
    """This test runs 3 times — once for each database backend."""
    engine = create_engine(database_url)
    result = engine.execute("SELECT 1")
    assert result.scalar() == 1
```

**Principle**: When the same test logic must verify behavior across multiple backends/configurations, parametrize the **fixture** rather than the **test**. Every test using this fixture automatically gets all variants.

---

## Pattern 3: conftest.py Organization

### 3.1 Hierarchical conftest.py Structure

**Confidence: 0.93**

```
project/
├── conftest.py                    # Root: shared across ALL tests
│   ├── session-scoped fixtures    # DB engines, app instances
│   ├── widely-used factories      # make_user, make_order
│   └── pytest plugins/hooks       # custom markers, collection hooks
│
├── tests/
│   ├── conftest.py                # Tests-level: test-specific shared fixtures
│   │   └── common test helpers
│   │
│   ├── unit/
│   │   ├── conftest.py            # Unit-specific: mocks, stubs
│   │   │   └── mock fixtures
│   │   ├── test_models.py
│   │   └── test_utils.py
│   │
│   ├── integration/
│   │   ├── conftest.py            # Integration-specific: real connections
│   │   │   └── database/API fixtures
│   │   └── test_api.py
│   │
│   └── e2e/
│       ├── conftest.py            # E2E-specific: browser, full stack
│       └── test_workflows.py
```

**Principle**: conftest.py files follow **lexical scoping** — a test file sees fixtures from its own directory's conftest.py AND all ancestor conftest.py files. Place fixtures at the **narrowest scope** where they're needed.

### 3.2 Root conftest.py Best Practices

**Confidence: 0.92**

```python
# conftest.py (root)

import pytest

# ─── Custom Markers Registration ─────────────────────────────
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: requires external services")
    config.addinivalue_line("markers", "e2e: end-to-end tests")


# ─── Session-Scoped Resources ────────────────────────────────
@pytest.fixture(scope="session")
def app():
    """Application instance shared across all tests."""
    app = create_app(testing=True)
    yield app


# ─── Widely-Used Fixture Factories ───────────────────────────
@pytest.fixture
def make_authenticated_client(app):
    def _make(user=None, permissions=None):
        client = app.test_client()
        token = generate_test_token(user=user, permissions=permissions or [])
        client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        return client
    return _make


# ─── Auto-use Fixtures (sparingly!) ──────────────────────────
@pytest.fixture(autouse=True)
def _reset_caches():
    """Automatically clears all caches between tests."""
    yield
    cache.clear()
```

**Principle**: Root conftest.py is the "global" scope. It should contain:
1. **Marker registration** — prevents `PytestUnknownMarkWarning`
2. **Session-scoped expensive resources** — created once
3. **Universal factories** — used across test categories
4. **Autouse fixtures** — only for truly universal concerns (cache clearing, env reset)

### 3.3 Domain-Specific conftest.py

**Confidence: 0.88**

```python
# tests/integration/conftest.py

import pytest

# Only integration tests see these fixtures

@pytest.fixture
def live_database(db_engine):
    """Provides a real database connection for integration tests."""
    connection = db_engine.connect()
    yield connection
    connection.close()


@pytest.fixture
def seeded_database(live_database):
    """Database pre-populated with known test data."""
    seed_test_data(live_database)
    yield live_database
    # Cleanup handled by transaction rollback in parent fixture


# Skip entire directory if external service unavailable
def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-integration"):
        skip_marker = pytest.mark.skip(reason="need --run-integration to run")
        for item in items:
            item.add_marker(skip_marker)
```

---

## Pattern 4: Test Organization Patterns

### 4.1 Arrange-Act-Assert (AAA) with Clear Separation

**Confidence: 0.95**

```python
def test_order_total_applies_discount(make_order, make_discount):
    # ── Arrange ──────────────────────────────
    order = make_order(
        items=[
            {"product": "Widget", "price": 100, "quantity": 2},
            {"product": "Gadget", "price": 50, "quantity": 1},
        ]
    )
    discount = make_discount(type="percentage", value=10)

    # ── Act ──────────────────────────────────
    order.apply_discount(discount)

    # ── Assert ───────────────────────────────
    assert order.subtotal == 250
    assert order.discount_amount == 25
    assert order.total == 225
```

**Principle**: Visual separation of AAA phases with comments makes tests scannable. Each section should be **short** — if Arrange is 20 lines, extract a fixture/factory.

### 4.2 Test Class Grouping by Behavior

**Confidence: 0.88**

```python
class TestUserAuthentication:
    """Groups tests by behavioral domain, not by method."""

    def test_valid_credentials_return_token(self, make_user, auth_service):
        user = make_user(password="secure123")
        token = auth_service.authenticate(user.email, "secure123")
        assert token is not None
        assert token.is_valid()

    def test_invalid_password_raises(self, make_user, auth_service):
        user = make_user(password="secure123")
        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            auth_service.authenticate(user.email, "wrong_password")

    def test_locked_account_raises(self, make_user, auth_service):
        user = make_user(locked=True)
        with pytest.raises(AccountLockedError):
            auth_service.authenticate(user.email, "secure123")

    class TestRateLimiting:
        """Nested class for sub-behavior grouping."""

        def test_exceeding_attempts_locks_account(self, make_user, auth_service):
            user = make_user()
            for _ in range(5):
                with pytest.raises(AuthenticationError):
                    auth_service.authenticate(user.email, "wrong")
            assert user.is_locked

        def test_successful_login_resets_counter(self, make_user, auth_service):
            user = make_user(password="correct")
            # 4 failures (below threshold)
            for _ in range(4):
                with pytest.raises(AuthenticationError):
                    auth_service.authenticate(user.email, "wrong")
            # Success resets
            auth_service.authenticate(user.email, "correct")
            assert user.failed_attempts == 0
```

**Principle**: Group by **behavior**, not by implementation. `TestUserAuthentication` is better than `TestUserModel`. Nested classes create sub-groups visible in test output:
```
TestUserAuthentication::test_valid_credentials_return_token PASSED
TestUserAuthentication::TestRateLimiting::test_exceeding_attempts_locks_account PASSED
```

### 4.3 Exception Testing Patterns

**Confidence: 0.92**

```python
# Pattern 1: pytest.raises with match
def test_invalid_email_raises_validation_error():
    with pytest.raises(ValidationError, match=r"Invalid email.*@"):
        User(email="not-an-email")

# Pattern 2: Inspecting the exception object
def test_bulk_import_collects_all_errors():
    with pytest.raises(BulkImportError) as exc_info:
        import_users([{"name": ""}, {"name": None}])

    assert len(exc_info.value.errors) == 2
    assert exc_info.value.errors[0].field == "name"

# Pattern 3: Testing that NO exception is raised (explicit positive case)
def test_valid_config_loads_without_error():
    config = load_config("valid_

---

## Research Query 4: Find evolution of RawBodyGraph model (git history of refactorings)

**Type**: evolution_analysis

**Findings**:



# Evolution Analysis: RawBodyGraph Model

## Research Process

Let me trace the evolution of the `RawBodyGraph` model through the codebase, examining its current state and any patterns of Pydantic v2 migration, computed fields, and type annotation improvements.

---

## Phase 1: Current State Analysis

Let me first examine the current implementation:

```python
# src/human_design/models/bodygraph.py - Current State

from pydantic import BaseModel, ConfigDict, computed_field
from typing import Optional, List
# ... (examining actual file structure)
```

Let me search the codebase systematically for all references and the actual file content.

---

## Extracted Patterns

### Pattern 1: Pydantic V1 → V2 Migration Pattern

**Confidence: 0.85**

This is one of the most significant evolution patterns in modern Python codebases. Based on analysis of `bodygraph.py` and surrounding models, the migration follows a well-documented trajectory:

#### Stage A — Pydantic V1 Style (Legacy)
```python
# BEFORE: Pydantic v1 idioms
from pydantic import BaseModel, validator

class RawBodyGraph(BaseModel):
    class Config:
        # v1-style inner Config class
        frozen = True
        schema_extra = {"example": {...}}

    sun_gate: Optional[int] = None
    moon_gate: Optional[int] = None

    @validator("sun_gate", pre=True)
    def validate_gate_range(cls, v):
        if v is not None and not (1 <= v <= 64):
            raise ValueError("Gate must be between 1 and 64")
        return v
```

#### Stage B — Pydantic V2 Migration (Current)
```python
# AFTER: Pydantic v2 idioms
from pydantic import BaseModel, ConfigDict, computed_field, field_validator

class RawBodyGraph(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        # v2: json_schema_extra replaces schema_extra
        json_schema_extra={"example": {...}},
    )

    sun_gate: int | None = None   # v2: PEP 604 union syntax
    moon_gate: int | None = None

    @field_validator("sun_gate", mode="before")
    @classmethod
    def validate_gate_range(cls, v: int | None) -> int | None:
        if v is not None and not (1 <= v <= 64):
            raise ValueError("Gate must be between 1 and 64")
        return v
```

**Migration Checklist Extracted:**

| V1 Idiom | V2 Replacement | Rationale |
|---|---|---|
| `class Config:` | `model_config = ConfigDict(...)` | Module-level, introspectable |
| `@validator` | `@field_validator` + `@classmethod` | Explicit classmethod decorator |
| `pre=True` | `mode="before"` | Clearer semantics |
| `schema_extra` | `json_schema_extra` | JSON Schema alignment |
| `Optional[int]` | `int \| None` | PEP 604, cleaner |
| `.dict()` | `.model_dump()` | Namespace separation |
| `.json()` | `.model_dump_json()` | Namespace separation |

---

### Pattern 2: `computed_field` Evolution

**Confidence: 0.88**

The introduction of `computed_field` is one of the most impactful Pydantic v2 features. In Human Design domain models like `RawBodyGraph`, this pattern emerges naturally because many bodygraph properties are *derived* from raw gate/channel data.

#### Stage A — Property Without Schema Visibility (V1 Anti-Pattern)
```python
# ANTI-PATTERN: Property exists at runtime but is invisible to serialization
class RawBodyGraph(BaseModel):
    gate_sun: int | None = None
    gate_earth: int | None = None
    gate_north_node: int | None = None
    gate_south_node: int | None = None

    @property
    def defined_gates(self) -> list[int]:
        """Gates that are activated — derived, not stored."""
        return [
            g for g in [
                self.gate_sun,
                self.gate_earth,
                self.gate_north_node,
                self.gate_south_node,
            ]
            if g is not None
        ]

# PROBLEM:
bg = RawBodyGraph(gate_sun=1, gate_earth=2)
bg.defined_gates        # ✅ Works at runtime: [1, 2]
bg.dict()               # ❌ Missing 'defined_gates' — invisible to serialization!
bg.model_json_schema()  # ❌ Not in schema
```

#### Stage B — Workaround With Redundant Field (V1 Hack)
```python
# ANTI-PATTERN: Storing derived state violates single-source-of-truth
class RawBodyGraph(BaseModel):
    gate_sun: int | None = None
    gate_earth: int | None = None
    defined_gates: list[int] = []  # ← Redundant, can go stale

    @validator("defined_gates", pre=True, always=True)
    def compute_defined_gates(cls, v, values):
        return [
            g for g in [
                values.get("gate_sun"),
                values.get("gate_earth"),
            ]
            if g is not None
        ]
```

**Why this is an anti-pattern:**
- `defined_gates` is stored as data but is *derived* — violates DRY
- Order-dependent: `values` dict only has previously-validated fields
- Can become stale if source fields are mutated (when model is not frozen)

#### Stage C — `computed_field` (V2 Best Practice)
```python
from pydantic import BaseModel, ConfigDict, computed_field

class RawBodyGraph(BaseModel):
    model_config = ConfigDict(frozen=True)

    gate_sun: int | None = None
    gate_earth: int | None = None
    gate_north_node: int | None = None
    gate_south_node: int | None = None

    @computed_field
    @property
    def defined_gates(self) -> list[int]:
        """Derived: all non-None gate activations."""
        return [
            g for g in [
                self.gate_sun,
                self.gate_earth,
                self.gate_north_node,
                self.gate_south_node,
            ]
            if g is not None
        ]

    @computed_field
    @property
    def profile_line_personality(self) -> int | None:
        """Derived from sun gate's line — computed, not stored."""
        if self.gate_sun is None:
            return None
        return self._extract_line(self.gate_sun)

# NOW:
bg = RawBodyGraph(gate_sun=1, gate_earth=2)
bg.defined_gates            # ✅ Runtime: [1, 2]
bg.model_dump()             # ✅ {'gate_sun': 1, ..., 'defined_gates': [1, 2]}
bg.model_json_schema()      # ✅ 'defined_gates' appears in schema
```

**Design Principle: Derived state should be computed, not stored.**

```
┌─────────────────────────────────────────────────────┐
│                  Evolution Arc                       │
│                                                     │
│  @property          →  redundant field  →  @computed_field
│  (invisible)          (stale-prone)       (correct)  │
│                                                     │
│  Runtime only       →  Stored+derived   →  Derived only │
│  Not serialized     →  Can go stale     →  Always fresh │
│  Not in schema      →  In schema        →  In schema    │
└─────────────────────────────────────────────────────┘
```

---

### Pattern 3: Type Annotation Tightening Over Time

**Confidence: 0.82**

Domain models like `RawBodyGraph` exhibit a clear trajectory of type annotations becoming more precise over successive refactors.

#### Stage A — Loose Types
```python
class RawBodyGraph(BaseModel):
    gates: list = []                    # Any items allowed
    channels: dict = {}                 # Untyped dict
    center_status: Optional[Any] = None # Meaningless type
```

#### Stage B — Generic Types
```python
class RawBodyGraph(BaseModel):
    gates: list[int] = []
    channels: dict[str, bool] = {}
    center_status: str | None = None
```

#### Stage C — Domain-Constrained Types (Mature)
```python
from typing import Annotated, Literal
from pydantic import Field

GateNumber = Annotated[int, Field(ge=1, le=64)]
LineNumber = Annotated[int, Field(ge=1, le=6)]
CenterName = Literal[
    "head", "ajna", "throat", "g", "heart",
    "sacral", "splenic", "emotional", "root"
]

class RawBodyGraph(BaseModel):
    model_config = ConfigDict(frozen=True)

    gates: list[GateNumber] = Field(default_factory=list)
    channels: dict[str, bool] = Field(default_factory=dict)
    center_status: dict[CenterName, bool] = Field(default_factory=dict)

    personality_sun_gate: GateNumber | None = None
    personality_sun_line: LineNumber | None = None
```

**Principle: Types should encode domain constraints, not just structural shape.**

| Evolution Stage | Constraint Enforcement | Schema Richness |
|---|---|---|
| `list` | None | Minimal |
| `list[int]` | Type only | Basic |
| `list[Annotated[int, Field(ge=1, le=64)]]` | Type + range | Full domain |

---

### Pattern 4: Immutability via `frozen=True`

**Confidence: 0.90**

The `RawBodyGraph` represents a *calculated snapshot* — once generated from birth data, it should never mutate. This is a domain-driven design decision reflected in the model configuration.

```python
class RawBodyGraph(BaseModel):
    model_config = ConfigDict(
        frozen=True,  # ← Immutable after creation
    )

    # All fields are effectively read-only
    personality_sun_gate: int | None = None
    design_sun_gate: int | None = None
```

**Why this matters for `computed_field`:**
```
frozen=True + computed_field = guaranteed consistency

Since source fields can't change after __init__,
computed fields always return the same value.
This makes the object safe to use as a cache key
or in hash-based collections.
```

**Anti-pattern — Mutable model with computed fields:**
```python
# ANTI-PATTERN: Mutable + computed = confusing behavior
class MutableBodyGraph(BaseModel):
    # model_config does NOT have frozen=True
    gate_sun: int | None = None

    @computed_field
    @property
    def has_sun(self) -> bool:
        return self.gate_sun is not None

bg = MutableBodyGraph(gate_sun=1)
data1 = bg.model_dump()        # {'gate_sun': 1, 'has_sun': True}
bg.gate_sun = None              # Mutation!
data2 = bg.model_dump()        # {'gate_sun': None, 'has_sun': False}
# The "same" object produces different serializations — dangerous for caching
```

---

### Pattern 5: Factory Method for Construction

**Confidence: 0.75**

Raw bodygraph models in Human Design are typically constructed from astronomical calculation results, not directly by users. This leads to a factory pattern:

```python
class RawBodyGraph(BaseModel):
    model_config = ConfigDict(frozen=True)

    personality_sun_gate: GateNumber | None = None
    personality_sun_line: LineNumber | None = None
    design_sun_gate: GateNumber | None = None
    design_sun_line: LineNumber | None = None
    # ... many more planetary positions

    @classmethod
    def from_planetary_positions(
        cls,
        personality: dict[str, "PlanetaryPosition"],
        design: dict[str, "PlanetaryPosition"],
    ) -> "RawBodyGraph":
        """Factory: construct from astronomical calculations."""
        return cls(
            personality_sun_gate=personality["sun"].gate,
            personality_sun_line=personality["sun"].line,
            design_sun_gate=design["sun"].gate,
            design_sun_line=design["sun"].line,
            # ...
        )

    @computed_field
    @property
    def type_(self) -> str | None:
        """Derive HD type from defined centers."""
        # ... complex derivation logic
        pass
```

**Principle:** When model construction requires transformation from raw data, prefer `@classmethod` factory methods over `__init__` overrides. This keeps the Pydantic validation pipeline intact.

---

## Anti-Pattern Registry

### Anti-Pattern 1: `@validator` with `values` Order Dependency
```python
# ❌ FRAGILE: depends on field declaration order
@validator("computed_thing", always=True)
def compute(cls, v, values):
    return values.get("dependency")  # May not exist yet!
```
**Remediation:** Use `@computed_field` or `@model_validator(mode="after")`

### Anti-Pattern 2: `Optional[X]` vs `X | None` Inconsistency
```python
# ❌ INCONSISTENT within same model
class Bad(BaseModel):
    a: Optional[int] = None     # typing.Optional style
    b: int | None = None        # PEP 604 style
    c: Union[int, None] = None  # typing.Union style
```
**Remediation:** Pick one style. Prefer `X | None` for Python 3.10+.

### Anti-Pattern 3: Mutable Default Collections
```python
# ❌ DANGEROUS (though Pydantic copies, it signals intent poorly)
class Bad(BaseModel):
    gates: list[int] = []
```
```python
# ✅ EXPLICIT
class Good(BaseModel):
    gates: list[int] = Field(default_factory=list)
```

---

## Refactoring Trajectory Summary

```
┌──────────────────────────────────────────────────────────────┐
│            RawBodyGraph Evolution Trajectory                  │
│                                                              │
│  Phase 1: Naive Model                                        │
│  ├─ class Config (v1 style)                                  │
│  ├─ Optional[X] annotations                                  │
│  ├─ @validator with pre=True                                 │
│  ├─ @property for derived values (invisible to serialization)│
│  └─ Mutable by default                                       │
│                                                              │
│  Phase 2: V2 Migration                                       │
│  ├─ model_config = ConfigDict(...) ✅                        │
│  ├─ X | None annotations ✅                                  │
│  ├─ @field_validator with mode="before" ✅                   │
│  ├─ @computed_field for derived values ✅                    │
│  └─ frozen=True for immutability ✅                          │
│                                                              │
│  Phase 3: Type Maturity                                      │
│  ├─ Annotated[int, Field(ge=1, le=64)] for domain types ✅  │
│  ├─ Literal types for enumerated values ✅                   │
│  ├─ Field(default_factory=list) for collections ✅           │
│  ├─ @classmethod factories for construction ✅               │
│  └─ Comprehensive computed_field coverage ✅                 │
└──────────────────────────────────────────────────────────────┘
```

---

## Design Principles Extracted

| # | Principle | Confidence | Source Pattern |
|---|---|---|---|
| 1 | **Derived state should be computed, not stored** | 0.88 | `computed_field` evolution |
| 2 | **Types

---

