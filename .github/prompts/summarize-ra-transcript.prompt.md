## Summarize Ra Uru Hu Transcript

You are summarizing a Ra Uru Hu lecture transcript for indexing and retrieval. Your output will be added to `ra_transcripts/index.json` to enable `/ask-ra` to find and reference this content.

---

## Input

You will receive a `.txt` transcript file containing:
- Timestamp markers like `[1.14s -> 5.22s]`
- Raw transcribed text (possibly with some transcription errors)
- Multiple segments from a single lecture track

---

## Your Task

Extract and format the following information:

### 1. Topic Summary (2-3 sentences)

Concise description of what Ra teaches in this track. Should answer: "What is this about?"

**Example:**
> "Venus represents the principle of morality and 'rightness' in your design. Ra explores how Venus shows us what feels intrinsically correct or incorrect based on our conditioning and design, using Monica Seles' chart to demonstrate how Venus manifests in the body."

### 2. Keywords (10-15 terms)

Key terms for BM25 full-text indexing. Include:
- Main topics (e.g., "venus", "morality")
- Concepts mentioned (e.g., "conditioning", "rightness")
- Related mechanics (e.g., "defined", "undefined")
- Technical HD terms used (e.g., "gates", "channels")
- **Do NOT** include common words like "the", "is", "and"

**Example keywords:**
```json
["venus", "morality", "mores", "rightness", "correctness", "conditioning", "yin", "female power", "definition", "undefined", "design"]
```

### 3. Example Persons/Charts Mentioned

List any actual people whose charts Ra uses as examples in this track. Include their name and relationship to the teaching.

**Example:**
```json
["Monica Seles (case study throughout series for planetary mechanics)"]
```

### 4. Key Concepts/Teachings (bulleted list)

What core ideas or principles does Ra teach here? What should a learner take away?

**Example:**
- Venus is about intrinsic rightness—what feels morally or ethically correct
- Conditioning heavily influences our Venus expression
- Undefined Venus means you're susceptible to others' definitions of "right" and "wrong"
- The difference between yin (receptive) and the patriarchal repression of female power

### 5. Notable Quotes (optional, 1-2)

If there's a particularly impactful or quotable statement from Ra, include it. This helps preserve his voice.

**Example:**
> "The Romans and the Greeks were sexist. They were patriarchs. They were not interested in exalting the nature of what it is to be female or yin, and they were deeply terrified of female power."

---

## Output Format

Provide your response in this JSON structure so it can be manually copied into `ra_transcripts/index.json`:

```json
{
  "track_entry": {
    "number": 3,
    "file": "3",
    "topic": "Venus - morality, mores, relationships",
    "keywords": ["venus", "morality", "mores", "rightness", "conditioning", "yin", "female power"],
    "duration_seconds": 246,
    "example_persons": ["Monica Seles"],
    "transcribed": true
  },
  "summary": {
    "topic_summary": "Venus represents the principle of morality and intrinsic rightness in your design...",
    "key_concepts": [
      "Venus shows us what feels correct or incorrect based on our design",
      "Conditioning heavily influences Venus expression",
      "Undefined Venus = susceptible to others' definitions"
    ],
    "notable_quote": "The Romans and the Greeks were sexist..."
  }
}
```

---

## Instructions for Integration

1. **File Preparation**: User provides path to `.txt` transcript (e.g., `ra_transcripts/21.txt`)
2. **Your Analysis**: You summarize using this prompt
3. **Manual Update**: User copies the `track_entry` JSON and appends to `ra_transcripts/index.json` in the appropriate series' `tracks` array
4. **Verification**: Verify that:
   - Keywords are accurate and useful for BM25 search
   - Key concepts capture Ra's core teaching
   - Example persons are correctly attributed
   - Duration matches the file's actual length (extract from JSON if available)

---

## Special Notes

- **Preserve Ra's voice**: Use his terminology and phrasing in the topic summary and key concepts
- **Technical accuracy**: Verify Human Design terms are correct (gates, channels, types, authorities)
- **Context matters**: If this track references earlier tracks in the series, note the connection
- **Transcription quality**: If the transcript has obvious errors or unclear segments, note that in a comment but do your best with the available text
- **Series consistency**: Maintain consistency with other tracks in the same series (e.g., Monica Seles is the recurring example in Planetary Imprint)

---

## Ready to Summarize

Provide the transcript file content or path, and I will generate the summary in the format above.
