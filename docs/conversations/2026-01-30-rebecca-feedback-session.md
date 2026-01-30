# Conversation: Rebecca Feedback Session

**Date:** January 30, 2026  
**Participants:** Rebecca Jolli (Jolly Alchemy), Nate (Developer)  
**Context:** First pass review of Humun Design Explorer web app  
**Main Topics:** UX ergonomics, data organization, relationship tracking, workflow optimization

---

## Key Insights

### 1. Name Organization Problem

Rebecca and her partner Cern enter names differently:
- Rebecca: First name first (e.g., "Sandy Johnson")
- Cern: Last name first (e.g., "Johnson, Sandy") — because of how 64keys displays stacked charts

**Pain Point:** When searching, Rebecca never knows if a person will be under first or last name. She has to mentally switch between formats depending on who entered the record.

**Possible Solution:** Normalize display to "First Last" format, but allow searching both ways.

---

### 2. Search Superiority

The DataTables search is already better than 64keys:
- 64keys requires exact capitalization
- 64keys sometimes needs the full name before matching
- Rebecca's workaround: She added "Sandy" to the names of all Sandy's family members, but 64keys search still doesn't find them

**Our search works!** Type "Sandy" and Sandy's family appears. This is a win.

---

### 3. Groups/Families Concept (Critical)

Rebecca's core organizational unit is the **family group** or **relational cluster**:

> "Every client that comes in is not just a single entry — they can be grouped by who their peeps are."

**The Pattern:**
- The **initial person** who comes to Rebecca "owns" the group
- Example: Sandy came first, so it's "Sandy's group" containing her husband Heath, her children, etc.
- If someone from the group emerges as important on their own, they can "graduate" to own their own group
- Example: Nate was "Bella's Nate" until recently upgraded to own "Nate's group"

**Semantic Meaning:**
- "Sandy's Heath" = Heath, accessed through Sandy's relational context
- The relationship matters: Heath is Sandy's *husband*
- Each person has relationships TO others (mom, husband, sister, ex, best friend)

---

### 4. Relationship Types

Common relationships Rebecca tracks:
- Parents (mom, dad)
- Natal family (siblings, grandparents)
- Partner/spouse (husband, wife, partner)
- Children
- Extended family (cousins, aunts, uncles)
- Best friends
- Exes (important conditioning influence!)
- Business relationships

**Data Structure Implication:** This is a **graph** — Person A has relationship R to Person B. Bidirectional in some cases (siblings), directional in others (parent→child).

---

### 5. Workflow: The Consultation Dance

When Rebecca is in a session with someone:

1. Client mentions their brother → Rebecca needs to pull up:
   - Brother's chart (solo)
   - Client + Brother interaction chart
   
2. Client mentions cousin Sue → Rebecca needs:
   - Cousin Sue's chart (solo)
   - Client + Cousin Sue interaction
   - Maybe Cousin Sue + Brother interaction
   
3. For family analysis → Penta chart (up to 5 people)

**Key Insight:** Rebecca is constantly pulling up **combinations** of charts during live sessions. Speed matters. She shouldn't have to search for each person individually.

**Desired Flow:**
1. Select a group (e.g., "Sandy family")
2. See all members listed
3. One-click to open any combo: 
   - Individual chart
   - Any 2-person interaction
   - Penta (3-5 people)
   - Full group multichart

---

### 6. 64keys Chart Types — DISCOVERED!

**Individual chart:** 
- `/chart?id=123` — Full overview
- `/type?id=123` — Type/Profile details
- `/activations?id=123` — Activations view
- `/aspects?id=123` — Potentials
- `/mission?id=123` — Mission/Purpose
- `/below?id=123` — Below the Line
- `/business?id=123` — Business view

**Transit (person + current planets):**
- `/transit?id1=123` — Transit overlay on person's chart

**Interaction (exactly 2 people):**
- `/interaction?id1=123&id2=456` — Two-person relationship chart

**Penta (3-5 people, team dynamics):**
- `/penta?id0=1&id1=2&id2=3&id3=4&id4=5&s0=a&s1=a&s2=a&s3=a&s4=a`
- Requires 3-5 people

**Family Penta (3-5 people, family dynamics):**
- `/familypenta?id0=1&id1=2&id2=3&id3=4&id4=5&s0=a&s1=a&s2=a&s3=a&s4=a`
- Same structure as team penta but different interpretation

**Multi-chart (2-16 people stacked):**
- `/multi_chart?id[0]=1&id[1]=2&id[2]=3...`
- Array-style parameters

**O16 (Organizational 16 channels, 1-100 people):**
- `/o16?ids=1,2,3,4,5` — Comma-separated IDs
- `/o16/lineup?ids=1,2,3,4,5` — Lineup view

**Cycle Returns:**
- `/cyclereturns?id1=123` — Saturn/Uranus returns

---

### 7. UI Feedback

**Chunky two-line display:** Rebecca finds the current layout a bit chunky. Birth date on its own line feels heavy.

**Date format win:** Showing month as word (e.g., "6 March 1968") eliminates the American vs. International date confusion. 64keys uses day/month/year which confuses American clients who give month/day/year.

**Count needed:** "How many people in this group?" — wants to see the count. (We added this!)

---

### 8. The "HD Group" Concept

Rebecca's idea for a special tag/category:
- When entering a new person, optionally assign them to an "HD Group"
- HD Group is not a single tag, but a **category of groups**
- Examples: "Sandy family", "Nate's people", "Workshop March 2025"
- These are first-class organizational units

---

### 9. Group Ownership Semantics

> "The initial one that comes to us owns the group."

- If Sandy comes in, Sandy owns "Sandy family"
- Heath (her husband) is IN "Sandy family" but doesn't own it
- Later, if Heath becomes a direct client, he might get his own group: "Heath's work team"
- A person can be IN multiple groups but typically OWNS at most one (their primary group)

---

## Rebecca's Philosophy (for Copilot Instructions)

### On Human Design Types

Rebecca uses 64keys terminology with traditional HD in parentheses:
- **Initiator** (Manifestor) — ~8%
- **Builder** (Generator) — ~37%  
- **Specialist** (Manifesting Generator) — ~33%
- **Coordinator** (Projector) — ~21%
- **Observer** (Reflector) — ~1%

### On Conditioning & Relationships

> "Everybody needs to have along with them their parents, their natal family, their best friend, all their exes."

Relationships are **conditioning influences**. Understanding someone's chart requires understanding the charts of people around them. This is why group organization matters so much.

### On the 7-Year Journey

Human Design is not a quick fix. It's a "7-year deconditioning experiment." The app should support long-term relationship with clients, not just one-off readings.

### On Accessibility

Rebecca recommends 64keys free accounts to clients. The tool should be affordable and accessible, not gatekept.

---

## Action Items

### Immediate
- [x] Fix type names (Coordinator, Specialist, etc.)
- [x] Rename "tags" to "groups"
- [x] Add group filtering with counts
- [x] Add "View Combined Chart" button

### Next Priority
- [ ] Discover 64keys interaction/penta endpoints
- [ ] Add relationship field (graph structure)
- [ ] Add group ownership (who "owns" each group)
- [ ] Quick-select UI for chart combinations

### Future
- [ ] Relationship visualization (graph view?)
- [ ] Session mode (quick chart switching during consultations)
- [ ] Streamlined data entry with relationship + group assignment

---

## Quotes to Remember

> "Every grand adventure begins with a single step — or perhaps a spirited leap into the unknown!"

> "It's such an important conditioning influence when you're looking at those things."

> "The initial one that comes to us owns the group."

> "When I'm talking with somebody and they mention their brother, I need to pull up a chart of you and your brother and a chart of your brother by himself."

---

## Technical Notes

- 64keys uses session-based filtering (discovered earlier)
- Multi-chart URL needs investigation
- Interaction charts may require specific endpoints
- Consider caching group definitions locally for speed
