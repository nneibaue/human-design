# Coordinator Synthesis: Deterministic Ontology Code Generation

**Date**: 2024-01-15  
**Task**: Generate deterministic Python code to transform YAML sources into HD_ONTOLOGY_complete.json  
**Status**: SYNTHESIS COMPLETE ✅ (Implementation phase blocked by missing agent archetype)

---

## Executive Summary

### Problem Solved
The current HD_ONTOLOGY_complete.json contains **11+ transcription errors** (incorrect gate complements, data inaccuracies) introduced by LLM interpretation when copying data from YAML files. This violates the integrity of Human Design system data.

### Solution Designed
**Architect agent** produced a comprehensive design for deterministic code generation:
- **Architecture**: YAML sources (source of truth) → Python script (mechanical transformation) → JSON ontology (derived artifact)
- **Core Principle**: ZERO interpretation - code mechanically copies YAML data without "correcting" or interpreting
- **Deliverable**: `ontology/generate_ontology.py` script that produces byte-identical, reproducible output

### Current Status
- ✅ **Architecture Complete**: 15KB design document (`docs/CODEGEN_DESIGN.md`) with full specification
- ❌ **Implementation Blocked**: Implementer agent not found in ontology (agent archetype missing)
- ⏸️ **Validation Pending**: Awaits implementation completion

---

## Convergence Analysis: What We Know Works

### 1. Architectural Pattern (HIGH CONFIDENCE)

**Universal Agreement**:
```
YAML Sources (hand-audited) 
    ↓
Python Script (deterministic transformation)
    ↓
JSON Ontology (reproducible output)
```

**Why This Works**:
- **Precedent**: Similar to RawBodyGraph calculation from Swiss Ephemeris (already proven in codebase)
- **Verifiable**: Git diffs show exactly what changed in YAML sources
- **Reproducible**: Same input → same output (idempotency guarantee)
- **Zero Errors**: Code reads directly from YAML, no human/LLM interpretation layer

### 2. Data Flow Design (HIGH CONFIDENCE)

**Source Files** (user-validated as 100% correct):
- `src/human_design/bodygraph.yaml` - 64 gates with complements, I Ching names, zodiac coordinates
- `src/human_design/channels.yaml` - 36 channels as gate pairs
- `src/human_design/centers.yaml` - 9 centers with gate assignments

**Transformation Strategy**:
- **Overwrite from YAML**: Gate complements, I Ching names, channel gate pairs, center gate lists
- **Preserve from Existing Ontology**: Types, Authorities, Profiles, gate descriptions, channel circuits
- **Derive Programmatically**: Channel centers (from gate-to-center lookup)

**Validation Strategy**:
```python
assert len(gates) == 64
assert len(channels) == 36
assert len(centers) == 9
cross_validate(ontology, yaml_sources)  # Returns empty list if perfect match
```

### 3. Implementation Structure (HIGH CONFIDENCE)

**Pydantic Models** (type-safe YAML parsing):
```python
class GateYAML(BaseModel):
    number: int
    complement: int | list[int]  # Some gates have multiple complements
    ra_description: str
    coordinate_range: CoordinateRange

class ChannelYAML(BaseModel):
    name: str
    gates: list[int]  # Always length 2

class CenterYAML(BaseModel):
    name: str
    gates: list[int]
```

**Key Functions**:
- `parse_gates()` / `parse_channels()` / `parse_centers()` - Read YAML with fail-fast error handling
- `merge_gate()` / `merge_channel()` / `merge_center()` - Combine YAML + existing ontology data
- `validate_output()` - Assert structural integrity (counts, gate numbers)
- `cross_validate()` - Prove ontology matches YAML sources exactly

**Error Handling Philosophy**:
- **YAML parsing errors**: FAIL FAST (YAML is source of truth)
- **Missing HD knowledge**: WARN (non-fatal, can be added later)
- **Data integrity violations**: ASSERT (programming error, fail immediately)

---

## Shear Analysis: What Needs Resolution

### 1. Implementation Gap: Missing Agent Archetype

**Issue**: Implementer agent failed with error:
```
Agent archetype 'implementer' not found in ontology
```

**Impact**: 
- Architecture design complete but code not written
- Cannot validate approach until script exists
- Blocks delivery of working `ontology/generate_ontology.py`

**Resolution Path**:
1. **Option A**: Manually implement script following design specification
2. **Option B**: Fix agent ontology to support implementer archetype
3. **Option C**: Re-run with available agent (e.g., "developer", "coder")

**Recommendation**: **Option A** - Manual implementation following CODEGEN_DESIGN.md specification ensures:
- Zero dependency on agent system working correctly
- Direct control over deterministic code quality
- Immediate unblocking of validation phase

### 2. YAML Data Structure Complexity

**Observation**: Some gates have multiple complements (arrays vs single integers):
```yaml
# Single complement (most gates)
- number: 16
  complement: 48

# Multiple complements (gates 10, 20, 34, 57)
- number: 20
  complement: [57, 10, 34]
```

**Design Handles This**:
```python
complement: int | list[int]  # Pydantic model supports both
```

**Validation Requirement**:
- Assert complement data matches YAML type exactly (no normalization)
- Preserve array vs integer distinction in output JSON

### 3. Missing `ra_description` in Gate 36

**Observation**: bodygraph.yaml line 501-513 shows gate 36 missing `ra_description` field

**Design Handles This**:
- `ra_description` field should be optional in Pydantic model
- If missing, fall back to existing ontology I Ching name
- Cross-validation should WARN (not fail) on missing fields

**Action Required**:
- Add `ra_description: Optional[str]` to GateYAML model
- Update merge logic to handle missing field gracefully

---

## Critical Insights: What Makes This Work

### 1. Source of Truth Principle

**Key Decision**: YAML files are **never overridden or "corrected"** by code
- If YAML says gate 16 complement is 48 → ontology MUST say 48
- If YAML is wrong, fix YAML then regenerate
- Code is a **mechanical transformer**, not an interpreter

**Why This Matters**:
- User hand-audited YAML files → trusting source data is correct
- Past errors came from LLM "improving" data during transcription
- Deterministic transformation eliminates interpretation layer

### 2. Idempotency as Validation

**Guarantee**: Running script twice produces **byte-identical** output
```bash
$ python ontology/generate_ontology.py
$ sha256sum ontology/HD_ONTOLOGY_complete.json
abc123...

$ python ontology/generate_ontology.py  # Run again
$ sha256sum ontology/HD_ONTOLOGY_complete.json
abc123...  # Identical hash
```

**Implementation Requirements**:
- Sort all arrays by ID/number before output
- Use deterministic JSON formatting (2-space indent, sorted keys)
- No timestamps in data (only in metadata section)
- No randomness, no LLM calls, no interpretation

### 3. Cross-Validation as Proof of Correctness

**Beyond Assertions**: Cross-validation proves ontology matches YAML sources exactly
```python
discrepancies = cross_validate(ontology, gates_yaml, channels_yaml, centers_yaml)
assert len(discrepancies) == 0, f"Mismatches found: {discrepancies}"
```

**What Gets Validated**:
- All 64 gate complements match bodygraph.yaml EXACTLY (fixes transcription errors)
- All 36 channel gate pairs match channels.yaml EXACTLY
- All 9 center gate lists match centers.yaml EXACTLY
- I Ching names copied exactly from bodygraph.yaml ra_description

---

## Recommendations

### Immediate Actions (Priority Order)

1. **[CRITICAL] Implement `ontology/generate_ontology.py`** following CODEGEN_DESIGN.md specification
   - Use Pydantic v2 for type-safe YAML parsing
   - Implement fail-fast error handling for YAML parsing
   - Add idempotency guarantee (sorted output, deterministic JSON)
   - Include comprehensive docstring explaining usage

2. **[CRITICAL] Handle Missing Data Edge Cases**
   - Make `ra_description` optional in GateYAML model (gate 36 missing)
   - Add fallback logic for missing I Ching names (use existing ontology)
   - Update validation to WARN (not fail) on missing optional fields

3. **[HIGH] Add Cross-Validation Tests**
   - Implement `cross_validate()` function as specified in design
   - Assert zero discrepancies after generation
   - Print validation report showing what was overwritten vs preserved

4. **[MEDIUM] Document Regeneration Workflow**
   - Add README.md section: "When to regenerate ontology"
   - List what gets overwritten vs what gets preserved
   - Provide example commands and expected output

### Validation Criteria (Pre-Delivery Checklist)

Before marking this task complete, verify:

- [ ] `ontology/generate_ontology.py` script exists and runs successfully
- [ ] `python ontology/generate_ontology.py` produces `ontology/HD_ONTOLOGY_complete.json`
- [ ] Running script twice produces byte-identical output (idempotency)
- [ ] All 64 gate complements match bodygraph.yaml EXACTLY
- [ ] All 36 channel gate pairs match channels.yaml EXACTLY
- [ ] All 9 center gate lists match centers.yaml EXACTLY
- [ ] Cross-validation reports zero discrepancies
- [ ] Docstring explains usage, regeneration process, preservation strategy
- [ ] CODEGEN_VALIDATION.md documents validation results

---

## Architectural Benefits: Why This Approach Wins

### 1. Zero Transcription Errors
- Code reads YAML directly → no human/LLM interpretation layer
- Past errors: 11+ gate complements wrong due to manual copying
- Future-proof: Any YAML changes automatically reflected in ontology

### 2. Reproducible & Verifiable
- Same YAML input → same JSON output (always)
- Git diff shows exactly what changed in sources
- Cross-validation proves correctness mathematically

### 3. Maintainable & Auditable
- YAML files are clean, human-readable, version-controlled
- Changes tracked in git history
- Regeneration takes seconds, not hours

### 4. Extensible
- Add new YAML files (e.g., `profiles.yaml`) → update script → regenerate
- Enhance HD knowledge in existing ontology → script preserves on next run
- No manual data entry or LLM interpretation required

### 5. Follows Proven Pattern
- Similar to RawBodyGraph calculation (deterministic, verifiable)
- Code-generated data > Hand-written data > LLM-interpreted data
- Matches software engineering best practices (DRY principle, single source of truth)

---

## Next Phase: Implementation

**Blocked**: Implementer agent not found in ontology

**Unblocking Options**:
1. **Manual Implementation**: Write script following CODEGEN_DESIGN.md (fastest path)
2. **Agent System Fix**: Add implementer archetype to agent ontology (systemic fix)
3. **Alternative Agent**: Re-run phase 2 with "developer" or "coder" agent (workaround)

**Recommended Path**: Manual implementation ensures:
- Control over code quality and determinism
- No dependency on agent system configuration
- Immediate delivery of working solution

**Estimated Effort**: 2-4 hours to implement + 1 hour validation
**Deliverables**: 
- `ontology/generate_ontology.py` (runnable script)
- `ontology/HD_ONTOLOGY_complete.json` (regenerated ontology)
- `docs/CODEGEN_VALIDATION.md` (proof of correctness)

---

## Conclusion: Architecture Proven, Implementation Blocked

### What We Accomplished
✅ **Complete architectural design** for deterministic ontology generation  
✅ **Validated approach** against existing codebase patterns (Swiss Ephemeris precedent)  
✅ **Specified all edge cases** (multiple complements, missing fields, merge strategy)  
✅ **Defined validation criteria** (assertions, cross-validation, idempotency)

### What's Blocking Progress
❌ **Implementer agent missing** from agent ontology  
❌ **No working code** to validate design against actual YAML files  
❌ **Cannot prove correctness** until script runs and cross-validates

### Clear Path Forward
**Option 1 (Recommended)**: Manually implement following CODEGEN_DESIGN.md specification  
**Option 2**: Fix agent system to support implementer archetype  
**Option 3**: Re-run with alternative agent ("developer", "coder")  

**Risk Assessment**: Low - architecture is complete and follows proven patterns. Implementation is mechanical translation of design specification to Python code.

---

**Coordinator Signature**: Analysis complete. Architecture validated. Implementation phase requires manual intervention or agent system fix.
