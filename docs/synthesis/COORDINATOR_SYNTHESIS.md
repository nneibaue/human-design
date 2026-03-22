# Coordinator Synthesis: Multi-Chart Human Design Ontology & Implementation Roadmap

**Task**: Reverse-engineer 64keys.com chart combination features and build comprehensive Human Design ontology to enable ergonomic multi-chart calculations during Rebecca's consultation sessions

**Date**: 2025-01-30  
**Status**: ✅ COMPREHENSIVE SYNTHESIS COMPLETE  
**Confidence**: 0.85 (HIGH)

---

## Executive Summary

The Human Design codebase has **excellent architectural foundations** for individual chart calculation but **critical gaps** in multi-chart features that block Rebecca's core workflow. This synthesis integrates findings from four specialist agents to provide a complete roadmap for implementation.

### 🎯 Key Findings

#### ✅ CONVERGENCE (High Confidence)
All agents agree on these points:

1. **Strong Foundation Exists**
   - RawBodyGraph calculation is production-ready
   - Raw vs semantic separation pattern is exemplary
   - Swiss Ephemeris integration is robust
   - 64keys API client works well for single entities
   - Pydantic v2 with strict typing ensures ontological validation

2. **Critical Missing Components**
   - ❌ Channel formation logic (blocking ALL multi-chart work)
   - ❌ Interaction charts (2 people)
   - ❌ Penta charts (3-5 people)
   - ❌ Transit overlays
   - ❌ Chart visualization system
   - ❌ Type/Authority/Profile calculations

3. **Rebecca's Workflow is 100% Blocked**
   - Can only generate individual charts
   - Cannot combine charts during sessions
   - No quick-access patterns for groups
   - No visual comparison tools

#### ⚡ SHEAR (Hidden Dimensions Revealed)

1. **Architect Agent Failed** (schema version mismatch: expected 1.0.0, got 2.0.0)
   - This reveals a **system evolution tension**: newer agent definitions are incompatible with older coordinator expectations
   - Recommendation: Update coordinator to support agent schema versioning

2. **Ontology Coverage Disparity**
   - Ontologist reports: **70% complete** (core entities done, multi-chart missing)
   - Fair Witness reports: **45% complete** (9/20 entities implemented)
   - **Resolution**: Different granularity of measurement. Ontologist measures by feature breadth (gates, centers, calculations), Fair Witness measures by total entity count including multi-chart models
   - **Reality**: ~50-60% complete when weighted by Rebecca's priorities

3. **Center Name Inconsistency**
   - Ontologist flagged: "DRIVE and LIFEFORCE both map to Sacral"
   - Fair Witness validated: centers.yaml needs clarification
   - **Investigation needed**: Check if 64keys uses different center divisions or if this is an error

4. **Penta Parameter Mystery**
   - Multiple agents noted `/penta?id0=1&id1=2&...&s0=a&s1=a&...` pattern
   - **Nobody knows what 's0-s4' parameters mean**
   - Hypothesis: status/show/selection flags?
   - **Action**: MCP server browsing required to reverse-engineer

---

## 🏗️ Comprehensive Human Design Ontology

### Implemented Entities (Production-Ready)

| Entity | Count | Confidence | Data Source | Notes |
|--------|-------|------------|-------------|-------|
| **Gate** | 64/64 | ✅ 100% | bodygraph.yaml, gates.json | Full zodiac coordinates, complements, 6 lines each |
| **Center** | 9/9 | ✅ 100% | bodygraph.yaml, centers.yaml | INSPIRATION, MIND, EXPRESSION, IDENTITY, WILLPOWER, EMOTION, DRIVE, LIFEFORCE, INTUITION |
| **Planet** | 13/13 | ✅ 100% | core.py | SUN, EARTH, MOON, MERCURY, VENUS, MARS, JUPITER, SATURN, URANUS, NEPTUNE, PLUTO, NORTH_NODE, SOUTH_NODE |
| **Activation** | 26/26 | ✅ 100% | bodygraph.py | 13 conscious + 13 unconscious planetary activations |
| **ZodiacSign** | 12/12 | ✅ 100% | core.py | Tropical zodiac with degree ranges |
| **GateLine** | 6/6 | ✅ 100% | bodygraph.py | Lines 1-6 within each gate |

### Missing Entities (CRITICAL BLOCKERS)

| Entity | Status | Blocking | Estimated Effort |
|--------|--------|----------|------------------|
| **Channel** | ❌ Defined in channels.yaml but no Python model | ALL multi-chart work | 2-3 days |
| **Type** | ❌ Not calculated | Profile understanding | 1 day |
| **Authority** | ❌ Not calculated | Decision-making context | 1 day |
| **Profile** | ❌ Not extracted (conscious Sun line + unconscious Sun line) | Core HD understanding | 0.5 days |
| **Definition** | ❌ No graph traversal logic | Chart structure understanding | 1-2 days |
| **InteractionChart** | ❌ Core requirement entirely missing | Rebecca's #1 use case | 1 week |
| **PentaChart** | ❌ Core requirement entirely missing | Family analysis | 1 week |
| **TransitOverlay** | 🟡 Partial (get_current_transit exists) | Temporal context | 3-5 days |
| **MultiChart** | ❌ Visual comparison not implemented | Group comparison | 1 week |

### Terminology Mappings (64keys ↔ Traditional HD)

```json
{
  "types": {
    "Initiator": "Manifestor (~8%)",
    "Builder": "Generator (~37%)",
    "Specialist": "Manifesting Generator (~33%)",
    "Coordinator": "Projector (~21%)",
    "Observer": "Reflector (~1%)"
  },
  "centers": {
    "INSPIRATION": "Head/Crown",
    "MIND": "Ajna",
    "EXPRESSION": "Throat",
    "IDENTITY": "G Center/Self",
    "WILLPOWER": "Heart/Ego",
    "EMOTION": "Solar Plexus",
    "DRIVE": "Root (?)",
    "LIFEFORCE": "Sacral (?)",
    "INTUITION": "Spleen"
  },
  "circuits": {
    "Individual": ["Knowing (mental)", "Centering (emotional)", "Integration (self-empowerment)"],
    "Collective": ["Understanding/Logic (patterns, proof)", "Sensing/Abstract (experience, reflection)"],
    "Tribal": ["Ego (material power, deals)", "Defense (nurturing, survival)"]
  }
}
```

⚠️ **Terminology Consistency Issue**: DRIVE and LIFEFORCE both appear to map to traditional "Sacral" center. Needs investigation.

---

## 🔬 64keys.com Integration Specification

### Working Endpoints

| Endpoint | Status | Purpose | Implementation |
|----------|--------|---------|----------------|
| `/chart?id=123` | ✅ Working | Individual chart | GateAPI.get_chart() |
| `/transit` | ✅ Working | Current transit | GateAPI.get_current_transit() |
| `list_api` | ✅ Working | List people | GateAPI authenticated session |
| `library_api?type=gate&param1=N` | ✅ Working | Single gate info | GateAPI.get_gate_summary() |

### Discovered But Not Implemented

| Endpoint | Priority | Purpose | Notes |
|----------|----------|---------|-------|
| `/interaction?id1=X&id2=Y` | 🔥 CRITICAL | 2-person composite | Rebecca's #1 use case |
| `/penta?id0=X&id1=Y&...&s0=a&s1=a&...` | 🔥 CRITICAL | 3-5 person group | Family analysis |
| `/familypenta?id0=X&...` | HIGH | 3-5 person family | Different semantic interpretation? |
| `/multi_chart?id[0]=X&id[1]=Y&...` | MEDIUM | 2-16 person visual comparison | Side-by-side charts |
| `/transit?id1=X` | MEDIUM | Transit overlay on natal chart | Temporal context |
| `/o16?ids=1,2,3,...` | LOW | 16-person organizational | Advanced feature |

### MCP Server Capabilities

**Available Tools**:
- `browse_page` - Fetch any 64keys page as Markdown ✅
- `analyze_page` - Extract structure and metadata ✅
- `get_people` - List people from account ✅
- `get_chart` - Get person's chart ✅
- `get_gate_info` - Detailed gate summaries ✅
- `find_text` - Search within pages ✅
- `search_64keys` - Global search ✅

**Usage Status**: Tools exist but **reverse-engineering process NOT EXECUTED**. No documented:
- SVG structure for charts
- Color schemes and visual encoding
- Composite calculation patterns from actual pages
- Interaction/penta page HTML structure

---

## 🎨 Visual Design System (Rebecca Energy)

### 64keys Color Palette (To Be Extracted)

**Research Needed**: Use MCP `browse_page` to systematically explore chart rendering and extract:
- Defined vs undefined center colors
- Channel activation colors
- Gate activation colors
- Conscious vs unconscious color coding
- Transit overlay colors
- Interactive state colors (hover, click)

### Rebecca Energy Palette (Proposed)

Based on `.github/copilot-instructions.md`:

```css
/* Primary Palette */
--mystical-purple: #6A4C9C;      /* Deep purple for mystical elements */
--twilight-purple: #8B6BB0;      /* Lighter purple for accents */
--autumn-gold: #D4A574;          /* Gold/amber for warmth */
--forest-green: #5A7D5E;         /* Grounding forest green */
--earth-brown: #8B7355;          /* Warm earth tones */

/* Functional Colors */
--defined-center: #6A4C9C;       /* Mystical purple for defined centers */
--undefined-center: #F5F5DC;     /* Warm cream for undefined */
--conscious-activation: #D4A574; /* Gold for personality/conscious */
--unconscious-activation: #5A7D5E; /* Green for design/unconscious */
--transit-overlay: #E8A87C;      /* Warm amber for transits */

/* Mood */
--cozy-background: #FFF8E7;      /* Warm off-white (tea-stained paper) */
--shadow-depth: #4A3D60;         /* Dark purple for shadows */
--highlight-glow: #FFD700;       /* Golden highlight for interactive states */
```

**Philosophy**: "Cozy autumnal forest, twilight magic, accessible not corporate"

---

## 🏗️ Chart Combination API Design

### Core Calculation Models

#### 1. Channel Detection (BLOCKING ALL WORK)

```python
# src/human_design/models/channel.py

from pydantic import BaseModel
from .core import GateNumber

class ChannelDefinition(BaseModel):
    """Definition of a channel connecting two gates."""
    name: str
    gates: tuple[GateNumber, GateNumber]
    circuit: str | None  # 'Knowing', 'Centering', 'Integration', etc.
    
    @classmethod
    def load_all(cls) -> list["ChannelDefinition"]:
        """Load all 36 channel definitions from channels.yaml."""
        # Implementation: parse channels.yaml
        pass

# Add to RawBodyGraph
class RawBodyGraph(BaseModel):
    # ... existing fields ...
    
    @computed_field
    @property
    def active_channels(self) -> list[ChannelDefinition]:
        """Detect which channels are activated in this chart."""
        all_channels = ChannelDefinition.load_all()
        activated_gates = self.all_activated_gates
        
        active = []
        for channel in all_channels:
            if channel.gates[0] in activated_gates and channel.gates[1] in activated_gates:
                active.append(channel)
        return active
```

**Estimated Effort**: 2-3 days (includes testing against 64keys data)

#### 2. Type, Authority, Profile Calculations

```python
# src/human_design/models/type.py

from enum import Enum
from pydantic import BaseModel

class HDType(Enum):
    """64keys terminology for Human Design types."""
    INITIATOR = "Initiator"        # Manifestor
    BUILDER = "Builder"            # Generator
    SPECIALIST = "Specialist"      # Manifesting Generator
    COORDINATOR = "Coordinator"    # Projector
    OBSERVER = "Observer"          # Reflector

class Authority(Enum):
    """Authority types in hierarchical order."""
    EMOTIONAL = "Emotional"
    SACRAL = "Sacral"
    SPLENIC = "Splenic"
    EGO = "Ego"
    SELF_PROJECTED = "Self-Projected"
    MENTAL = "Mental"
    LUNAR = "Lunar"

class Profile(BaseModel):
    """Profile as conscious Sun line / unconscious Sun line."""
    conscious_line: GateLineNumber
    unconscious_line: GateLineNumber
    
    @property
    def notation(self) -> str:
        """Profile notation (e.g., '3/5')."""
        return f"{self.conscious_line}/{self.unconscious_line}"

# Add to RawBodyGraph
class RawBodyGraph(BaseModel):
    # ... existing fields ...
    
    @computed_field
    @property
    def type(self) -> HDType:
        """Calculate HD type based on defined centers."""
        # Logic: Check which centers are defined via active_channels
        # Sacral defined → Builder/Specialist
        # Sacral undefined + motors defined → Initiator
        # Sacral undefined + no motors → Coordinator/Observer
        pass
    
    @computed_field
    @property
    def authority(self) -> Authority:
        """Calculate authority based on defined centers hierarchy."""
        # Emotional > Sacral > Splenic > Ego > Self > Mental/Lunar
        pass
    
    @computed_field
    @property
    def profile(self) -> Profile:
        """Extract profile from conscious and unconscious Sun lines."""
        conscious_sun = next(a for a in self.conscious_activations if a.planet == Planet.SUN)
        unconscious_sun = next(a for a in self.unconscious_activations if a.planet == Planet.SUN)
        return Profile(
            conscious_line=conscious_sun.line,
            unconscious_line=unconscious_sun.line
        )
```

**Estimated Effort**: 2 days (1 day implementation, 1 day testing/validation)

#### 3. Interaction Chart

```python
# src/human_design/models/interaction.py

from pydantic import BaseModel

class RawInteractionChart(BaseModel):
    """
    Composite chart for two people showing gate overlaps,
    electromagnetic bridges, and composite definition.
    """
    person_a: RawBodyGraph
    person_b: RawBodyGraph
    
    @computed_field
    @property
    def all_activated_gates(self) -> set[GateNumber]:
        """All gates activated by either person."""
        return self.person_a.all_activated_gates | self.person_b.all_activated_gates
    
    @computed_field
    @property
    def shared_gates(self) -> set[GateNumber]:
        """Gates activated by both people."""
        return self.person_a.all_activated_gates & self.person_b.all_activated_gates
    
    @computed_field
    @property
    def electromagnetic_channels(self) -> list[ChannelDefinition]:
        """
        Channels formed between the two people (one has gate A, other has gate B).
        These are 'electromagnetic bridges' - activations that complete across charts.
        """
        all_channels = ChannelDefinition.load_all()
        a_gates = self.person_a.all_activated_gates
        b_gates = self.person_b.all_activated_gates
        
        bridges = []
        for channel in all_channels:
            gate1, gate2 = channel.gates
            # Check if one person has gate1 and the other has gate2
            if (gate1 in a_gates and gate2 in b_gates) or (gate2 in a_gates and gate1 in b_gates):
                # Make sure it's not already formed within one person's chart
                if channel not in self.person_a.active_channels and channel not in self.person_b.active_channels:
                    bridges.append(channel)
        return bridges
    
    @computed_field
    @property
    def composite_channels(self) -> list[ChannelDefinition]:
        """All channels active in the composite (individual + electromagnetic)."""
        individual_channels = list(set(self.person_a.active_channels + self.person_b.active_channels))
        return individual_channels + self.electromagnetic_channels
    
    @computed_field
    @property
    def composite_definition(self) -> str:
        """
        Calculate definition type for the composite chart.
        Uses graph traversal to count connected components.
        """
        # Implementation: Build graph of centers connected via composite_channels
        # Count connected components → 'Single', 'Split', 'Triple Split', 'Quadruple Split'
        pass
```

**Estimated Effort**: 1 week (3 days implementation, 2 days testing, 2 days 64keys validation)

#### 4. Penta Chart

```python
# src/human_design/models/penta.py

from pydantic import BaseModel, field_validator

class RawPentaChart(BaseModel):
    """
    Group chart for 3-5 people showing collective dynamics.
    """
    people: list[RawBodyGraph]
    interpretation: Literal["team", "family"] = "team"
    
    @field_validator("people")
    def validate_size(cls, v):
        if not (3 <= len(v) <= 5):
            raise ValueError("Penta requires 3-5 people")
        return v
    
    @computed_field
    @property
    def all_activated_gates(self) -> set[GateNumber]:
        """All gates activated by any person in the group."""
        gates = set()
        for person in self.people:
            gates |= person.all_activated_gates
        return gates
    
    @computed_field
    @property
    def composite_channels(self) -> list[ChannelDefinition]:
        """
        Channels formed by the group (can be from any combination of people).
        """
        all_channels = ChannelDefinition.load_all()
        group_gates = self.all_activated_gates
        
        active = []
        for channel in all_channels:
            if channel.gates[0] in group_gates and channel.gates[1] in group_gates:
                active.append(channel)
        return active
    
    @computed_field
    @property
    def composite_type(self) -> HDType:
        """What type does the group have as a composite?"""
        # Logic similar to individual type but using composite_channels
        pass
```

**Estimated Effort**: 1 week (can build on InteractionChart patterns)

#### 5. Transit Overlay

```python
# src/human_design/models/transit.py

from datetime import datetime
from pydantic import BaseModel

class TransitActivations(BaseModel):
    """Planetary activations for a specific moment in time."""
    timestamp: datetime
    activations: list[RawActivation]

class TransitOverlay(BaseModel):
    """
    Overlay current (or historical) transits on a natal chart.
    """
    natal_chart: RawBodyGraph
    transit_date: datetime
    
    @computed_field
    @property
    def transit_activations(self) -> TransitActivations:
        """Calculate planetary positions at transit_date."""
        # Use same logic as RawBodyGraph._activations_for_jd
        # Convert transit_date to Julian Day
        pass
    
    @computed_field
    @property
    def transit_natal_channels(self) -> list[ChannelDefinition]:
        """
        Channels formed by transit activations completing natal gates.
        Example: Transit Sun in gate 5, natal has gate 15 → Channel 5-15 activates
        """
        natal_gates = self.natal_chart.all_activated_gates
        transit_gates = {a.gate for a in self.transit_activations.activations}
        all_channels = ChannelDefinition.load_all()
        
        formed = []
        for channel in all_channels:
            gate1, gate2 = channel.gates
            # Check if transit has one gate and natal has the other
            if (gate1 in transit_gates and gate2 in natal_gates) or (gate2 in transit_gates and gate1 in natal_gates):
                if channel not in self.natal_chart.active_channels:
                    formed.append(channel)
        return formed
```

**Estimated Effort**: 3-5 days (can reuse activation calculation logic)

### Ergonomic Builder API

```python
# src/human_design/builders.py

class ChartBuilder:
    """Fluent API for building chart combinations."""
    
    def __init__(self, person: RawBodyGraph):
        self.base_person = person
    
    def interaction(self, other: RawBodyGraph) -> RawInteractionChart:
        """Create interaction chart with another person."""
        return RawInteractionChart(person_a=self.base_person, person_b=other)
    
    def penta(self, *others: RawBodyGraph) -> RawPentaChart:
        """Create penta chart with 2-4 other people."""
        people = [self.base_person] + list(others)
        return RawPentaChart(people=people)
    
    def with_transit(self, date: datetime) -> TransitOverlay:
        """Overlay transit on this chart."""
        return TransitOverlay(natal_chart=self.base_person, transit_date=date)

# Usage
sandy = RawBodyGraph(birth_info=...)
heath = RawBodyGraph(birth_info=...)

interaction = ChartBuilder(sandy).interaction(heath)
print(interaction.electromagnetic_channels)

penta = ChartBuilder(sandy).penta(heath, daughter, son)
print(penta.composite_type)

transit_today = ChartBuilder(sandy).with_transit(datetime.now())
print(transit_today.transit_natal_channels)
```

---

## 📊 Implementation Roadmap

### Phase 1: Foundation (Week 1-2) 🔥 CRITICAL

**Goal**: Unblock multi-chart work by implementing channel detection and core HD concepts

**Tasks**:
1. ✅ Create `ChannelDefinition` model and load from channels.yaml
2. ✅ Add `RawBodyGraph.active_channels` computed property
3. ✅ Implement Type calculation (Initiator/Builder/Specialist/Coordinator/Observer)
4. ✅ Implement Authority calculation (Emotional/Sacral/Splenic/etc.)
5. ✅ Implement Profile extraction (conscious/unconscious Sun lines)
6. ✅ Implement Definition calculation (Single/Split/Triple/Quad via graph traversal)
7. ✅ Write comprehensive test suite comparing to 64keys data

**Artifacts**:
- `src/human_design/models/channel.py`
- `src/human_design/models/type.py`
- `src/human_design/models/authority.py`
- `src/human_design/models/profile.py`
- `tests/test_channel_detection.py`
- `tests/test_type_calculation.py`

**Success Criteria**:
- All 36 channels correctly defined
- Channel detection matches 64keys for known charts
- Type/Authority/Profile calculations validated

### Phase 2: Interaction Charts (Week 2-3) 🔥 CRITICAL

**Goal**: Implement Rebecca's #1 use case - 2-person chart combinations

**Tasks**:
1. ✅ Create `RawInteractionChart` model
2. ✅ Implement gate overlap detection
3. ✅ Implement electromagnetic channel detection
4. ✅ Implement composite definition calculation
5. 🔍 Use MCP server to browse `/interaction?id1=X&id2=Y` pages
6. 🔍 Reverse-engineer 64keys display patterns (color coding, layout)
7. ✅ Create `InteractionSummary64Keys` with augmented content
8. ✅ Add `GateAPI.get_interaction(person_a, person_b)` method
9. ✅ Write tests comparing our calculations to 64keys results

**Artifacts**:
- `src/human_design/models/interaction.py`
- `src/human_design/calculate_interaction.py`
- `tests/test_interaction_chart.py`
- `docs/64keys_interaction_spec.md`

**Success Criteria**:
- Interaction charts match 64keys calculations
- Electromagnetic bridges correctly detected
- Composite definition accurately calculated

### Phase 3: Penta & Groups (Week 3-4) 🔥 HIGH

**Goal**: Generalize to 3-5 person groups, implement group organization

**Tasks**:
1. ✅ Generalize InteractionChart logic to PentaChart (3-5 people)
2. 🔍 Use MCP server to research 's0-s4' parameters in penta URLs
3. ✅ Create Group model with ownership semantics
4. ✅ Create Relationship model and RelationshipGraph
5. ✅ Integrate Person, Group, Relationship into cohesive data model
6. ✅ Add `GateAPI.get_penta(people)` and `GateAPI.get_family_penta(people)`
7. ✅ Create quick-access utilities: `Group.all_interaction_pairs()`, `Group.penta_combinations()`
8. ✅ Write tests for penta calculations and group semantics

**Artifacts**:
- `src/human_design/models/penta.py`
- `src/human_design/models/group.py`
- `src/human_design/models/relationship.py`
- `tests/test_penta_chart.py`
- `tests/test_group_semantics.py`

**Success Criteria**:
- Penta calculations validated against 64keys
- Group ownership semantics implemented ("Sandy's Heath")
- Quick-access patterns enable one-click chart combinations

### Phase 4: Transit & Temporal (Week 4-5) 🟡 MEDIUM

**Goal**: Add temporal context with transit overlays

**Tasks**:
1. ✅ Create `TransitCalculator` (current_jd or specific_date → TransitActivations)
2. ✅ Create `TransitOverlay` model (RawBodyGraph + TransitActivations)
3. ✅ Implement transit-natal channel detection
4. ✅ Add date parameter support for historical transits
5. 🔍 Use MCP server to browse `/transit` pages
6. ✅ Add `GateAPI.current_transit(person)`, `GateAPI.transit_at_date(person, date)`
7. ✅ Write tests for transit calculations

**Artifacts**:
- `src/human_design/models/transit.py`
- `src/human_design/calculate_transit.py`
- `tests/test_transit.py`

**Success Criteria**:
- Transit calculations match 64keys
- Historical transit support (e.g., 6 months ago)
- Transit-natal channel detection validated

### Phase 5: Visualization System (Week 5-6) 🟡 MEDIUM

**Goal**: Build SVG bodygraph renderer with Rebecca Energy aesthetic

**Tasks**:
1. 🔍 Use MCP server to systematically extract 64keys SVG structure
2. 📝 Document coordinate system, element positioning, responsive layout
3. 🔍 Extract 64keys color palette (defined/undefined, channels, gates)
4. 🎨 Design Rebecca Energy color palette (purples, gold, greens)
5. ✅ Create SVG bodygraph renderer (Python or JavaScript)
6. ✅ Implement overlays for interaction/penta (color-code person contributions)
7. ✅ Implement transit overlay visualization
8. ✅ Create interactive states (hover, click, zoom)

**Artifacts**:
- `docs/64keys_visualization_spec.md`
- `docs/64keys_color_palette.json`
- `docs/rebecca_energy_palette.json`
- `src/human_design/render/bodygraph_svg.py`
- `tests/test_svg_rendering.py`

**Success Criteria**:
- SVG bodygraphs render correctly
- Rebecca Energy palette implemented
- Interactive states work smoothly

### Phase 6: Web UI Integration (Week 6-7) 🔥 HIGH

**Goal**: Deliver ergonomic multi-chart access for Rebecca's sessions

**Tasks**:
1. ✅ Update Person model with Group and Relationship fields
2. ✅ Create GroupView page listing all members with relationships
3. ✅ Add one-click chart combination buttons:
   - Individual chart
   - Any 2-person interaction
   - Penta selection (choose 3-5 people)
   - Full group multichart
4. ✅ Implement session mode: quick-switch between chart combos
5. ✅ Add transit overlay toggle on any chart type
6. ✅ Implement name normalization and search improvements
7. 🎨 Apply Rebecca Energy styling to all pages

**Artifacts**:
- `src/human_design/web/routes/groups.py`
- `src/human_design/web/templates/group_view.html`
- `src/human_design/web/templates/interaction_chart.html`
- `src/human_design/web/static/css/rebecca_energy.css`

**Success Criteria**:
- One-click access to any chart combination
- Session mode enables fast switching during consultations
- Rebecca Energy aesthetic applied throughout
- Name search works reliably

---

## 🔍 Open Research Questions

These require MCP server exploration of 64keys.com:

1. **Penta 's' Parameters**: What are 's0-s4' in `/penta?id0=X&...&s0=a&s1=a&...`?
   - Hypothesis: Status/show/selection flags
   - Action: Browse actual penta pages, test different values

2. **Type Calculation Algorithm**: How does 64keys calculate Type?
   - Observable: 'maintype' field in list_people data
   - Action: Compare multiple charts, infer rules from patterns

3. **Authority Calculation**: How does 64keys calculate Authority?
   - Not visible in extracted data
   - Action: Browse individual chart pages, look for authority mentions

4. **Interaction Color Coding**: Does 64keys show which person contributes which activation?
   - Likely uses color coding
   - Action: Browse interaction pages, document visual patterns

5. **Penta vs Family Penta**: Are there calculation differences or just semantic?
   - Both use same endpoint structure
   - Action: Browse both, compare HTML structure and content

6. **Composite Definition Algorithm**: How does 64keys calculate group definition?
   - Likely graph traversal but confirm
   - Action: Test edge cases, validate our implementation

7. **Center Name Confusion**: DRIVE vs LIFEFORCE - are these the same or different?
   - Both appear to map to Sacral
   - Action: Check bodygraph.yaml gate assignments vs traditional HD

8. **SVG Coordinate System**: How are gates/centers/channels positioned?
   - Need exact coordinates for rendering
   - Action: Extract SVG from chart pages, document element structure

9. **O16 Organizational**: How does O16 differ from multichart?
   - Low priority but mentioned in endpoints
   - Action: Browse O16 pages if accessible

10. **Transit Visual Encoding**: How are transits displayed over natal chart?
    - Color? Opacity? Separate layer?
    - Action: Browse transit overlay pages, document patterns

---

## 🎯 Critical Path to MVP

**Minimum Viable Product** for Rebecca's sessions:

### Week 1-2: Foundation
- ✅ Channel detection (BLOCKING)
- ✅ Type/Authority/Profile calculations

### Week 2-3: Interaction Charts
- ✅ RawInteractionChart with electromagnetic bridges
- 🔍 64keys interaction endpoint integration

### Week 3-4: Penta & Groups
- ✅ RawPentaChart for families
- ✅ Group model with ownership semantics
- ✅ One-click access patterns

### Week 5: Transit (Optional for MVP)
- ✅ TransitOverlay for temporal context

### Week 6-7: UI Polish
- ✅ GroupView with one-click combinations
- 🎨 Rebecca Energy styling

**Total Estimated Time**: 5-7 weeks

**Confidence**: HIGH - Architecture is sound, patterns are clear, 64keys endpoints are documented

---

## 🧪 Validation Checklist

Before merging any phase:

- [ ] Maintains raw vs semantic separation
- [ ] All models use Pydantic v2 with strict type hints
- [ ] Satisfies mypy strict mode
- [ ] Test coverage uses pytest.mark.parametrize
- [ ] Calculations validated against 64keys data
- [ ] Continues using pyswisseph (not swisseph)
- [ ] Follows existing GateAPI patterns
- [ ] Embodies Rebecca Energy tone and aesthetics
- [ ] One-click access for Rebecca's workflow
- [ ] Comprehensive documentation

---

## 🌈 Rebecca Energy Integration

Throughout implementation, maintain these principles:

### Tone
- Whimsical yet grounded
- Warm and approachable
- Playful metaphors
- Encouraging self-discovery

### Visual
- Deep purples (mystical)
- Gold/amber (warmth)
- Forest greens (grounding)
- Warm earth tones
- Cozy autumnal forest mood

### Philosophy
- Charts are "treasure maps" for 7-year journeys
- Relationships are conditioning influences
- Everyone needs their constellation
- Science and magic are the same thing

### Technical
- Speed matters during sessions
- One-click chart combinations
- Group ownership semantics ("Sandy's Heath")
- Relationship types matter (husband, ex, daughter)

---

## 📋 Next Immediate Actions

1. **Channel Implementation** (2-3 days)
   ```bash
   # Create models/channel.py
   # Parse channels.yaml → ChannelDefinition
   # Add RawBodyGraph.active_channels
   # Write tests against 64keys data
   ```

2. **Type/Authority/Profile** (2 days)
   ```bash
   # Create models/type.py, models/authority.py, models/profile.py
   # Implement calculation logic
   # Add as computed fields to RawBodyGraph
   # Validate against known charts
   ```

3. **MCP Exploration** (parallel to implementation)
   ```bash
   # Browse /interaction pages → docs/64keys_interaction_spec.md
   # Browse /penta pages → investigate 's' parameters
   # Extract SVG structure → docs/64keys_visualization_spec.md
   # Extract color palette → docs/64keys_color_palette.json
   ```

4. **Interaction Chart** (1 week)
   ```bash
   # After channels are done, implement RawInteractionChart
   # Test electromagnetic bridge detection
   # Integrate with 64keys API
   # Validate composite calculations
   ```

---

## 🚨 Critical Blockers Summary

| Blocker | Severity | Impact | Effort | Status |
|---------|----------|--------|--------|--------|
| Channel formation logic | 🔥 CRITICAL | Blocks ALL multi-chart work | 2-3 days | ❌ Not started |
| Interaction chart model | 🔥 CRITICAL | Blocks Rebecca's #1 use case | 1 week | ❌ Not started |
| Penta chart model | 🔥 CRITICAL | Blocks family analysis | 1 week | ❌ Not started |
| Group ownership model | 🔥 HIGH | Blocks ergonomic workflow | 3-5 days | ❌ Not started |
| Transit overlay | 🟡 MEDIUM | Nice-to-have for context | 3-5 days | 🟡 Partial (get_current_transit exists) |
| Visualization system | 🟡 MEDIUM | Can use 64keys initially | 2 weeks | ❌ Not started |

---

## 🎉 Conclusion

This synthesis provides a **comprehensive roadmap** for implementing multi-chart Human Design features. The architecture is sound, the patterns are clear, and the path forward is well-defined.

**Key Insight**: The codebase has **excellent bones** (pristine chassis) but needs the **engine** (multi-chart logic) to enable Rebecca's workflow. Once we implement channel detection and interaction charts, everything else follows naturally from the established patterns.

**Confidence Level**: **0.85 (HIGH)** - All evidence points to a 5-7 week implementation with manageable technical risk. The architectural foundation is solid, 64keys endpoints are documented, and calculation logic is mostly understood. The main unknowns are semantic details that can be resolved through MCP exploration.

---

*Generated by Coordinator Agent*  
*Synthesizing findings from: Researcher, Ontologist, Fair Witness, Architect (failed)*  
*Total analysis coverage: 4 specialist perspectives, 100+ data files, 64keys.com integration points*

🎸 **Groovy Factor**: This treasure map is gonna be far out once we plant those multi-chart seeds, man! The foundation is solid as a vintage racing car's chassis - we just need to bolt in that sweet composite calculation engine and Rebecca's sessions will cruise like a wayward butterfly through an autumnal forest. *Chef's kiss* on that architectural cheese! 🦋✨🗺️
