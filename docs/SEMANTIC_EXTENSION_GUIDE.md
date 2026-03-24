# Semantic Extension Guide: Creating Custom Human Design Interpretation Systems

**Status**: DRAFT  
**Audience**: Community contributors, Rebecca (Jolly Alchemy), third-party semantic system creators  
**Prerequisites**: Understanding of Human Design basics (gates, channels, types, authorities)

---

## Overview

The Human Design codebase **separates deterministic calculations from semantic interpretations**:

```
Raw Calculations (immutable)  →  Semantic Layer (hot-swappable)  →  User-Facing Descriptions
  gate 42, line 3                      "Maturation" (64keys)             "The gift of completion..."
  channel 42-53                        OR "Increase" (Ra)               
  type: sacral_motor_throat            OR "Harvest Cycle" (Jolly)
```

This guide teaches you how to create your own semantic interpretation system (terminology, descriptions, meanings) **without modifying any code**.

---

## Quick Start

### Step 1: Copy the Template

```bash
cd ontology/semantics/
cp -r _template/ my_system/
cd my_system/
```

### Step 2: Edit `manifest.yaml`

```yaml
# ontology/semantics/my_system/manifest.yaml
system_id: my_system
version: "1.0.0"
author: "Your Name"
license: "CC-BY-4.0"  # or your preferred license
description: |
  My custom Human Design interpretation system that emphasizes...
  
compatibility:
  core_version: ">=1.0.0"  # Minimum core ontology version required
```

### Step 3: Define Your Type Names

```yaml
# ontology/semantics/my_system/types.yaml
- type_code: sacral_defined_no_motor_throat
  display_name: "Pure Builder"             # Your terminology
  traditional_name: "Generator"            # Optional cross-reference
  strategy: "Wait to respond"
  signature: "Satisfaction"
  not_self_theme: "Frustration"
  description: |
    Pure Builders have sustainable energy when responding to what they love.
    Your custom interpretation here...

- type_code: sacral_motor_throat
  display_name: "Energized Catalyst"       # Example: Jolly Alchemy flavor
  traditional_name: "Manifesting Generator"
  strategy: "Respond and inform"
  signature: "Satisfaction and peace"
  not_self_theme: "Frustration and anger"
  description: |
    Energized Catalysts have both generator energy and manifestor quickness...
```

### Step 4: Describe a Gate

```yaml
# ontology/semantics/my_system/gates/gate_42.yaml
gate_number: 42
name: "The Harvest Cycle"                 # Your gate name
quarter: "Quarter of Initiation"          # Optional
summary: "Growth through completion of natural cycles"
description: |
  Gate 42 represents the natural rhythm of starting and finishing.
  Your full interpretation here...
  
strive: |
  Honor the natural timing of beginnings and endings.
  Your guidance here...

lines:
  - line_number: 1
    title: "The Seed"
    text: "New beginnings require patience as seeds germinate..."
    
  - line_number: 2
    title: "The Sprout"
    text: "Early growth is delicate..."
    
  # ... lines 3-6
```

### Step 5: Use Your System

```python
from human_design import GateAPI, RawBodyGraph, BirthInfo

# Load your custom semantic system
api = GateAPI(semantic_system="my_system")

# Calculate raw bodygraph
birth_info = BirthInfo(
    date="1990-01-01",
    localtime="1990-01-01T12:00:00",
    city="New York",
    country="USA"
)
raw = RawBodyGraph(birth_info=birth_info)

# Get summary with YOUR terminology and descriptions
summary = api.bodygraph_to_summary(raw)
print(summary.type.display_name)  # "Energized Catalyst" (your term)
```

---

## File Structure Reference

All semantic systems follow this structure:

```
ontology/semantics/my_system/
├── manifest.yaml              # System metadata (required)
├── types.yaml                 # Type names and descriptions (required)
├── authorities.yaml           # Authority names and descriptions (required)
├── centers.yaml               # Center names and descriptions (required)
├── profiles.yaml              # Profile names and descriptions (required)
│
├── gates/                     # Gate-by-gate descriptions
│   ├── gate_01.yaml
│   ├── gate_02.yaml
│   └── ...                    # gate_64.yaml
│
└── README.md                  # Your system's philosophy (optional)
```

---

## Schema Reference

### `manifest.yaml` (Required)

```yaml
system_id: string              # Unique identifier (lowercase, underscores)
version: string                # Semantic versioning (e.g., "1.0.0")
author: string                 # Your name or organization
license: string                # License identifier (e.g., "CC-BY-4.0", "MIT")
description: string            # Multi-line description of your system
compatibility:
  core_version: string         # Minimum core ontology version (e.g., ">=1.0.0")
```

**Validation Rules**:
- `system_id` must match directory name
- `version` must follow semantic versioning
- `license` recommended (default: CC-BY-4.0)

---

### `types.yaml` (Required)

Each type must specify:

```yaml
- type_code: string            # Internal code (MUST match core topology)
  display_name: string         # Your terminology (e.g., "Energized Catalyst")
  traditional_name: string?    # Optional Ra Uru Hu term (e.g., "Manifesting Generator")
  strategy: string             # Decision-making strategy
  signature: string            # When aligned
  not_self_theme: string       # When not aligned
  description: string          # Full type description
  
  # Optional custom fields
  keywords: list[string]?
  famous_examples: list[string]?
  extra: dict?                 # Any custom fields
```

**Required Type Codes** (must include all 5):
- `no_definition` → Observer/Reflector
- `sacral_defined_no_motor_throat` → Builder/Generator
- `sacral_motor_throat` → Specialist/Manifesting Generator
- `motor_throat_no_sacral` → Initiator/Manifestor
- `other_definition` → Coordinator/Projector

**Example**:
```yaml
- type_code: sacral_motor_throat
  display_name: "The Energized Catalyst"
  traditional_name: "Manifesting Generator"
  strategy: "Respond, then inform before acting"
  signature: "Satisfaction and peace"
  not_self_theme: "Frustration and anger"
  description: |
    Energized Catalysts blend the sustainable power of Builders with the
    initiating speed of Initiators. You're designed to respond to opportunities,
    but once committed, you move fast and skip steps that aren't essential.
  keywords:
    - multi-passionate
    - efficient
    - quick manifestor
  famous_examples:
    - "Beyoncé"
    - "Frida Kahlo"
```

---

### `authorities.yaml` (Required)

Each authority must specify:

```yaml
- authority_code: string       # Internal code (MUST match core logic)
  display_name: string         # Your terminology
  traditional_name: string?    # Optional Ra term
  center_dependencies: list    # Which centers must be defined
  decision_strategy: string    # How to use this authority
  time_frame: string           # How long decisions take
  description: string          # Full authority description
```

**Required Authority Codes** (must include all 7, in hierarchy order):
1. `emotional` → Emotional/Solar Plexus
2. `sacral` → Sacral
3. `splenic` → Splenic
4. `ego` → Ego/Heart/Will
5. `self` → Self-Projected/G-Center
6. `mental` → Mental/Environmental
7. `lunar` → Lunar/None (Reflectors)

**Example**:
```yaml
- authority_code: emotional
  display_name: "Wave Wisdom"
  traditional_name: "Emotional Authority"
  center_dependencies: ["EMOTION"]
  decision_strategy: "Ride your emotional wave before deciding"
  time_frame: "Days to weeks (full wave cycle)"
  description: |
    Wave Wisdom requires patience. Your emotions move in waves from hope to
    disappointment and back. There is no truth in the now - only over time.
    Wait for emotional clarity by experiencing the full wave before big decisions.
  hierarchy_rank: 1            # Highest priority
  custom_guidance: |
    Ask yourself: "How will I feel about this in 3 days? In a week?"
```

---

### `centers.yaml` (Required)

Each center must specify meanings for **both defined and undefined states**:

```yaml
- center_name: string          # MUST match CenterName enum (e.g., "LIFEFORCE")
  display_name: string         # Your terminology (e.g., "Source Well")
  traditional_name: string?    # Optional Ra term (e.g., "Sacral")
  function: string             # What this center does
  
  defined_description: string  # When center IS colored in (consistent energy)
  defined_shadow: string?      # Pitfalls when defined
  
  undefined_description: string  # When center is NOT colored in (amplifies others)
  undefined_shadow: string?    # Pitfalls when undefined
  undefined_wisdom: string?    # Gift of undefined state
  
  questions: list[string]?     # Contemplation questions
```

**Required Center Names** (must include all 9):
- `INSPIRATION` (Head/Crown)
- `MIND` (Ajna)
- `EXPRESSION` (Throat)
- `IDENTITY` (G-Center/Self)
- `WILLPOWER` (Heart/Ego)
- `EMOTION` (Solar Plexus)
- `DRIVE` (Root)
- `LIFEFORCE` (Sacral)
- `INTUITION` (Spleen)

**Example**:
```yaml
- center_name: LIFEFORCE
  display_name: "Source Well"
  traditional_name: "Sacral Center"
  function: "Sustainable life force energy and power to work"
  
  defined_description: |
    Your Source Well is full and consistent. You generate sustainable energy
    when responding to what excites you. This is your power source for work.
  defined_shadow: |
    Over-committing to things that don't light you up, leading to burnout.
    
  undefined_description: |
    Your Source Well samples the energy of others. You're not designed for
    exhausting work - you need to use energy wisely and rest when depleted.
  undefined_shadow: |
    Not knowing when to stop. Taking on too much because you feel others' energy.
  undefined_wisdom: |
    You know who has sustainable energy and who doesn't. You're wise about rest.
    
  questions:
    - "Does this light me up?"
    - "Am I working at what I love?"
    - "Am I recognizing when I'm depleted?"
```

---

### `profiles.yaml` (Required)

Each profile must specify:

```yaml
- profile_notation: string     # E.g., "1/3", "4/6"
  display_name: string         # Your terminology
  traditional_name: string?    # Ra's archetype (e.g., "Investigator/Martyr")
  conscious_line: int          # 1-6 (personality)
  unconscious_line: int        # 1-6 (design)
  description: string          # Full profile description
  
  life_theme: string?
  keywords: list[string]?
```

**Required Profiles** (must include all 12):
- 1/3, 1/4, 2/4, 2/5, 3/5, 3/6
- 4/6, 4/1, 5/1, 5/2, 6/2, 6/3

**Example**:
```yaml
- profile_notation: "4/6"
  display_name: "The Networked Sage"
  traditional_name: "Opportunist/Role Model"
  conscious_line: 4
  unconscious_line: 6
  description: |
    You're designed to build networks (line 4) while learning through three
    life phases (line 6). Your influence comes through authentic relationships.
  life_theme: "From chaos to wisdom through connection"
  keywords:
    - networker
    - three life phases
    - authentic influence
```

---

### `gates/gate_XX.yaml` (Required for all 64 gates)

Each gate must specify:

```yaml
gate_number: int               # 1-64 (must match filename)
name: string                   # Your gate name
quarter: string?               # Optional (64keys uses quarters)
summary: string                # One-line essence
description: string            # Full gate description (multi-paragraph OK)
strive: string?                # Optional guidance
keywords: list[string]?        # Optional

lines:                         # MUST include all 6 lines
  - line_number: int           # 1-6
    title: string              # Line name/archetype
    text: string               # Line description
    keywords: list[string]?    # Optional
```

**Example**:
```yaml
# gates/gate_42.yaml
gate_number: 42
name: "The Harvest Cycle"
quarter: "Quarter of Initiation"
summary: "Growth through completion of natural cycles"
description: |
  Gate 42 is the energy of bringing things to completion. Like a farmer
  who plants, tends, and harvests, you understand the natural rhythm of
  beginnings and endings. This gate carries the capacity to finish what
  is started and to know when something has run its course.
  
  In the LIFEFORCE center, this energy is sustainable when you're responding
  to cycles that excite you. You're not here to force completion, but to
  honor the natural timing of growth and maturation.
  
strive: |
  Trust the timing of natural cycles. Don't rush the harvest or prolong
  what has already concluded. Respond to what's ready to complete.
  
keywords:
  - completion
  - growth
  - natural timing
  - harvest

lines:
  - line_number: 1
    title: "The Seed"
    text: |
      Line 1 brings the foundation of beginning. New cycles require patience
      as seeds germinate. Study the conditions for growth before planting.
    keywords: [foundation, patience, preparation]
    
  - line_number: 2
    title: "The Sprout"
    text: |
      Line 2 is the natural emergence. Growth happens when you stop forcing
      and allow natural unfolding. The sprout breaks ground in its own time.
    keywords: [natural, emergence, allowing]
    
  - line_number: 3
    title: "The Roots"
    text: |
      Line 3 discovers through experience. Trial and error teach you about
      what helps growth and what hinders it. Mistakes are part of the process.
    keywords: [experimentation, discovery, resilience]
    
  - line_number: 4
    title: "The Stem"
    text: |
      Line 4 builds the network. Growth is supported by community. You create
      the conditions where others' growth supports yours and vice versa.
    keywords: [community, support, networking]
    
  - line_number: 5
    title: "The Flower"
    text: |
      Line 5 projects solutions. You see how to bring things to full expression.
      Others look to you for guidance on how to complete what they've started.
    keywords: [projection, solutions, leadership]
    
  - line_number: 6
    title: "The Fruit"
    text: |
      Line 6 embodies wisdom. Through three life phases, you discover the art
      of completion. In the third phase, you model mature harvesting for others.
    keywords: [wisdom, maturity, role-model]
```

---

## Validation Checklist

Before publishing your semantic system, ensure:

### Completeness
- [ ] `manifest.yaml` present with all required fields
- [ ] All 5 types defined in `types.yaml`
- [ ] All 7 authorities defined in `authorities.yaml` (in hierarchy order)
- [ ] All 9 centers defined in `centers.yaml`
- [ ] All 12 profiles defined in `profiles.yaml`
- [ ] All 64 gates defined in `gates/gate_01.yaml` through `gates/gate_64.yaml`
- [ ] Each gate has all 6 lines

### Correctness
- [ ] `type_code` values match core topology (no typos)
- [ ] `authority_code` values match core logic
- [ ] `center_name` values match `CenterName` enum exactly
- [ ] `profile_notation` uses correct format (e.g., "1/3" not "1-3")
- [ ] `gate_number` matches filename (e.g., `gate_42.yaml` has `gate_number: 42`)

### Quality
- [ ] Descriptions are multi-paragraph (not just one sentence)
- [ ] No copy-paste errors (check gate names don't repeat)
- [ ] Terminology is consistent throughout (pick names and stick with them)
- [ ] Optional fields used where appropriate (keywords, examples, etc.)

### Testing
```python
# Test loading your system
from human_design.semantic_loader import SemanticLoader

try:
    my_system = SemanticLoader.load("my_system")
    print(f"✅ Loaded {my_system.system_id} v{my_system.version}")
    print(f"   Gates: {len(my_system.gates)}")
    print(f"   Types: {len(my_system.types)}")
    print(f"   Authorities: {len(my_system.authorities)}")
except Exception as e:
    print(f"❌ Validation error: {e}")
```

---

## Advanced Features

### Custom Fields

Add any custom fields to your models using the `extra` dict:

```yaml
# types.yaml
- type_code: sacral_motor_throat
  display_name: "Energized Catalyst"
  # ... standard fields ...
  extra:
    element: "Fire"                    # Your custom taxonomy
    chakra_focus: "Sacral + Solar"
    spirit_animal: "Hummingbird"
    recommended_practices:
      - "Morning response check-in"
      - "Energy tracking journal"
```

Access in code:
```python
type_desc = semantics.get_type_description("sacral_motor_throat")
print(type_desc.extra["spirit_animal"])  # "Hummingbird"
```

### Multi-Language Support

Create language variants as separate systems:

```
ontology/semantics/
├── my_system_en/          # English
├── my_system_es/          # Spanish
└── my_system_fr/          # French
```

Each has same `type_code`, `authority_code`, etc., but different `display_name` and descriptions.

### Versioning

Use semantic versioning in `manifest.yaml`:

```yaml
version: "1.2.0"
changelog: |
  v1.2.0 (2025-02-15):
  - Updated Gate 42 description to emphasize harvest timing
  - Added keywords to all profiles
  
  v1.1.0 (2025-02-01):
  - Expanded type descriptions with famous examples
  
  v1.0.0 (2025-01-15):
  - Initial release
```

---

## Publishing Your System

### Option 1: Pull Request to Core Repo

Submit your semantic system to the community:

```bash
# Fork the repo
git checkout -b semantic-system-my-system

# Add your system
cp -r ontology/semantics/my_system/ ../human-design/ontology/semantics/

# Commit and push
git add ontology/semantics/my_system/
git commit -m "Add My System semantic interpretation"
git push origin semantic-system-my-system

# Open pull request on GitHub
```

**Review Criteria**:
- Completeness (all required files present)
- Validation passes (Pydantic models load successfully)
- Quality (descriptions are substantive, not placeholder text)
- License compatible (CC-BY-4.0 or similar)

### Option 2: External Package

Publish as a separate Python package:

```python
# setup.py
setup(
    name="hd-semantics-my-system",
    version="1.0.0",
    packages=["hd_semantics_my_system"],
    package_data={
        "hd_semantics_my_system": ["ontology/**/*.yaml"],
    },
    install_requires=["human-design>=1.0.0"],
)
```

Users install via pip:
```bash
pip install hd-semantics-my-system
```

Register your system:
```python
from hd_semantics_my_system import register_system
register_system()  # Adds to semantic loader registry
```

---

## FAQ

### Q: Can I use a different gate numbering system?
**A:** No. Gate numbers 1-64 are fixed by the I Ching and zodiac coordinate mappings. You can rename gates (e.g., Gate 42 = "The Harvest Cycle") but the number must stay 42.

### Q: Can I add new types beyond the 5 core types?
**A:** No. Types are determined by topology (which centers are defined and how they connect). However, you can create **subtypes** within types:

```yaml
- type_code: motor_throat_no_sacral
  display_name: "Initiator"
  subtypes:
    - name: "Emotional Initiator"
      condition: "EMOTION center defined"
    - name: "Direct Initiator"  
      condition: "EMOTION center undefined"
```

### Q: What if I disagree with the core ontology (e.g., gate coordinates)?
**A:** Core ontology (gate-to-zodiac mappings, channel pairs) is based on Ra Uru Hu's original system and cannot be changed without creating a different system entirely. The semantic layer is for **interpretation**, not **calculation**.

If you believe there's an error in core coordinates, open an issue with astronomical sources.

### Q: Can I use content from other systems (64keys, Gene Keys, etc.)?
**A:** Only with permission. Most HD content is copyrighted:
- 64keys.com content: © Richard Rudd (requires license)
- Gene Keys: © Richard Rudd (requires license)
- Ra Uru Hu original teachings: © Jovian Archive (requires license)

Your semantic system must be **original content** or have **explicit permission** to republish.

### Q: How do I handle gates with fewer than 6 lines?
**A:** All gates have exactly 6 lines in traditional Human Design. If a system claims fewer lines, either:
1. Research the missing lines from other sources
2. Create placeholder content and mark as incomplete

### Q: Can I merge multiple semantic systems (e.g., 64keys + Gene Keys)?
**A:** Yes, create a hybrid system:

```yaml
# manifest.yaml
system_id: my_hybrid
version: "1.0.0"
author: "Your Name"
description: |
  Hybrid system combining 64keys type names with Gene Keys gate descriptions.
sources:
  - "64keys.com (type terminology)"
  - "Gene Keys (gate interpretations - used with permission)"
```

---

## Examples

### Example 1: Minimalist System

Focus on core types/authorities, minimal gate descriptions:

```yaml
# gates/gate_42.yaml (minimalist)
gate_number: 42
name: "Completion"
summary: "Finishing what you start"
description: "Gate 42 brings things to completion."
lines:
  - line_number: 1
    title: "Foundation"
    text: "Build strong foundations."
  # ... (minimal line descriptions)
```

### Example 2: Maximalist System

Extensive descriptions, keywords, examples:

```yaml
# gates/gate_42.yaml (maximalist)
gate_number: 42
name: "The Harvest Cycle: Growth Through Natural Completion"
quarter: "Quarter of Initiation (Gates 13-24)"
summary: "The sacred energy of bringing cycles to their natural conclusion"
description: |
  [5+ paragraphs of detailed interpretation]
  
strive: |
  [Detailed guidance]
  
keywords:
  - completion
  - harvest
  - maturation
  # ... 10+ keywords
  
biological_correlation: "Sacral chakra, reproductive cycle"
iching_hexagram: 
  number: 42
  name: "Increase"
  judgment: "Increase. It furthers one to undertake something..."
  
lines:
  - line_number: 1
    title: "The Seed: Foundation of New Cycles"
    text: |
      [3+ paragraphs per line]
    keywords: [foundation, patience, study]
    embodiment_practice: "Plant actual seeds and observe their growth cycle"
  # ... (extensive line descriptions)
```

### Example 3: Jolly Alchemy (Rebecca's System)

```yaml
# manifest.yaml
system_id: jolly_alchemy
version: "1.0.0"
author: "Rebecca Energy"
license: "Proprietary"
description: |
  Jolly Alchemy reframes Human Design through the lens of energetic alchemy,
  emphasizing the transformation of raw energy into conscious expression.
  
# types.yaml
- type_code: sacral_motor_throat
  display_name: "The Energized Catalyst"
  traditional_name: "Manifesting Generator"
  strategy: "Alchemize response into swift action"
  signature: "Satisfaction and catalytic impact"
  not_self_theme: "Frustration and scattered energy"
  description: |
    You're an energetic alchemist - transforming responsive power into
    rapid manifestation. Your gift is distilling what matters and moving
    with fierce efficiency...

# centers.yaml
- center_name: LIFEFORCE
  display_name: "The Source Well"
  traditional_name: "Sacral Center"
  function: "Renewable life force and creative power"
  defined_description: |
    Your Source Well is a renewable spring of creative energy...
  # ... Rebecca's custom interpretations
```

---

## Support

### Documentation
- **Core Ontology Reference**: `docs/CORE_ONTOLOGY.md`
- **Semantic Schema API**: `docs/API_SEMANTIC_SCHEMA.md`
- **Example Systems**: Browse `ontology/semantics/64keys/` and `ontology/semantics/ra_traditional/`

### Community
- **Discussions**: GitHub Discussions (ask questions, share systems)
- **Issues**: GitHub Issues (report bugs, request features)
- **Contributing**: `CONTRIBUTING.md`

### Contact
- **Technical Questions**: Open a GitHub issue
- **Content Licensing**: Email the author (see `manifest.yaml`)
- **Custom System Development**: Hire a consultant (see community resources)

---

## Appendix: Type Code Reference

Map your type names to these internal codes:

| Type Code | Topology | 64keys | Ra Traditional |
|-----------|----------|--------|----------------|
| `no_definition` | No centers defined | Observer | Reflector |
| `sacral_defined_no_motor_throat` | Sacral defined, no motor-throat | Builder | Generator |
| `sacral_motor_throat` | Sacral + motor-throat connection | Specialist | Manifesting Generator |
| `motor_throat_no_sacral` | Motor-throat, no Sacral | Initiator | Manifestor |
| `other_definition` | Centers defined but not above | Coordinator | Projector |

## Appendix: Authority Code Reference

Map your authority names to these internal codes (hierarchy order):

| Authority Code | Center Requirements | 64keys | Ra Traditional |
|---------------|---------------------|--------|----------------|
| `emotional` | EMOTION defined | Emotional | Solar Plexus |
| `sacral` | LIFEFORCE defined, no EMOTION | Sacral | Sacral |
| `splenic` | INTUITION defined, no EMOTION/LIFEFORCE | Splenic | Splenic |
| `ego` | WILLPOWER defined, no above | Ego | Ego/Heart |
| `self` | IDENTITY defined, no above | Self | Self-Projected |
| `mental` | MIND defined, no above | Mental | Mental/Environmental |
| `lunar` | No centers defined | Lunar | None/Lunar |

## Appendix: Center Name Reference

Map your center names to these internal codes:

| Center Name (Code) | 64keys | Ra Traditional | Jolly Alchemy (Example) |
|-------------------|--------|----------------|-------------------------|
| `INSPIRATION` | Inspiration | Head/Crown | The Question |
| `MIND` | Mind | Ajna | The Processor |
| `EXPRESSION` | Expression | Throat | The Voice |
| `IDENTITY` | Identity | G-Center/Self | The Compass |
| `WILLPOWER` | Willpower | Heart/Ego | The Promise |
| `EMOTION` | Emotion | Solar Plexus | The Wave |
| `DRIVE` | Drive | Root | The Engine |
| `LIFEFORCE` | Life Force | Sacral | The Source Well |
| `INTUITION` | Intuition | Spleen | The Instinct |

---

**Last Updated**: 2025-01-31  
**Version**: 1.0.0 (DRAFT)  
**Maintainer**: Nathan Neibauer  
**License**: CC-BY-4.0
