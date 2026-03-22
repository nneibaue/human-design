# HD_ONTOLOGY_complete.json Usage Guide

## Overview

`HD_ONTOLOGY_complete.json` is the comprehensive Human Design ontology file containing all concepts, relationships, and terminology mappings needed for chart interpretation, UI generation, and educational content.

## Location

```
ontology/HD_ONTOLOGY_complete.json
```

## Purpose

- **Programmatic Access**: Load once at application startup, query throughout runtime
- **UI Generation**: Populate dropdowns, labels, descriptions, and educational tooltips
- **Chart Interpretation**: Provide semantic context for raw calculation outputs
- **Terminology Translation**: Map between 64keys and traditional Human Design terms
- **Educational Content**: Display descriptions, strategies, themes, and interpretations

## Structure

### Root Level

```json
{
  "schema_version": "1.0.0",
  "ontology_standard": "64keys",
  "generated_at": "ISO 8601 timestamp",
  "metadata": {...},
  "types": [...],
  "authorities": [...],
  "profiles": [...],
  "channels": [...],
  "centers": [...],
  "gates": [...],
  "definitions": [...],
  "quarters": [...]
}
```

### Collections

Each collection is an array of objects with consistent structure:

#### Types (5)
- `id`: 64keys name (Initiator, Builder, Specialist, Coordinator, Observer)
- `traditional_name`: Traditional HD name (Manifestor, Generator, etc.)
- `strategy`, `not_self_theme`, `signature`: Core type mechanics
- `calculation_logic`: Rules for determining type from chart data

#### Authorities (7)
- `id`: Authority name (Emotional, Sacral, Splenic, Ego, Self-Projected, Mental, Lunar)
- `hierarchy_rank`: Priority order (1 = highest)
- `center_dependencies`: Required defined centers
- `decision_strategy`: How to make decisions with this authority

#### Profiles (12)
- `id`: Profile notation (e.g., "3/5", "6/2")
- `conscious_line`, `unconscious_line`: Line numbers (1-6)
- `conscious_theme`, `unconscious_theme`: Line interpretations
- `life_phases`: For profiles with Line 6

#### Channels (36)
- `id`: Gate pair (e.g., "1-8")
- `gate1`, `gate2`: Gate numbers
- `centers`: Connected center names
- `circuit`: Individual/Tribal/Collective
- `theme`, `description`: Channel interpretation

#### Centers (9)
- `id`: 64keys name (INSPIRATION, MIND, EXPRESSION, etc.)
- `traditional_name`: Traditional HD name (Head, Ajna, Throat, etc.)
- `type`: Motor/Awareness/Pressure/Identity
- `gates`: Array of gate numbers assigned to this center
- `defined_description`, `undefined_description`: Interpretation by state

#### Gates (64)
- `number`: Gate number (1-64)
- `i_ching_name`: I Ching hexagram name
- `center`: Center assignment
- `complement`: Complement gate number(s)
- `quarter`: Q1/Q2/Q3/Q4

#### Definitions (5)
- `id`: Single/Split/Triple Split/Quadruple Split/None
- `calculation`: Algorithm description
- `implications`: What it means for the person

#### Quarters (4)
- `id`: Q1/Q2/Q3/Q4
- `name`: Initiation/Civilization/Duality/Mutation
- `theme`: Purpose through Mind/Form/Bonding/Transformation

## Usage Patterns

### 1. Load at Startup

```python
import json
from pathlib import Path

def load_ontology():
    ontology_path = Path(__file__).parent / "ontology" / "HD_ONTOLOGY_complete.json"
    with open(ontology_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Global reference
HD_ONTOLOGY = load_ontology()
```

### 2. Query by ID

```python
# Get type information
def get_type_info(type_id: str):
    """
    type_id: '64keys' name like 'Initiator', 'Builder', etc.
    """
    for type_obj in HD_ONTOLOGY['types']:
        if type_obj['id'] == type_id:
            return type_obj
    return None

# Get gate information
def get_gate_info(gate_number: int):
    for gate in HD_ONTOLOGY['gates']:
        if gate['number'] == gate_number:
            return gate
    return None

# Get channel by gate pair
def get_channel_by_gates(gate1: int, gate2: int):
    channel_id = f"{min(gate1, gate2)}-{max(gate1, gate2)}"
    for channel in HD_ONTOLOGY['channels']:
        if channel['id'] == channel_id:
            return channel
    return None
```

### 3. Generate UI Labels

```python
def get_center_label(center_name: str, use_traditional: bool = False):
    """
    Get display label for center.
    center_name: 64keys name like 'INSPIRATION'
    use_traditional: If True, return traditional name like 'Head'
    """
    for center in HD_ONTOLOGY['centers']:
        if center['id'] == center_name:
            return center['traditional_name'] if use_traditional else center['id']
    return center_name

def populate_type_dropdown():
    """Generate dropdown options for Type selector"""
    return [
        {
            'value': type_obj['id'],
            'label': type_obj['traditional_name'],
            'description': type_obj['description']
        }
        for type_obj in HD_ONTOLOGY['types']
    ]
```

### 4. Display Educational Content

```python
def get_profile_description(profile_id: str):
    """
    profile_id: Profile like '3/5', '6/2', etc.
    Returns full profile interpretation
    """
    for profile in HD_ONTOLOGY['profiles']:
        if profile['id'] == profile_id:
            return {
                'name': profile['name'],
                'description': profile['description'],
                'conscious': profile['conscious_theme'],
                'unconscious': profile['unconscious_theme'],
                'life_phases': profile.get('life_phases', None)
            }
    return None

def get_center_interpretation(center_name: str, is_defined: bool):
    """
    Get interpretation based on whether center is defined or undefined
    """
    for center in HD_ONTOLOGY['centers']:
        if center['id'] == center_name:
            desc = center['defined_description'] if is_defined else center['undefined_description']
            return {
                'name': center['traditional_name'],
                'type': center['type'],
                'interpretation': desc,
                'questions': center.get('questions', [])
            }
    return None
```

### 5. Terminology Translation

```python
def translate_type_64keys_to_traditional(type_64keys: str) -> str:
    """
    Convert 64keys type name to traditional HD term
    'Initiator' -> 'Manifestor'
    """
    for type_obj in HD_ONTOLOGY['types']:
        if type_obj['id'] == type_64keys:
            return type_obj['traditional_name']
    return type_64keys

def translate_center_traditional_to_64keys(traditional_name: str) -> str:
    """
    Convert traditional center name to 64keys term
    'Head' -> 'INSPIRATION'
    """
    for center in HD_ONTOLOGY['centers']:
        if center['traditional_name'].lower() == traditional_name.lower():
            return center['id']
    return traditional_name
```

### 6. Integration with RawBodyGraph

```python
from human_design.models.core import RawBodyGraph

def enrich_chart_with_ontology(raw_chart: RawBodyGraph):
    """
    Add semantic context to raw calculation output
    """
    # Get type interpretation
    type_info = get_type_info(raw_chart.type)
    
    # Get profile details
    profile_info = get_profile_description(raw_chart.profile)
    
    # Get defined centers with interpretations
    defined_centers = []
    for center_name, is_defined in raw_chart.centers.items():
        if is_defined:
            center_info = get_center_interpretation(center_name, is_defined=True)
            defined_centers.append(center_info)
    
    # Get active channels with themes
    active_channels = []
    for channel_id in raw_chart.channels:
        channel_info = next(
            (ch for ch in HD_ONTOLOGY['channels'] if ch['id'] == channel_id),
            None
        )
        if channel_info:
            active_channels.append(channel_info)
    
    return {
        'raw_chart': raw_chart,
        'type': type_info,
        'profile': profile_info,
        'defined_centers': defined_centers,
        'channels': active_channels
    }
```

### 7. Validate Chart Calculations

```python
def validate_type_calculation(raw_chart: RawBodyGraph):
    """
    Cross-check that calculated type matches ontology logic
    """
    type_info = get_type_info(raw_chart.type)
    if not type_info:
        return False, f"Type {raw_chart.type} not found in ontology"
    
    calc_logic = type_info['calculation_logic']
    
    # Example: Check if Builder/Generator has Sacral defined
    if raw_chart.type == 'Builder':
        sacral_defined = raw_chart.centers.get('LIFEFORCE', False)
        if not sacral_defined:
            return False, "Builder type requires LIFEFORCE (Sacral) to be defined"
    
    return True, "Type calculation valid"

def validate_channel_formation(gate1: int, gate2: int):
    """
    Check if two gates actually form a channel
    """
    channel_id = f"{min(gate1, gate2)}-{max(gate1, gate2)}"
    channel_info = next(
        (ch for ch in HD_ONTOLOGY['channels'] if ch['id'] == channel_id),
        None
    )
    return channel_info is not None
```

## Data Completeness

The ontology includes:

✅ **Types**: All 5 types with calculation logic, strategies, not-self themes  
✅ **Authorities**: All 7 authorities with hierarchy, decision strategies  
✅ **Profiles**: All 12 profiles with line meanings and life phases  
✅ **Channels**: All 36 channels with gate pairs, centers, circuits, themes  
✅ **Centers**: All 9 centers with 64keys↔traditional mappings, defined/undefined descriptions  
✅ **Gates**: All 64 gates with I Ching names, center assignments, complements  
✅ **Definitions**: All 5 definition types with calculation algorithms  
✅ **Quarters**: All 4 quarters with themes and archetypes  

## Terminology Standard

**Primary**: 64keys terminology  
**Secondary**: Traditional HD terminology in `traditional_name` fields

### Examples

| Concept | 64keys (Primary) | Traditional (Secondary) |
|---------|------------------|-------------------------|
| Type | Initiator | Manifestor |
| Type | Builder | Generator |
| Type | Specialist | Manifesting Generator |
| Type | Coordinator | Projector |
| Type | Observer | Reflector |
| Center | INSPIRATION | Head/Crown |
| Center | MIND | Ajna |
| Center | EXPRESSION | Throat |
| Center | IDENTITY | G-Center/Self |
| Center | WILLPOWER | Heart/Ego |
| Center | EMOTION | Solar Plexus |
| Center | DRIVE | Root |
| Center | LIFEFORCE | Sacral |
| Center | INTUITION | Spleen |

## File Characteristics

- **Format**: JSON (RFC 8259 compliant)
- **Encoding**: UTF-8
- **Size**: ~60KB uncompressed
- **Schema Version**: 1.0.0
- **Human-readable**: 2-space indentation

## Validation

The ontology has been validated against:

- `src/human_design/bodygraph.yaml` (64 gates)
- `src/human_design/channels.yaml` (36 channels)
- `src/human_design/centers.yaml` (9 centers)
- `src/human_design/models/core.py` (type-safe Literals)

All gate-to-center mappings, channel gate pairs, and center names match the source data exactly.

## Extensibility

The JSON structure allows adding custom fields without breaking existing consumers:

```json
{
  "id": "Builder",
  "traditional_name": "Generator",
  "strategy": "Wait to respond",
  // ... standard fields ...
  
  // Custom extension fields
  "custom_theme_color": "#8B4513",
  "custom_icon": "builder-icon.svg",
  "custom_audio_url": "https://example.com/builder-intro.mp3"
}
```

## Version Management

The `schema_version` field supports ontology evolution:

```python
def check_ontology_version():
    required_version = "1.0.0"
    actual_version = HD_ONTOLOGY['schema_version']
    
    if actual_version != required_version:
        raise ValueError(
            f"Ontology version mismatch: expected {required_version}, got {actual_version}"
        )
```

## Best Practices

1. **Load Once**: Load the ontology file once at application startup, not per request
2. **Cache Queries**: Build lookup dictionaries if querying frequently
3. **Validate References**: Check that chart data references valid ontology IDs
4. **Use Type-Safe Access**: Validate IDs exist before accessing nested fields
5. **Display Both Terms**: Show 64keys terms primarily, traditional in tooltips/help
6. **Update Documentation**: If extending ontology, document custom fields

## Integration Example: Chart Display Component

```python
def render_chart_summary(raw_chart: RawBodyGraph):
    """
    Generate rich chart summary using ontology data
    """
    type_info = get_type_info(raw_chart.type)
    profile_info = get_profile_description(raw_chart.profile)
    
    # Get authority info
    authority_info = None
    for auth in HD_ONTOLOGY['authorities']:
        if auth['id'] == raw_chart.authority:
            authority_info = auth
            break
    
    return {
        'type': {
            'name': type_info['traditional_name'],
            'strategy': type_info['strategy'],
            'not_self': type_info['not_self_theme'],
            'signature': type_info['signature'],
            'description': type_info['description']
        },
        'profile': {
            'notation': profile_info['id'],
            'name': profile_info['name'],
            'description': profile_info['description']
        },
        'authority': {
            'name': authority_info['id'],
            'strategy': authority_info['decision_strategy'],
            'time_frame': authority_info.get('time_frame', '')
        },
        'definition': raw_chart.definition,
        'channels_count': len(raw_chart.channels),
        'defined_centers_count': sum(1 for defined in raw_chart.centers.values() if defined)
    }
```

## Support

For questions about ontology structure, data accuracy, or integration patterns:

1. Review this documentation
2. Check `IMPLEMENTATION_NOTES_ontology.md` for technical details
3. Validate against source YAML files in `src/human_design/`
4. Cross-reference with `src/human_design/models/core.py` type definitions

## Related Files

- `ontology/HD_ONTOLOGY_schema.json` - JSON Schema v7 definition (if generated)
- `docs/IMPLEMENTATION_NOTES_ontology.md` - Technical implementation guidance
- `src/human_design/bodygraph.yaml` - Source data for gates
- `src/human_design/channels.yaml` - Source data for channels
- `src/human_design/centers.yaml` - Source data for centers
- `src/human_design/models/core.py` - Type-safe Python definitions
