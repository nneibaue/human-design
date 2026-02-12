# Memory Academy: Deployment Complete ✅

## Live API Endpoints

The Memory Academy gates learning system is now live at:
**https://lxmkhc0y2c.execute-api.us-east-1.amazonaws.com**

### Public Endpoints (No Auth Required)

#### GET `/api/gates`
Returns all 64 gates with metadata (names, centers, partners, channels, circuits, difficulty, memory hooks).
```bash
curl https://lxmkhc0y2c.execute-api.us-east-1.amazonaws.com/api/gates | jq '.gates | length'
# Output: 64
```

#### GET `/api/gates/{gate_number}`
Returns detailed information for a specific gate.
```bash
curl https://lxmkhc0y2c.execute-api.us-east-1.amazonaws.com/api/gates/1 | jq '.'
# Output: Gate 1 data with memory hook and partner connections
```

#### GET `/api/channels`
Returns all 36 channels with gate pairs, circuits, and memory hooks.
```bash
curl https://lxmkhc0y2c.execute-api.us-east-1.amazonaws.com/api/channels | jq '.channels | length'
# Output: 36
```

#### GET `/api/circuits`
Returns circuit group structure (Individual, Collective, Tribal).
```bash
curl https://lxmkhc0y2c.execute-api.us-east-1.amazonaws.com/api/circuits | jq '.circuit_groups'
```

#### GET `/api/confusables`
Returns confusable gate clusters for disambiguation study.
```bash
curl https://lxmkhc0y2c.execute-api.us-east-1.amazonaws.com/api/confusables | jq '.clusters | keys'
# Output: ["Commitment Gates", "Deep Thinking Gates", "Emotional Gates", "Power/Force Gates"]
```

### Authenticated Endpoints (Require Login)

#### GET `/gates`
Interactive flash card learning page with 4 minigame modes:
- **Flip Cards**: Reveal gate details and memory hooks
- **Quiz Gate→Channel**: Answer MCQ about which channel a gate connects to
- **Quiz Channel→Gates**: Answer MCQ about which gates form a channel
- **Spaced Repetition**: Review gates due for review based on confidence intervals

#### GET `/api/learning/progress`
Retrieve user's learning progress (requires session authentication).
```bash
curl -H "Cookie: session=..." https://lxmkhc0y2c.execute-api.us-east-1.amazonaws.com/api/learning/progress
```
Returns:
- `all_progress`: Dict mapping gate numbers to review stats
- `gates_due_for_review`: Array of gate numbers needing review
- `total_reviewed`: Count of gates reviewed
- `session_id`: Session identifier for data isolation

#### POST `/api/learning/progress`
Save quiz/flip card results to track learning progress (requires session authentication).
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"gate_number": 1, "result": "correct", "mode": "flip"}' \
  https://lxmkhc0y2c.execute-api.us-east-1.amazonaws.com/api/learning/progress
```

## Data Structure

### Gate Data (`src/human_design/gates_data.py`)
All 64 gates with dual naming (64keys + Ra terminology):
- Gate name and Ra name
- Center designation
- Partner gates (for channel connections)
- Channel names and circuits
- Difficulty rating (1-3 stars)
- Vivid memory hooks from "Memorize the 64 Gates" study guide

**Example: Gate 1 (Originality)**
```python
{
    "name_64keys": "Originality",
    "name_ra": "The Creative",
    "center": "Identity",
    "partner_gates": [8],
    "channel_names": ["Inspiration"],
    "circuits": ["Individual Knowing"],
    "difficulty": 2,
    "memory_hook": "Gate 1 (Originality) is a painter alone in a studio, brush flying..."
}
```

### Channel Data
All 36 channels with gate pairs and circuits:
- Channel name (64keys terminology)
- Gate pair numbers
- Circuit classification (Individual Knowing, Collective Sensing, Tribal Ego, etc.)
- Memory hooks explaining the channel's meaning

### Confusable Clusters
4 groups of gates that are easily confused during learning:
1. **Deep Thinking Gates** (24, 47, 43, 61, 64)
2. **Commitment Gates** (29, 46, 40, 32)
3. **Emotional Gates** (30, 22, 36, 55, 58)
4. **Power/Force Gates** (34, 51, 21, 28, 38)

## Learning Progress Storage

### Session Isolation
Each user gets a unique `session_id` (UUID) stored in a session cookie. This isolates learning progress:
- No user authentication required (uses anonymous sessions)
- Multiple browsers/devices = multiple independent progress tracks
- Session data never mixed between users

### Storage Backend
- **Production (S3)**: `learning/{session_id}/progress.json` in the app data bucket
- **Development (Local)**: `data/learning/{session_id}/progress.json`

### Progress Data Format
```json
{
  "1": {
    "confidence": 0.8,
    "review_count": 5,
    "correct_count": 4,
    "last_reviewed": "2026-02-08T00:15:30.123456",
    "attempts": [
      {
        "timestamp": "2026-02-07T23:45:10",
        "result": "correct",
        "mode": "flip"
      },
      ...
    ]
  },
  ...
}
```

## Frontend Features

### Flash Card UI (gates.html)
- CSS 3D flip animation with back showing:
  - Partner gates
  - Channel names
  - Circuit classification
  - Difficulty rating (stars)
  - Memory hooks for memorization

- Progress sidebar with:
  - Overall completion percentage
  - Average confidence score
  - Gates due for review
  - 64-gate confidence grid (color-coded: not reviewed / needs work / getting there / confident)

### Quiz Modes
- **MCQ Format**: 4 options with correct/incorrect feedback
- **Memory Reinforcement**: Shows memory hook after answering
- **Adaptive Difficulty**: Spaced repetition prioritizes low-confidence gates

### Spaced Repetition Algorithm
Simple confidence-based intervals:
```
Interval = max(1 day, confidence × 3 days)
```
Example:
- Confidence 0.2 → review after 1 day
- Confidence 0.5 → review after 1.5 days
- Confidence 1.0 → review after 3 days

### Keyboard Shortcuts
- `←` / `→` : Previous/Next gate
- `Space` / `Enter` : Flip card
- `g` : Mark as "Got it!"
- `w` : Mark as "Needs work"

## Design System

Matches existing Jolly Alchemy Labs design:
- **Colors**: Deep purple (#4a2c6a), golden amber (#d4a853), soft purple (#9d7bb5)
- **Fonts**: Cormorant Garamond (headings), Quicksand (body)
- **Animations**: 3D flip, progress bar transitions, hover effects
- **Responsive**: Mobile-optimized grid layouts

## Testing & Verification

All 132 existing unit tests pass. Data integrity verified:
- ✅ All 64 gates present
- ✅ All 36 channels present
- ✅ Partner gate symmetry (if A→B, then B→A)
- ✅ All gates referenced in at least one channel
- ✅ Gate partner relationships match `bodygraph.yaml`
- ✅ API endpoints accessible and returning correct data structure

## Files Created/Modified

### Created
- `src/human_design/gates_data.py` (800+ lines) — All gate, channel, circuit, and confusable data
- `src/human_design/web/templates/gates.html` (800+ lines) — Interactive flash card page

### Modified
- `src/human_design/web/app.py` — 8 new routes for gates and learning progress APIs
- `src/human_design/web/templates/index.html` — Added "Memory Academy" nav link

## Architecture Decisions

### Session-Based Learning Progress (Not User Accounts)
Benefits:
- No login/registration required for learning
- Can add traditional user auth later without breaking existing data
- Multiple sessions per user possible (home, work, mobile)
- Fully backward compatible with existing app

### Dual Naming (64keys + Ra)
All gates and centers stored with both naming systems:
- Frontend toggleable (future feature: "Use Ra Terminology")
- All memory hooks adapt to selected system
- Enables multi-tradition learning

### Simple Spaced Repetition (Not SM2 Algorithm)
MVP approach: confidence-based intervals rather than complex SM-2
- Easy to understand and debug
- Can upgrade to SM-2 later if needed
- Sufficient for initial learning phase

### Memory Hooks from Revised Study Guide
All 36 channel memory hooks sourced from "Memorize the 64 Gates, Revised Edition":
- Vivid, bizarre, sensory-rich imagery
- Generator Effect: users' own hooks will stick better
- Self-generation prompts provided in guide

## Next Steps (Future Enhancements)

1. **Dual Terminology UI**: Add toggle for Ra vs 64keys terminology
2. **SM-2 Algorithm**: Implement proper spaced repetition scheduling
3. **User Accounts**: Add login system while preserving anonymous sessions
4. **Memory Palace**: Interactive visual guide through 9 centers
5. **Progress Export**: PDF certificate or progress report
6. **Mobile Optimization**: Swipe gestures for flip cards
7. **Audio**: Pronunciation of gate and channel names
8. **Real Chart Integration**: Show which gates appear in user's birth chart

## Deployment Details

- **Runtime**: Python 3.14 (bookworm base)
- **Framework**: FastAPI + Starlette sessions
- **Deployment**: AWS Lambda + API Gateway
- **Storage**: S3 for learning progress data
- **Session Management**: HTTP-only cookies via Starlette middleware

Deploy command: `make redeploy` (builds Docker image + deploys to AWS)

---

**Status**: ✅ Live and tested
**Launch Date**: 2026-02-07
**API Version**: 1.0
