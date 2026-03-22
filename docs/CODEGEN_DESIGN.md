# CODEGEN_DESIGN: Deterministic YAML → JSON Ontology Transformation

**Problem**: Generate HD_ONTOLOGY_complete.json from YAML sources with ZERO interpretation errors  
**Solution**: Code-generated data eliminates human/LLM transcription errors  
**Principle**: YAML files are source of truth - ontology is a derived artifact

---

## Architecture Overview

### Core Principle: Deterministic Transformation

```
YAML Sources (100% correct, hand-audited)
    ↓
Python Script (mechanical transformation, zero interpretation)
    ↓
HD_ONTOLOGY_complete.json (reproducible, verifiable)
```

**NEVER override or 'correct' source data**. If YAML says gate 16 complement is 48, ontology MUST say 48.

---

## Data Flow Architecture

### 1. Input Sources (Source of Truth)

**YAML Files** (user-validated, treat as 100% correct):
- `src/human_design/bodygraph.yaml` - 64 gates with:
  - `number` (1-64)
  - `complement` (gate number or array of gate numbers)
  - `ra_description` (I Ching name)
  - `coordinate_range` (zodiac: sign, degree, minute, second)
- `src/human_design/channels.yaml` - 36 channels:
  - `name` (channel name)
  - `gates` (array of 2 gate numbers)
- `src/human_design/centers.yaml` - 9 centers:
  - `name` (center name)
  - `gates` (array of gate numbers)

**Existing Ontology** (contains HD system knowledge):
- `ontology/HD_ONTOLOGY_complete.json` - Current file with:
  - Types (Initiator/Builder/Specialist/Coordinator/Observer)
  - Authorities (Emotional/Sacral/Splenic/Ego/Self-Projected/Mental/Lunar)
  - Profiles (12 profiles: 1/3, 1/4, 2/4, etc.)
  - Circuit classifications
  - Quarter themes
  - Center descriptions (defined/undefined)

### 2. Transformation Logic

**Pydantic Models** (type-safe parsing):

```python
class GateYAML(BaseModel):
    number: int
    complement: int | list[int]
    ra_description: str
    coordinate_range: CoordinateRange

class ChannelYAML(BaseModel):
    name: str
    gates: list[int]  # Always length 2

class CenterYAML(BaseModel):
    name: str
    gates: list[int]
```

**Transformation Functions**:

```python
def parse_gates(bodygraph_yaml: Path) -> dict[int, GateYAML]:
    """Parse bodygraph.yaml → structured gate data"""
    # Returns: {gate_number: GateYAML}

def parse_channels(channels_yaml: Path) -> list[ChannelYAML]:
    """Parse channels.yaml → structured channel data"""

def parse_centers(centers_yaml: Path) -> dict[str, CenterYAML]:
    """Parse centers.yaml → structured center data"""

def merge_ontology(
    gates: dict[int, GateYAML],
    channels: list[ChannelYAML],
    centers: dict[str, CenterYAML],
    existing_ontology: dict
) -> dict:
    """Merge YAML data into ontology structure, preserving HD system knowledge"""
```

### 3. Output Structure

**HD_ONTOLOGY_complete.json**:

```json
{
  "schema_version": "1.0.0",
  "ontology_standard": "64keys",
  "generated_at": "ISO 8601 timestamp",
  "metadata": {
    "description": "...",
    "generated_by": "ontology/generate_ontology.py",
    "source_files": ["bodygraph.yaml", "channels.yaml", "centers.yaml"]
  },
  "gates": [
    {
      "number": 16,
      "i_ching_name": "Enthusiasm",  // FROM bodygraph.yaml ra_description
      "center": "EXPRESSION",         // FROM centers.yaml gate assignment
      "complement": 48,                // FROM bodygraph.yaml complement
      "coordinate_range": {...},       // FROM bodygraph.yaml coordinate_range
      "description": "...",            // FROM existing ontology (HD knowledge)
      "keywords": [...]                // FROM existing ontology (HD knowledge)
    }
  ],
  "channels": [
    {
      "id": "16-48",
      "name": "The Wave Length",       // FROM channels.yaml
      "gate1": 16,
      "gate2": 48,                      // FROM channels.yaml gates array
      "centers": ["EXPRESSION", "INTUITION"],  // DERIVED from gate-to-center lookup
      "circuit": "Individual",          // FROM existing ontology (HD knowledge)
      "description": "..."              // FROM existing ontology (HD knowledge)
    }
  ],
  "centers": [
    {
      "id": "EXPRESSION",
      "gates": [62, 23, 56, ...],      // FROM centers.yaml
      "traditional_name": "Throat",    // FROM existing ontology (HD knowledge)
      "defined_description": "...",    // FROM existing ontology (HD knowledge)
      "undefined_description": "..."   // FROM existing ontology (HD knowledge)
    }
  ],
  "types": [...],        // PRESERVED from existing ontology
  "authorities": [...],  // PRESERVED from existing ontology
  "profiles": [...],     // PRESERVED from existing ontology
  "quarters": [...]      // PRESERVED from existing ontology (or derived from coordinates)
}
```

---

## Data Merging Strategy

### What Gets Overwritten (YAML is Source of Truth)

**Gates Section**:
- `number` - YAML
- `i_ching_name` - YAML (`ra_description`)
- `complement` - YAML (CRITICAL: this fixes transcription errors)
- `center` - DERIVED from centers.yaml lookup
- `coordinate_range` - YAML

**Channels Section**:
- `id` - GENERATED from YAML gates array (`{gate1}-{gate2}`)
- `name` - YAML
- `gate1`, `gate2` - YAML
- `centers` - DERIVED from gate-to-center lookup

**Centers Section**:
- `id` - YAML (center name)
- `gates` - YAML (gate assignments)

### What Gets Preserved (HD System Knowledge)

**Gates Section**:
- `description` - Keep from existing ontology
- `keywords` - Keep from existing ontology
- `quarter` - Keep from existing ontology (or derive from coordinates)

**Channels Section**:
- `circuit` - Keep from existing ontology
- `sub_circuit` - Keep from existing ontology
- `description` - Keep from existing ontology
- `theme` - Keep from existing ontology

**Centers Section**:
- `traditional_name` - Keep from existing ontology
- `type` - Keep from existing ontology
- `defined_description` - Keep from existing ontology
- `undefined_description` - Keep from existing ontology
- `function` - Keep from existing ontology

**Top-Level Sections** (NO YAML source):
- `types` - PRESERVE entirely
- `authorities` - PRESERVE entirely
- `profiles` - PRESERVE entirely
- `definitions` - PRESERVE entirely
- `quarters` - PRESERVE (or enhance with coordinate-based gate ranges)

---

## Validation Strategy

### Assertions (Fail Fast)

```python
def validate_output(ontology: dict) -> None:
    """Validate generated ontology matches expected data integrity"""
    
    # Count validations
    assert len(ontology["gates"]) == 64, "Must have 64 gates"
    assert len(ontology["channels"]) == 36, "Must have 36 channels"
    assert len(ontology["centers"]) == 9, "Must have 9 centers"
    
    # Gate number continuity
    gate_numbers = {g["number"] for g in ontology["gates"]}
    assert gate_numbers == set(range(1, 65)), "Gates must be 1-64"
    
    # Channel gate pairs match YAML
    for channel in ontology["channels"]:
        assert channel["gate1"] in gate_numbers
        assert channel["gate2"] in gate_numbers
        assert f"{channel['gate1']}-{channel['gate2']}" == channel["id"]
    
    # Center gate assignments match YAML
    all_center_gates = set()
    for center in ontology["centers"]:
        all_center_gates.update(center["gates"])
    assert all_center_gates == gate_numbers, "All gates must be assigned to centers"
    
    # Gate complements match bodygraph.yaml EXACTLY
    # (This is the CRITICAL validation that fixes transcription errors)
    for gate in ontology["gates"]:
        # Validate complement exists and is correct type
        assert "complement" in gate
        assert isinstance(gate["complement"], (int, list))
```

### Cross-Reference Checks

```python
def cross_validate(
    ontology: dict,
    gates_yaml: dict[int, GateYAML],
    channels_yaml: list[ChannelYAML],
    centers_yaml: dict[str, CenterYAML]
) -> list[str]:
    """Return list of discrepancies (should be empty)"""
    
    discrepancies = []
    
    # Validate gate complements
    for gate in ontology["gates"]:
        yaml_gate = gates_yaml[gate["number"]]
        if gate["complement"] != yaml_gate.complement:
            discrepancies.append(
                f"Gate {gate['number']} complement mismatch: "
                f"JSON={gate['complement']}, YAML={yaml_gate.complement}"
            )
    
    # Validate channel gate pairs
    for channel in ontology["channels"]:
        yaml_channel = next(
            (c for c in channels_yaml if c.name == channel["name"]),
            None
        )
        if yaml_channel:
            if sorted([channel["gate1"], channel["gate2"]]) != sorted(yaml_channel.gates):
                discrepancies.append(
                    f"Channel {channel['name']} gate mismatch"
                )
    
    # Validate center gate assignments
    for center in ontology["centers"]:
        yaml_center = centers_yaml.get(center["id"])
        if yaml_center:
            if set(center["gates"]) != set(yaml_center.gates):
                discrepancies.append(
                    f"Center {center['id']} gate assignment mismatch"
                )
    
    return discrepancies
```

---

## Implementation Pattern: Merge, Don't Replace

### Gate Merging Example

```python
def merge_gate(
    yaml_gate: GateYAML,
    center_name: str,
    existing_gate: dict | None
) -> dict:
    """Merge YAML data with existing ontology gate data"""
    
    # Start with YAML data (source of truth)
    merged = {
        "number": yaml_gate.number,
        "i_ching_name": yaml_gate.ra_description,
        "complement": yaml_gate.complement,
        "center": center_name,
        "coordinate_range": yaml_gate.coordinate_range.dict()
    }
    
    # Preserve HD system knowledge from existing ontology
    if existing_gate:
        merged["description"] = existing_gate.get("description", "")
        merged["keywords"] = existing_gate.get("keywords", [])
        merged["quarter"] = existing_gate.get("quarter", derive_quarter_from_coordinates(yaml_gate))
    
    return merged
```

### Channel Merging Example

```python
def merge_channel(
    yaml_channel: ChannelYAML,
    gate_to_center: dict[int, str],
    existing_channel: dict | None
) -> dict:
    """Merge YAML channel with existing ontology channel data"""
    
    gate1, gate2 = yaml_channel.gates
    
    merged = {
        "id": f"{gate1}-{gate2}",
        "name": yaml_channel.name,
        "gate1": gate1,
        "gate2": gate2,
        "centers": [gate_to_center[gate1], gate_to_center[gate2]]
    }
    
    # Preserve circuit and semantic content
    if existing_channel:
        merged["circuit"] = existing_channel.get("circuit", "")
        merged["sub_circuit"] = existing_channel.get("sub_circuit", "")
        merged["description"] = existing_channel.get("description", "")
        merged["theme"] = existing_channel.get("theme", "")
    
    return merged
```

---

## Error Handling Philosophy

### Fail Fast on YAML Parsing Errors

```python
try:
    gates = parse_gates(bodygraph_yaml_path)
except Exception as e:
    print(f"FATAL: Cannot parse bodygraph.yaml - {e}")
    sys.exit(1)
```

**Rationale**: If YAML is malformed, DO NOT proceed. YAML is the source of truth.

### Warn on Missing HD Knowledge

```python
if not existing_gate.get("description"):
    warnings.warn(f"Gate {gate_num} missing description in existing ontology")
```

**Rationale**: Missing HD knowledge is non-fatal. Can be added later.

### Assert on Data Integrity

```python
assert len(ontology["gates"]) == 64, "Critical: Gate count must be 64"
```

**Rationale**: Structural integrity violations = programming error. Fail immediately.

---

## Idempotency Guarantee

### Same Input → Same Output

```python
# Running twice produces byte-identical JSON
$ python ontology/generate_ontology.py
$ sha256sum ontology/HD_ONTOLOGY_complete.json
abc123...

$ python ontology/generate_ontology.py
$ sha256sum ontology/HD_ONTOLOGY_complete.json
abc123...  # Identical hash
```

**Implementation**:
- Sort all arrays by ID/number before output
- Use deterministic JSON formatting (2-space indent, sorted keys)
- No timestamps in data (only in metadata)
- No randomness, no LLM calls, no interpretation

---

## Script Structure

```
ontology/generate_ontology.py
├── Imports (yaml, json, pydantic, pathlib)
├── Data Models
│   ├── GateYAML(BaseModel)
│   ├── ChannelYAML(BaseModel)
│   ├── CenterYAML(BaseModel)
│   └── CoordinateRange(BaseModel)
├── Parsing Functions
│   ├── parse_gates(path) -> dict[int, GateYAML]
│   ├── parse_channels(path) -> list[ChannelYAML]
│   └── parse_centers(path) -> dict[str, CenterYAML]
├── Transformation Functions
│   ├── build_gate_to_center_map(centers) -> dict[int, str]
│   ├── merge_gate(yaml_gate, center, existing) -> dict
│   ├── merge_channel(yaml_channel, gate_to_center, existing) -> dict
│   └── merge_center(yaml_center, existing) -> dict
├── Validation Functions
│   ├── validate_output(ontology) -> None
│   └── cross_validate(ontology, yaml_data) -> list[str]
├── Main Function
│   ├── Load YAML sources
│   ├── Load existing ontology
│   ├── Build gate-to-center map
│   ├── Merge gates section
│   ├── Merge channels section
│   ├── Merge centers section
│   ├── Preserve types/authorities/profiles/quarters
│   ├── Validate output
│   ├── Cross-validate against YAML
│   └── Write HD_ONTOLOGY_complete.json
└── CLI Entry Point
```

---

## Success Criteria

✅ **Determinism**: Running twice produces identical output  
✅ **Accuracy**: All gate complements match bodygraph.yaml EXACTLY  
✅ **Completeness**: 64 gates, 36 channels, 9 centers, all present  
✅ **Idempotency**: Byte-identical output on repeated runs  
✅ **Validation**: All assertions pass, zero discrepancies  
✅ **Runnable**: `python ontology/generate_ontology.py` works  
✅ **Documentation**: Docstring explains usage and regeneration process

---

## Usage Instructions

```bash
# Generate ontology from YAML sources
python ontology/generate_ontology.py

# Validates:
# - 64 gates with correct complements
# - 36 channels with correct gate pairs
# - 9 centers with correct gate assignments
# - Cross-references against YAML sources

# Output:
# - ontology/HD_ONTOLOGY_complete.json (production file)
# - Validation report (printed to stdout)
```

**When to regenerate**:
- After hand-editing bodygraph.yaml, channels.yaml, or centers.yaml
- After discovering transcription errors in existing ontology
- To verify ontology matches YAML sources (validation mode)

**What gets preserved**:
- Types, Authorities, Profiles, Definitions, Quarters (HD system knowledge)
- Gate descriptions, keywords (semantic content)
- Channel circuits, themes, descriptions (semantic content)
- Center descriptions, functions (semantic content)

**What gets overwritten**:
- Gate numbers, I Ching names, complements, coordinates (from YAML)
- Channel names, gate pairs (from YAML)
- Center names, gate assignments (from YAML)

---

## Architectural Benefits

1. **Zero Transcription Errors**: Code reads YAML directly, no human/LLM interpretation
2. **Reproducible**: Same YAML always produces same JSON
3. **Verifiable**: Cross-validation proves ontology matches sources
4. **Maintainable**: YAML files are clean, readable, version-controlled
5. **Auditable**: Git diff shows exactly what changed in sources
6. **Extensible**: Add new YAML files → update script → regenerate

This follows the pattern: **Code-generated data > Hand-written data > LLM-interpreted data**
