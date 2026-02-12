# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python toolkit for Human Design built for Rebecca Jolli of Jolly Alchemy. This project calculates Human Design bodygraphs from birth information using astronomical calculations. The core calculation system is intentionally agnostic of any specific semantic description system (Ra Uru Hu's traditional system, 64keys terminology, or future custom naming).

**Key architectural principle**: Separate raw astronomical calculations from semantic overlays. Raw models (gate numbers, planetary positions, coordinate ranges) should never assume a particular interpretation system.

The project embodies "Rebecca Energy" - whimsical yet grounded, warm and approachable, focusing on self-discovery and deconditioning.

## Development Environment

### Working in Dev Container (Preferred)
This project uses a dev container for consistent development environments:

- **Dockerfile**: Multi-stage build with `development` target
- **Python version**: 3.14 (bookworm base)
- **Container user**: Matches host user (passed via `${localEnv:USER}`)
- **Dependencies**: Installed system-wide from `pip-compile` output of `pyproject.toml`
- **Mounts**: SSH keys, `~/HD` data directory, Docker socket

```bash
# Open in VS Code
# Command Palette → "Dev Containers: Reopen in Container"

# Dependencies are auto-installed via postCreateCommand
# If needed manually:
pip install -e '.[dev]'
```

### CLI Commands
The package provides two equivalent CLI entry points: `human-design` and `hd`

```bash
# Calculate bodygraphs
hd bodygraph 1990-01-15 09:13 Albuquerque NM
hd bodygraph 1990-01-15 09:13 Albuquerque NM --raw  # without 64keys content

# Fetch gate information from 64keys
hd gate 11              # Get Gate 11 info
hd gate 11 --line 11.4  # Get Gate 11, Line 4 info
hd show-gates "1 2 11 42"  # Multiple gates
hd show-gates "1-10"       # Gate range
hd cache-gates             # Cache all 64 gates locally

# AWS operations (when deployed)
hd aws jobs                    # Monitor transcription jobs
hd aws jobs --status RUNNING   # Filter by status
hd aws billing                 # Show AWS costs
hd aws billing --days 7        # Last 7 days
```

### Running Tests
```bash
pytest                                    # Run all tests
pytest tests/test_api.py                  # Run specific test file
pytest -v                                 # Verbose output
pytest tests/test_models_core.py::test_planet_enum  # Specific test
```

### Code Quality
```bash
ruff check .      # Lint
ruff format .     # Format
mypy src/         # Type check
```

## Architecture

**Note**: Models, capabilities, and web app are currently in flux. This architecture represents stable patterns, not final implementation.

### Core Calculation Flow
1. **BirthInfo** → Geocode location, determine timezone
2. **RawBodyGraph** → Calculate planetary positions using Swiss Ephemeris
3. **BodyGraphDefinition** → Map longitudes to gates/lines via `bodygraph.yaml`
4. **Semantic Augmentation** (optional) → Overlay 64keys, Ra, or custom descriptions

The raw calculations are completely independent of any interpretation system.

### Key Architectural Patterns

**Separation of Concerns**:
- `models/bodygraph.py` - Raw astronomical calculations (no semantic content)
- `models/core.py` - Core types (`GateNumber`, `Planet`, `CenterName`) - agnostic of interpretation
- `models/summaries_64keys.py` - 64keys-specific augmentation layer
- Future: `models/summaries_custom.py` or similar for alternative systems

**64keys.com API Integration** (`api.py`):
- `GateAPI` class handles authentication with cached session cookies
- Credentials from environment (`HD_USERNAME`, `HD_PASSWORD`) or AWS Secrets Manager
- Session cache: `~/.config/human-design/session.json`
- **Important quirk**: Must call `list_prepare` endpoint before `list_api` (session-based filtering)

**Astronomical Calculations**:
- Uses Swiss Ephemeris via `pyswisseph` (not `swisseph` - note the 'py')
- Conscious activations: birth time
- Unconscious activations: ~88 days before birth (Design time)
- Calculations use sidereal zodiac (not tropical)

### Important Development Patterns

**Pydantic v2**:
- All models use Pydantic v2 for validation
- Type hints required (mypy strict mode enabled)
- Use `GateNumber`, `CenterName`, `Planet` Literal types for compile-time validation

**Testing with pytest.mark.parametrize**:
Use parametrized tests to reduce duplication when testing the same logic with different inputs:
```python
@pytest.mark.parametrize("gate_num,expected_name", [(1, "Gate 1"), (11, "Gate 11")])
def test_gates(gate_num, expected_name):
    gate = get_gate(gate_num)
    assert gate.name == expected_name
```

**Rebecca's Workflow Priorities**:
During client sessions, Rebecca needs to:
1. **Quickly pull up chart combinations** - individual, interaction, penta, family penta
2. **Track relationships** - who belongs to whose "constellation" (family, friends, exes)
3. **Group organization** - "Sandy's group" owned by first person, semantic naming like "Sandy's Heath (husband)"

### 64keys Terminology

Rebecca uses 64keys terminology (traditional Human Design in parentheses):
- **Initiator** (Manifestor) — ~8%
- **Builder** (Generator) — ~37%
- **Specialist** (Manifesting Generator) — ~33%
- **Coordinator** (Projector) — ~21%
- **Observer** (Reflector) — ~1%

Use 64keys terms in UI/documentation unless Rebecca explicitly requests traditional terms.

## Files and Directories

```
src/human_design/
├── api.py                  # 64keys.com API client
├── cli.py                  # Typer CLI application
├── calculate_utils.py      # Geocoding and ephemeris helpers
├── models/
│   ├── bodygraph.py        # RawBodyGraph, astronomical calculations
│   ├── coordinates.py      # CoordinateRange, LocalTime
│   ├── core.py             # Enums, type aliases (Planet, GateNumber)
│   ├── people.py           # Person, TagStore, RelationshipStore
│   └── summaries_64keys.py # 64keys-augmented models
├── web/
│   ├── app.py              # FastAPI web application (in flux)
│   └── templates/          # Jinja2 templates
└── bodygraph.yaml          # Gate definitions with zodiac ranges

src/mcp_server_64keys/      # MCP server for 64keys browsing
src/mcp_server_ra/          # MCP server for Ra transcription (in flux)
src/mcp_server_pdf/         # MCP server for PDF extraction

tests/                      # pytest test suite
cdk/                        # AWS CDK infrastructure (Batch, S3, ECR)
.devcontainer/              # Dev container configuration
```

## Environment Variables

**Required for 64keys API access:**
- `HD_USERNAME` - 64keys.com username
- `HD_PASSWORD` - 64keys.com password

**AWS (optional):**
- `SECRET_NAME` - AWS Secrets Manager secret for HD credentials
- `AWS_REGION` - AWS region (default: us-east-1)
- `DATA_BUCKET` - S3 bucket for web app data storage
- `USE_AWS_BATCH` - Set to "true" to use AWS Batch for transcription

## Working with This Codebase

- **Use the dev container** for all development work (ensures consistent environment)
- **Prefer editing existing files** over creating new ones
- **Models are in flux** - expect changes to data structures and capabilities
- **Keep raw calculations separate** from semantic interpretations
- **Use parametrized tests** to reduce duplication
- **Respect Rebecca Energy** - whimsical, warm, grounded tone in UI text
- **Consult `.github/copilot-instructions.md`** for Rebecca Energy philosophy and detailed context
