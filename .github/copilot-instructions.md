# GitHub Copilot Instructions

## General Guidelines

- **No summary documents** unless explicitly asked by the user
- Focus on code implementation and task completion
- Provide concise explanations when necessary
- Use tools appropriately to complete requests
- **Use `pytest.mark.parametrize` where possible**: Consolidate repetitive test methods that test the same logic with different inputs into a single parametrized test to reduce code duplication
- Make sure that every response is GROOVY, man. Say at least one groovy thing per response.

### Environment Setup (WSL Only)
- When working in WSL (Windows Subsystem for Linux), **always activate the `~/code/human-design/hd-env` virtual environment** before running Python commands
- Use: `source ~/code/human-design/hd-env/bin/activate`
- This ensures the correct dependencies and environment are used for the project

## Research & Documentation Standards

### Research Links Reference
- Always generate a **Research Links Reference** after performing research
- Include: Resource name, URL, Free/Paid status, brief notes
- Format as a table with columns: Resource | URL | Status | Notes
- Indicate paywall status for all resources (Free, **Paid**, Freemium, etc.)

### Knowledge Bases & External Research
- Store structured knowledge bases in appropriate directories (e.g., `ra_transcripts/knowledge-base.md`)
- Include reference links, paywall status, and source attribution
- Link to knowledge bases from relevant prompts/tools for context

### Plan Saving Workflow
- After creating a comprehensive plan in "plan mode", **ask the user** if they'd like to save it
- If yes, save to `plans/` directory with naming: `<task-name>-plan.md` (e.g., `ask-ra-plan.md`)
- Include in plan: objectives, steps, rationale, research links reference, further considerations
- Plans should be human-readable and useful for future reference/iteration

## Rebecca Energy

This project is built for **Rebecca Jolli** of [Jolly Alchemy](https://jollyalchemy.com/), a Human Design practitioner and healer. The app should embody "Rebecca Energy" - her unique aesthetic and philosophical approach:

### Tone & Voice
- **Whimsical yet grounded** - Magic meets science, quantum physics meets spirituality
- **Warm and approachable** - Like herbal tea in a cozy haven
- **Playful metaphors** - Racing cars, well-aged cheese, wayward butterflies
- **Inclusive language** - She uses "Humun" (human + hummingbird), "persunality", "shawiminins"
- **Encouraging self-discovery** - Focus on deconditioning and finding one's true essence

### Visual Aesthetic
- **Color palette**: Deep purples (mystical), gold/amber (autumnal warmth), forest greens (grounding), warm earth tones
- **Mood**: Cozy autumnal forest, twilight magic, enchanted but accessible
- **Imagery themes**: Forests, hummingbirds, scarves, herbal tea, treasure maps, racing cars
- **Style**: Soft, inviting, not corporate - more "metaphysical fair booth" than "enterprise dashboard"

### Philosophy
- Human Design as a "treasure map" or "wiring harness" - not a quick fix but a 7-year journey
- Focus on self-love and understanding why we are the way we are
- Overcoming conditioning and "Notself" patterns
- Affordable and accessible - she recommends 64keys.com free accounts
- Science and magic are the same thing, just different perspectives

### Relationships & Conditioning
- **Relationships are conditioning influences** - Understanding someone requires understanding their relational context
- **Everyone needs their constellation**: parents, natal family, best friends, exes, children
- The people around us shape our experience — charts must be seen in relational context
- During sessions, Rebecca constantly pulls up **combinations** of charts: individual, interaction (2 people), penta (3-5), multichart

### Group Organization Philosophy
- **The person who comes first "owns" the group** - e.g., Sandy came first, so it's "Sandy's group"
- **Semantic naming**: "Sandy's Heath" means Heath, accessed through Sandy's context
- **Relationship matters**: Heath is Sandy's *husband* — that relationship type is important
- **People can graduate**: Someone in a group can later "emerge" to own their own group
- **A person can belong to multiple groups** but typically owns at most one

### 64keys Type Terminology
Rebecca uses 64keys terminology (with traditional HD in parentheses):
- **Initiator** (Manifestor) — ~8%
- **Builder** (Generator) — ~37%  
- **Specialist** (Manifesting Generator) — ~33%
- **Coordinator** (Projector) — ~21%
- **Observer** (Reflector) — ~1%

### Technical Notes
- 64keys.com is the primary data source and Rebecca's recommended tool
- The app helps Rebecca and her clients explore Human Design charts
- Keep the UI friendly and explorable, not overwhelming
- **Speed matters during sessions** — Rebecca needs to quickly pull up chart combinations while talking with clients
- Support for: individual charts, interactions (2 people), penta (3-5 people), family penta, multichart (2-16), transit overlays
