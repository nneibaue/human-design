# ADR 001: API Layer Architecture for Human Design Chart Operations

**Status**: Proposed  
**Date**: 2024-01-XX  
**Architects**: System Design Team  
**Stakeholders**: Rebecca (primary user), developers

---

## Context

We have working core models (`RawBodyGraph`, `CompositeBodyGraph`, `Transit`) with elegant `__add__` operator composition:
```python
interaction = chart1 + chart2
penta = chart1 + chart2 + chart3 + chart4
with_transit = chart + Transit.now()
```

**Current State**:
- ✅ Core calculation logic works
- ✅ `__add__` operator pattern is clean and extensible
- ❌ No storage layer for people/relationships
- ❌ CLI commands are ~90 lines each (should be <10)
- ❌ No API layer to abstract operations
- ❌ Can't easily recall "Sandy + Heath interaction" or "Sandy's family penta"

**Rebecca's Workflow Need**:
> "During client sessions, I need to quickly pull up chart combinations:
> - Show me Sandy and Heath's interaction chart
> - Pull up Sandy's family penta (Sandy, Heath, daughter, son)
> - Show Sandy's chart with today's transit"

**Key Constraints**:
1. **Testability**: API layer must be testable without CLI
2. **Tagged Storage**: Support tags like "Sandy's group", "Heath (husband)"
3. **Thin CLI**: Commands must be < 10 lines (wrappers over API)
4. **Preserve __add__**: Don't break existing operator pattern
5. **Type Safety**: Full type hints, IDE autocomplete, mypy compliance

---

## Decision

### 1. **Three-Layer Architecture**

```
┌─────────────────────────────────────┐
│   CLI Layer (Typer commands)       │  ← Thin wrappers (<10 lines)
│   • hd person add/list/show         │
│   • hd interaction/penta/transit    │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   API Layer (Python functions)      │  ← Business logic
│   • add_person()                    │
│   • get_person()                    │
│   • create_interaction()            │
│   • create_penta()                  │
│   • add_transit()                   │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   Storage Layer (Repository)        │  ← Data persistence
│   • PersonRepository                │
│   • RelationshipRepository          │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   Core Models (existing)            │  ← Calculations
│   • RawBodyGraph                    │
│   • CompositeBodyGraph              │
│   • Transit                         │
└─────────────────────────────────────┘
```

### 2. **Storage Models** (New Pydantic Models)

```python
# src/human_design/storage/models.py

class StoredPerson(BaseModel):
    """A person with birth info and tags for quick recall."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(description="Full name (e.g., 'Sandy Rodriguez')")
    tags: list[str] = Field(
        default_factory=list,
        description="Tags for grouping (e.g., 'family', 'client', 'Sandy's group')"
    )
    birth_info: BirthInfo
    created_at: datetime = Field(default_factory=datetime.now)
    
    @computed_field
    @property
    def chart(self) -> RawBodyGraph:
        """Calculate bodygraph on demand."""
        return RawBodyGraph(birth_info=self.birth_info)


class StoredRelationship(BaseModel):
    """A saved relationship (interaction, penta, etc) with metadata."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(description="Relationship name (e.g., 'Sandy + Heath')")
    person_ids: list[UUID] = Field(min_length=2)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    
    @computed_field
    @property
    def chart_type(self) -> str:
        """Classify based on number of people."""
        count = len(self.person_ids)
        if count == 2:
            return "interaction"
        elif 3 <= count <= 5:
            return "penta"
        else:
            return "multichart"
```

### 3. **Storage Repository** (File-based JSON)

```python
# src/human_design/storage/repository.py

class PersonRepository:
    """Repository for person storage with tag-based queries."""
    
    def __init__(self, storage_path: Path = Path.home() / ".human-design" / "people.json"):
        self.storage_path = storage_path
    
    def add(self, person: StoredPerson) -> StoredPerson:
        """Add person to storage."""
        
    def get(self, person_id: UUID) -> StoredPerson | None:
        """Get person by ID."""
        
    def find_by_name(self, name: str) -> StoredPerson | None:
        """Find person by exact name."""
        
    def search_by_name(self, query: str) -> list[StoredPerson]:
        """Fuzzy search by name."""
        
    def find_by_tag(self, tag: str) -> list[StoredPerson]:
        """Find all people with tag."""
        
    def list_all(self) -> list[StoredPerson]:
        """List all people."""
```

**Why JSON file storage?**
- Simple, no database setup
- Human-readable for debugging
- Easy backup (just copy file)
- Sufficient for Rebecca's use case (dozens of people, not thousands)
- Can migrate to SQLite later if needed (same API)

### 4. **API Layer Functions** (Type-safe, testable)

```python
# src/human_design/api/operations.py

def add_person(
    name: str,
    birth_info: BirthInfo,
    tags: list[str] | None = None,
    repo: PersonRepository | None = None
) -> StoredPerson:
    """Add person to storage.
    
    Args:
        name: Full name
        birth_info: Birth information
        tags: Optional tags for grouping
        repo: Repository (defaults to standard location)
        
    Returns:
        StoredPerson with generated ID
        
    Example:
        >>> sandy = add_person(
        ...     name="Sandy Rodriguez",
        ...     birth_info=BirthInfo(...),
        ...     tags=["client", "family"]
        ... )
    """


def get_interaction(
    person1: str | UUID,
    person2: str | UUID,
    repo: PersonRepository | None = None
) -> CompositeBodyGraph:
    """Create interaction chart between two people.
    
    Args:
        person1: Name or UUID of first person
        person2: Name or UUID of second person
        repo: Repository (defaults to standard location)
        
    Returns:
        Composite bodygraph showing interaction
        
    Example:
        >>> interaction = get_interaction("Sandy", "Heath")
        >>> print(interaction.emergent_channels())
    """


def get_penta(
    people: list[str | UUID],
    repo: PersonRepository | None = None
) -> CompositeBodyGraph:
    """Create penta/multichart from multiple people.
    
    Args:
        people: List of names or UUIDs (3-16 people)
        repo: Repository
        
    Returns:
        Composite bodygraph
        
    Example:
        >>> family = get_penta(["Sandy", "Heath", "daughter", "son"])
        >>> print(family.defined_centers)
    """


def add_transit_to_person(
    person: str | UUID,
    transit: Transit | None = None,
    repo: PersonRepository | None = None
) -> CompositeBodyGraph:
    """Add transit overlay to person's chart.
    
    Args:
        person: Name or UUID
        transit: Transit (defaults to Transit.now())
        repo: Repository
        
    Returns:
        Chart with transit overlay
        
    Example:
        >>> now_chart = add_transit_to_person("Sandy")
        >>> specific = add_transit_to_person(
        ...     "Sandy", 
        ...     Transit.at(datetime(2024, 6, 21))
        ... )
    """
```

### 5. **CLI Commands** (Thin wrappers)

```python
# src/human_design/cli.py (additions)

@app.command()
def person_add(
    name: str,
    date: str,
    time: str,
    city: str,
    state: str,
    tags: str = typer.Option("", help="Comma-separated tags")
) -> None:
    """Add person to storage."""
    birth_info = BirthInfo(...)
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    person = api.add_person(name, birth_info, tag_list)
    typer.echo(f"✓ Added {person.name} (ID: {person.id})")


@app.command()
def interaction(person1: str, person2: str) -> None:
    """Show interaction chart between two people."""
    chart = api.get_interaction(person1, person2)
    typer.echo(chart.model_dump_json(indent=2))


@app.command()
def penta(*people: str) -> None:
    """Show penta/multichart for group."""
    chart = api.get_penta(list(people))
    typer.echo(chart.model_dump_json(indent=2))
```

---

## Rationale

### Why This Architecture?

**1. Separation of Concerns**
- **CLI**: User interface only (parsing args, formatting output)
- **API**: Business logic (orchestration, error handling)
- **Storage**: Persistence (CRUD operations)
- **Models**: Calculations (existing, unchanged)

**2. Testability**
```python
# Test API without CLI
def test_interaction():
    repo = PersonRepository(Path("/tmp/test.json"))
    p1 = add_person("Test1", birth_info1, repo=repo)
    p2 = add_person("Test2", birth_info2, repo=repo)
    chart = get_interaction(p1.id, p2.id, repo=repo)
    assert isinstance(chart, CompositeBodyGraph)
```

**3. Flexibility**
- Repository interface allows swapping storage (JSON → SQLite)
- API functions work from CLI, web UI, or Jupyter notebooks
- Tag system allows freeform organization

**4. Type Safety**
- All functions fully typed
- `str | UUID` union allows both lookup methods
- Pydantic models validate at boundaries

**5. Preserves Existing Patterns**
- `__add__` operator still works
- API layer uses it internally:
  ```python
  def get_interaction(p1, p2, repo):
      person1 = repo.get(p1)
      person2 = repo.get(p2)
      return person1.chart + person2.chart  # Uses __add__
  ```

---

## Consequences

### Positive

✅ **Rebecca can recall charts by name**: `hd interaction Sandy Heath`  
✅ **Tags enable flexible grouping**: Find all "Sandy's group" or "client"  
✅ **CLI commands are tiny**: Each <10 lines, easy to read/maintain  
✅ **API is reusable**: Works from CLI, web, notebooks  
✅ **Type-safe throughout**: IDE autocomplete, mypy checks pass  
✅ **Testable without CLI**: Unit test business logic directly  
✅ **Extensible**: Add SQLite, caching, or analytics layer later  

### Negative

⚠️ **File-based storage limitations**:
- No concurrent writes (single user only)
- Linear search performance (fine for <1000 people)
- Migration: JSON → SQLite if scale needed

⚠️ **Name ambiguity**: Multiple "John Smith" require UUID lookup
- Mitigated: CLI shows all matches, prompts for selection

⚠️ **Storage location**: `~/.human-design/` might surprise users
- Mitigated: Document clearly, add `hd config` command

### Neutral

🔄 **New dependency**: None (uses stdlib `json`, `pathlib`)  
🔄 **Migration path**: Existing CLI commands unchanged  
🔄 **Learning curve**: Minimal (intuitive API)  

---

## Alternatives Considered

### Alternative 1: SQLite Database
**Pros**: Better query performance, concurrent access  
**Cons**: Overkill for use case, adds complexity, requires migration tools  
**Decision**: Start with JSON, migrate if needed (same API)

### Alternative 2: CLI-Only (No API Layer)
**Pros**: Simpler (fewer files)  
**Cons**: Not testable, not reusable, violates separation of concerns  
**Decision**: API layer is essential for testability

### Alternative 3: Object-Oriented (Chart Manager classes)
**Pros**: Familiar OOP pattern  
**Cons**: More boilerplate, harder to compose, less Pythonic  
**Decision**: Functions + repositories more Pydantic-aligned

### Alternative 4: Embed Storage in Models
```python
class RawBodyGraph(BaseModel):
    def save(self): ...  # NO!
```
**Pros**: Convenient  
**Cons**: Violates single responsibility, hard to test, tight coupling  
**Decision**: Separate storage concern into repository

---

## Implementation Plan

### Phase 1: Storage Foundation
1. ✅ Define `StoredPerson`, `StoredRelationship` models
2. ✅ Implement `PersonRepository` with JSON backend
3. ✅ Write tests for repository (add, get, find, search)

### Phase 2: API Layer
1. ✅ Implement `add_person()`, `get_interaction()`, `get_penta()`
2. ✅ Add `add_transit_to_person()`, `save_relationship()`
3. ✅ Write comprehensive unit tests (use mock repository)

### Phase 3: CLI Integration
1. ✅ Add `person add/list/show` commands
2. ✅ Add `interaction/penta/transit` commands
3. ✅ Write CLI integration tests (use temp storage)

### Phase 4: Documentation
1. ✅ Update README with new workflows
2. ✅ Add usage examples to docstrings
3. ✅ Create migration guide (if existing users)

---

## Open Questions

1. **Should we support relationship templates?**
   - e.g., "Sandy's family" as reusable group
   - **Decision**: Use tags first, add templates if needed

2. **How to handle chart caching?**
   - Recompute every time vs cache results
   - **Decision**: Always recompute (calculations are fast)

3. **Export formats?**
   - JSON, PDF, image?
   - **Decision**: JSON first, add formats later

---

## Success Metrics

📊 **API Adoption**: Web UI uses API layer by default  
📊 **CLI Simplicity**: All commands <10 lines  
📊 **Test Coverage**: >90% for API layer  
📊 **Type Safety**: 0 mypy errors  
📊 **User Satisfaction**: Rebecca can recall charts in <5 seconds  

---

## References

- [Pydantic Best Practices](https://docs.pydantic.dev/)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Typer CLI Best Practices](https://typer.tiangolo.com/)
- Existing models: `bodygraph.py`, `composite.py`, `transit.py`

---

**Review Status**: Awaiting stakeholder approval  
**Next Review**: After Phase 1 implementation  
**Last Updated**: 2024-01-XX
