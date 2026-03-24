# /implement

Implement features using test-driven development with embedded multi-agent system.

## Usage

```bash
/implement <feature_description>
```

**Examples**:
```bash
/implement bodygraph caching layer
/implement composite chart calculation
/implement transit overlay visualization
/implement --tdd --agents implementer,test_engineer,d3_specialist
```

## How It Works

1. **Feature Specification**: Parse user request to understand feature requirements
2. **Agent Composition**: Use `implementer` + `test_engineer` for TDD workflow
3. **Strand Execution**: Agents work in sequence:
   - `implementer`: Designs and implements feature
   - `test_engineer`: Creates comprehensive test suite
4. **Results**: Working code + tests ready for review

## Default Agent Composition

```python
agents = ["implementer", "test_engineer"]
```

**implementer**: Feature implementation with tool integration
**test_engineer**: Test suite creation and validation

For visualization features, add `d3_specialist`:
```python
agents = ["d3_specialist", "implementer", "test_engineer"]
```

## Options

- `--agents <list>` - Override default agents (comma-separated)
- `--tdd` - Enable strict TDD workflow (tests first)
- `--type <type>` - Implementation type (feature, refactor, fix)

## Example Output

```
🚀 Implementing: bodygraph caching layer

📐 Design Phase (implementer):
  - Location: src/human_design/cache/bodygraph_cache.py
  - Strategy: LRU cache with TTL support
  - Dependencies: functools.lru_cache, datetime

🔨 Implementation Phase (implementer):
  ✓ Created BodygraphCache class
  ✓ Added get/set/invalidate methods
  ✓ Integrated with RawBodyGraph calculation

✅ Testing Phase (test_engineer):
  ✓ Created tests/test_bodygraph_cache.py
  ✓ Tests: cache_hit, cache_miss, cache_expiry, cache_invalidation
  ✓ Coverage: 95%

📁 Files Generated:
  - src/human_design/cache/bodygraph_cache.py (NEW)
  - tests/test_bodygraph_cache.py (NEW)
  - strand-results/active/IMPLEMENTATION_SUMMARY.md

✅ Implementation complete. Run tests? [Y/n]
```

## Implementation

Uses embedded DODO-Lite system:

```python
from human_design.strands import create_strand

strand = create_strand(
    problem=f"Implement {feature_description}",
    agents=["implementer", "test_engineer"],
    strand_type="implementation",
    context={"tdd": True}
)

result = await strand.run()
```

## TDD Workflow

When `--tdd` flag is used, agents work in strict TDD order:

1. **test_engineer** writes failing tests first
2. **implementer** implements feature to pass tests
3. **test_engineer** validates and adds edge cases

## See Also

- `/refine` - Refine existing code
- `/visualize` - Create D3 visualizations
- `src/human_design/strands/` - DODO-Lite implementation
