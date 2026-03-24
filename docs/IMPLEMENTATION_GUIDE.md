# Implementation Guide: Human Design API Layer

This guide walks through implementing the new API layer architecture for Human Design chart operations.

## 📁 File Structure

```
src/human_design/
├── api/
│   ├── __init__.py          ✅ Created
│   └── operations.py        ✅ Created
├── storage/
│   ├── __init__.py          ✅ Created
│   ├── models.py            ✅ Created
│   └── repository.py        ✅ Created
├── cli.py                   🔄 To update
└── models/                  ✅ Existing (unchanged)
    ├── bodygraph.py
    ├── composite.py
    └── transit.py

tests/
├── test_storage_models.py   ✅ Created
├── test_repository.py       ✅ Created
└── test_api_operations.py   ✅ Created
```

## 🚀 Phase 1: Storage Foundation ✅

### Storage Models (`storage/models.py`)

**✅ Implemented**:
- `StoredPerson`: Person with birth info + tags + computed chart property
- `StoredRelationship`: Saved chart combinations (interaction/penta/multichart)
- Tag helper methods (`has_tag`, `add_tag`, `remove_tag`)
- Chart type classification (`interaction`, `penta`, `multichart`)

**Key Design Decisions**:
- **Computed `chart` property**: Always recalculate (fast enough, ensures consistency)
- **UUID primary keys**: Enable stable references independent of names
- **Flexible tagging**: No predefined schema, users define their own organization

### Repository Layer (`storage/repository.py`)

**✅ Implemented**:
- `PersonRepository`: CRUD operations for people
  - Add/get/update/delete
  - Search by name (exact and fuzzy)
  - Find by tag
  - List all with tag filtering
- `RelationshipRepository`: CRUD operations for relationships
  - Add/get/update/delete
  - Find by person, type, tag
- `StorageConfig`: Centralized configuration for file paths

**Key Design Decisions**:
- **JSON file storage**: Simple, human-readable, no database setup
- **Default location**: `~/.human-design/` (documented in config)
- **Case-insensitive search**: Matches user expectations
- **No concurrent access**: Single-user CLI tool (documented limitation)

**Storage Format**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Sandy Rodriguez",
    "tags": ["client", "family"],
    "birth_info": { "date": "1990-01-15", ... },
    "created_at": "2024-01-15T10:30:00"
  }
]
```

### Tests ✅

**Coverage**:
- `test_storage_models.py`: 15 tests (model validation, properties, helpers)
- `test_repository.py`: 20+ tests (CRUD, search, filtering)

**Run tests**:
```bash
pytest tests/test_storage_models.py -v
pytest tests/test_repository.py -v
```

---

## 🚀 Phase 2: API Layer ✅

### API Operations (`api/operations.py`)

**✅ Implemented Functions**:

1. **Person Management**:
   - `add_person()`: Add person with validation (duplicate name check)
   - `get_person()`: Retrieve by name (fuzzy) or UUID (exact)
   - `list_people()`: List all or filter by tag

2. **Chart Composition**:
   - `get_interaction()`: Two-person chart (uses `chart1 + chart2`)
   - `get_penta()`: 3-16 person chart (chained `+` operator)
   - `add_transit_to_person()`: Chart with transit overlay

3. **Relationship Storage**:
   - `save_relationship()`: Save named chart combination
   - `get_relationship()`: Retrieve and calculate saved relationship
   - `list_relationships()`: List all or filter by tag

**Key Design Decisions**:
- **`str | UUID` parameters**: Accept both names (user-friendly) and UUIDs (stable)
- **Helper `_resolve_person()`**: Centralized name→person logic with helpful errors
- **Optional `repo` parameter**: Defaults to standard location, injectable for testing
- **Preserves `__add__` pattern**: API wraps, doesn't replace existing operators

**Error Handling**:
```python
# Name not found
ValueError: No person found matching 'Nonexistent'

# Ambiguous name
ValueError: Multiple people match 'Sandy': ['Sandy Rodriguez', 'Sandy Smith']. Use full name or UUID.

# Person in relationship missing
ValueError: Person {uuid} in relationship not found in storage
```

### Tests ✅

**Coverage**:
- `test_api_operations.py`: 25+ tests covering all functions
  - Success paths
  - Error conditions (not found, ambiguous, validation)
  - Both name and UUID lookups

**Run tests**:
```bash
pytest tests/test_api_operations.py -v
```

---

## 🚀 Phase 3: CLI Integration 🔄

### CLI Commands (To Add to `cli.py`)

**Person Management**:
```python
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
    from .api import add_person
    from .models import BirthInfo, LocalTime
    from datetime import datetime
    
    # Parse birth info
    dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    birth_info = BirthInfo(
        date=date,
        localtime=LocalTime(dt),
        city=city,
        country=state
    )
    
    # Parse tags
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    
    # Add person
    person = add_person(name, birth_info, tag_list)
    typer.echo(f"✓ Added {person.name} (ID: {person.id})")


@app.command()
def person_list(tag: str = typer.Option(None, help="Filter by tag")) -> None:
    """List all people."""
    from .api import list_people
    
    people = list_people(tag=tag)
    
    if not people:
        typer.echo("No people found")
        return
    
    for p in people:
        tags_str = f"[{', '.join(p.tags)}]" if p.tags else ""
        typer.echo(f"{p.name} {tags_str}")
        typer.echo(f"  ID: {p.id}")
        typer.echo(f"  Type: {p.chart.type}, Authority: {p.chart.authority}")
        typer.echo()


@app.command()
def person_show(name: str) -> None:
    """Show person details."""
    from .api import get_person
    
    person = get_person(name)
    chart = person.chart
    
    typer.echo(f"Name: {person.name}")
    typer.echo(f"Tags: {', '.join(person.tags)}")
    typer.echo(f"Type: {chart.type}")
    typer.echo(f"Authority: {chart.authority}")
    typer.echo(f"Profile: {chart.profile}")
    typer.echo(f"\nDefined Centers: {', '.join(chart.defined_centers)}")
```

**Chart Operations**:
```python
@app.command()
def interaction(person1: str, person2: str) -> None:
    """Show interaction chart."""
    from .api import get_interaction
    
    chart = get_interaction(person1, person2)
    
    typer.echo(f"Interaction: {person1} + {person2}")
    typer.echo(f"Type: {chart.type}")
    typer.echo(f"Authority: {chart.authority}")
    typer.echo(f"Defined Centers: {', '.join(chart.defined_centers)}")
    
    emergent = chart.emergent_channels()
    if emergent:
        typer.echo(f"\n✨ Emergent Channels ({len(emergent)}):")
        for ch in emergent:
            typer.echo(f"  {ch.gate_a}-{ch.gate_b}: {ch.name}")


@app.command()
def penta(*people: str) -> None:
    """Show penta/multichart."""
    from .api import get_penta
    
    if len(people) < 3:
        typer.echo("❌ Penta requires at least 3 people", err=True)
        raise typer.Exit(1)
    
    chart = get_penta(list(people))
    
    typer.echo(f"Penta: {', '.join(people)}")
    typer.echo(f"Type: {chart.type}")
    typer.echo(f"Authority: {chart.authority}")
    typer.echo(f"Defined Centers: {', '.join(chart.defined_centers)}")


@app.command()
def transit(person: str) -> None:
    """Show person with current transit."""
    from .api import add_transit_to_person
    
    chart = add_transit_to_person(person)
    
    typer.echo(f"Transit: {person} + Now")
    typer.echo(f"Type: {chart.type}")
    typer.echo(f"Authority: {chart.authority}")
    typer.echo(f"Active Channels: {len(chart.active_channels)}")
```

**Relationship Management**:
```python
@app.command()
def save(
    name: str,
    people: str,
    tags: str = typer.Option("", help="Comma-separated tags")
) -> None:
    """Save relationship for later recall."""
    from .api import save_relationship
    
    # Parse people (comma-separated)
    person_list = [p.strip() for p in people.split(",")]
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    
    rel = save_relationship(name, person_list, tag_list)
    typer.echo(f"✓ Saved {rel.name} ({rel.chart_type})")


@app.command()
def recall(name: str) -> None:
    """Recall saved relationship."""
    from .api import get_relationship
    
    chart = get_relationship(name)
    
    typer.echo(f"Relationship: {name}")
    typer.echo(f"Type: {chart.type}")
    typer.echo(f"Authority: {chart.authority}")
```

### CLI Usage Examples

```bash
# Add people
hd person-add "Sandy Rodriguez" 1990-01-15 09:13 Albuquerque NM --tags "client,family"
hd person-add "Heath" 1985-06-20 14:30 Denver CO --tags "family"

# List people
hd person-list
hd person-list --tag family

# Show interaction
hd interaction "Sandy" "Heath"

# Show penta
hd penta "Sandy" "Heath" "daughter" "son"

# Add transit
hd transit "Sandy"

# Save relationship
hd save "Sandy + Heath" "Sandy,Heath" --tags "marriage,primary"

# Recall relationship
hd recall "Sandy + Heath"
```

**Line Count Check**: Each command ~8 lines ✅ (target: <10)

---

## 🚀 Phase 4: Documentation 📝

### 1. Update README.md

Add new section:

```markdown
## Chart Operations API

### Person Management

```python
from human_design.api import add_person, get_person, list_people
from human_design.models import BirthInfo, LocalTime
from datetime import datetime

# Add person
birth_info = BirthInfo(
    date="1990-01-15",
    localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
    city="Albuquerque",
    country="NM"
)
sandy = add_person("Sandy Rodriguez", birth_info, tags=["client", "family"])

# Retrieve by name or UUID
person = get_person("Sandy")
person = get_person(uuid_obj)

# List all or filter by tag
all_people = list_people()
clients = list_people(tag="client")
```

### Chart Composition

```python
from human_design.api import get_interaction, get_penta, add_transit_to_person

# Interaction chart (2 people)
interaction = get_interaction("Sandy", "Heath")
print(f"Type: {interaction.type}")
print(f"Emergent channels: {interaction.emergent_channels()}")

# Penta chart (3-5 people)
family = get_penta(["Sandy", "Heath", "daughter", "son"])

# Add transit
with_transit = add_transit_to_person("Sandy")
```

### Relationship Storage

```python
from human_design.api import save_relationship, get_relationship

# Save named relationship
rel = save_relationship(
    name="Sandy + Heath",
    people=["Sandy", "Heath"],
    tags=["marriage", "primary"]
)

# Recall later
chart = get_relationship("Sandy + Heath")
```

### CLI Commands

```bash
# Person management
hd person-add <name> <date> <time> <city> <state> [--tags]
hd person-list [--tag]
hd person-show <name>

# Chart operations
hd interaction <person1> <person2>
hd penta <person1> <person2> <person3> [...]
hd transit <person>

# Relationship storage
hd save <name> <people> [--tags]
hd recall <name>
```
```

### 2. Storage Location Documentation

Create `docs/STORAGE.md`:

```markdown
# Storage Configuration

## Default Location

Human Design data is stored in:
- **People**: `~/.human-design/people.json`
- **Relationships**: `~/.human-design/relationships.json`

## File Format

Storage uses JSON for simplicity and debuggability.

### People (`people.json`)
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Sandy Rodriguez",
    "tags": ["client", "family"],
    "birth_info": {
      "date": "1990-01-15",
      "localtime": "1990-01-15T09:13:00",
      "city": "Albuquerque",
      "country": "NM"
    },
    "created_at": "2024-01-15T10:30:00"
  }
]
```

### Relationships (`relationships.json`)
```json
[
  {
    "id": "650e8400-e29b-41d4-a716-446655440001",
    "name": "Sandy + Heath",
    "person_ids": [
      "550e8400-e29b-41d4-a716-446655440000",
      "550e8400-e29b-41d4-a716-446655440002"
    ],
    "tags": ["marriage"],
    "created_at": "2024-01-15T11:00:00"
  }
]
```

## Backup

To backup your data:
```bash
cp -r ~/.human-design ~/Dropbox/backups/human-design-$(date +%Y%m%d)
```

## Custom Location

Override storage location in code:
```python
from pathlib import Path
from human_design.storage import PersonRepository

repo = PersonRepository(storage_path=Path("/custom/path/people.json"))
```

## Limitations

- **No concurrent access**: Not thread-safe (single-user CLI tool)
- **Linear search**: O(n) lookup (acceptable for <1000 people)
- **No transactions**: File is rewritten on each change
- **No versioning**: No automatic migration for schema changes

## Migration to SQLite (Future)

If storage becomes a bottleneck, migrate to SQLite:
- Same API (repository pattern unchanged)
- Better query performance
- Concurrent access support
- Add `alembic` for migrations
```

### 3. API Reference Documentation

Create `docs/API_REFERENCE.md`:

```markdown
# API Reference

## Person Management

### `add_person()`
Add person to storage.

**Signature**:
```python
def add_person(
    name: str,
    birth_info: BirthInfo,
    tags: list[str] | None = None,
    repo: PersonRepository | None = None
) -> StoredPerson
```

**Parameters**:
- `name`: Full name (e.g., "Sandy Rodriguez")
- `birth_info`: Birth information for chart calculation
- `tags`: Optional tags for grouping
- `repo`: Repository (defaults to ~/.human-design/people.json)

**Returns**: `StoredPerson` with generated UUID

**Raises**: `ValueError` if person with this name already exists

**Example**:
```python
from human_design.api import add_person
from human_design.models import BirthInfo, LocalTime
from datetime import datetime

birth_info = BirthInfo(
    date="1990-01-15",
    localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
    city="Albuquerque",
    country="NM"
)

sandy = add_person("Sandy Rodriguez", birth_info, tags=["client"])
print(f"Added {sandy.name} with ID {sandy.id}")
```

[... document all other functions ...]
```

---

## ✅ Verification Checklist

### Storage Layer
- [ ] `StoredPerson` model validates correctly
- [ ] `StoredRelationship` model classifies chart types
- [ ] `PersonRepository` CRUD operations work
- [ ] `RelationshipRepository` CRUD operations work
- [ ] Tag-based filtering works (case-insensitive)
- [ ] JSON files created in correct location
- [ ] All tests pass (`pytest tests/test_storage_models.py tests/test_repository.py`)

### API Layer
- [ ] `add_person()` prevents duplicates
- [ ] `get_person()` handles ambiguous names
- [ ] `get_interaction()` uses `__add__` operator
- [ ] `get_penta()` chains `+` correctly
- [ ] `add_transit_to_person()` works with default `Transit.now()`
- [ ] `save_relationship()` stores all person UUIDs
- [ ] `get_relationship()` reconstructs charts correctly
- [ ] All tests pass (`pytest tests/test_api_operations.py`)

### CLI Integration
- [ ] All commands < 10 lines
- [ ] `person-add` command works
- [ ] `person-list` command works
- [ ] `interaction` command works
- [ ] `penta` command works
- [ ] `transit` command works
- [ ] `save` command works
- [ ] `recall` command works
- [ ] Error messages are helpful

### Documentation
- [ ] README updated with API examples
- [ ] `STORAGE.md` created
- [ ] `API_REFERENCE.md` created
- [ ] Docstrings complete for all public functions
- [ ] Migration guide (if needed)

### Type Safety
- [ ] All functions have type hints
- [ ] `mypy` passes with no errors
- [ ] IDE autocomplete works for all API functions

---

## 🐛 Known Issues & Future Work

### Current Limitations
1. **No concurrent access**: JSON file rewritten on each change (OK for single-user CLI)
2. **Linear search**: O(n) lookup (acceptable for <1000 people)
3. **No undo**: Deletes are permanent (add confirmation prompts)
4. **No schema versioning**: Manual migration if models change

### Future Enhancements
1. **SQLite migration**: If performance becomes issue
2. **Caching layer**: Cache chart calculations if needed
3. **Export formats**: PDF, image generation
4. **Relationship templates**: Reusable group definitions
5. **Web UI integration**: Use same API layer
6. **Import/export**: Bulk operations from CSV/JSON

---

## 📚 Related Documents
- [ADR-001: API Layer Architecture](ADR-001-api-layer-architecture.md)
- [Storage Documentation](STORAGE.md)
- [API Reference](API_REFERENCE.md)
