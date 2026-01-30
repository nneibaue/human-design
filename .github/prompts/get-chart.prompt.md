You are helping users find and process data for specific people. Follow this workflow:

## 1. Search the Data File
- Reference the `people.yaml` file which contains person records with relevant information
- Search for a match by the provided identifier (name, partial name, or other info)
- Check for both exact and partial/fuzzy matches

## 2. If Person Found
- Display their complete record from the data file
- Confirm you found the right person
- Use their stored information (birth_date, birth_time, birth_location) to construct and run the CLI command
- **Extract location components**: Split "City, Country/State" into separate city and country/state

## 3. If Person Not Found
- Tell the user the person is not in the database
- Ask for the required information needed by the CLI command
  - Birth date in YYYY-MM-DD format (e.g., 1992-08-13)
  - Birth time in HH:MM format (e.g., 09:13)
  - Birth location as "City, Country/State" (e.g., "Albuquerque, United States")
- Validate the format before proceeding
- Run the CLI command with the provided information
- Optionally offer to add this person to `people.yaml` for future reference

## 4. CLI Command Format

The CLI bodygraph command has this syntax:
```bash
python -m human_design.cli bodygraph <date> <time> <city> <country/state>
```

### Parameters:
- `<date>`: Birth date in YYYY-MM-DD format
- `<time>`: Birth time in HH:MM format (24-hour)
- `<city>`: Birth city name
- `<country/state>`: Country or State name

### Flags:
- `--raw`: Output raw bodygraph (minimal data, fast)
  - Contains only calculated planetary positions and gate/line mappings
  - No enriched descriptions or interpretations from 64keys.com
  - Use this for lightweight data or performance
  
- Default (no flag): Output enriched bodygraph
  - Includes full 64keys.com content (descriptions, summaries, interpretations)
  - Richer, more readable output
  - Takes slightly longer to generate

### Output:
Both modes output JSON that can be redirected to a file:
```bash
# Save enriched bodygraph to file
python -m human_design.cli bodygraph 1990-11-27 08:49 Taipei Taiwan > bodygraph.json

# Save raw bodygraph to file
python -m human_design.cli bodygraph 1990-11-27 08:49 Taipei Taiwan --raw > bodygraph_raw.json
```

## 5. Example Interactions

### Scenario A: Person Found in people.yaml
```
User: "Calculate bodygraph for Jessica Peng"

→ Found in people.yaml:
   Name: Jessica Peng
   Birth Date: 1990-11-27
   Birth Time: 08:49
   Birth Location: Taipei City, Taiwan

→ Command (enriched, default):
   python -m human_design.cli bodygraph 1990-11-27 08:49 Taipei Taiwan
   
→ Command (raw data):
   python -m human_design.cli bodygraph 1990-11-27 08:49 Taipei Taiwan --raw

→ Execute and display results
→ Offer: "Would you like to save this, view raw data, or calculate for another person?"
```

### Scenario B: Person Not Found
```
User: "Calculate bodygraph for John Smith"

→ "John Smith is not in people.yaml. I'll need some information:
    - Birth date (YYYY-MM-DD format)?
    - Birth time (HH:MM format)?
    - Birth location (City, Country/State)?"

User: "1985-03-15, 14:30, New York, USA"

→ Construct command:
   python -m human_design.cli bodygraph 1985-03-15 14:30 New York USA
   
→ Execute and display results
→ Offer: "Would you like me to add John Smith to people.yaml for future reference?"
```

### Scenario C: Raw vs Enriched Comparison
```
User: "Show me both raw and enriched versions for Nate Neibauer"

→ Found in people.yaml: 1992-08-13, 09:13, Albuquerque, United States

→ Raw version (--raw flag):
   python -m human_design.cli bodygraph 1992-08-13 09:13 Albuquerque United --raw
   (Fast, minimal output - just gate/line mappings)

→ Enriched version (default):
   python -m human_design.cli bodygraph 1992-08-13 09:13 Albuquerque United
   (Includes full descriptions and interpretations)

→ Display both and highlight the differences
```

## 6. Key Implementation Notes
- Always parse birth_location from people.yaml by splitting on the comma: "City, Country/State"
- When constructing CLI arguments, use just the city name and country/state name separately
- The CLI expects 4 positional arguments: date, time, city, state/country
- Redirect output to file using `> filename.json` to save results
- All output is JSON formatted and can be parsed programmatically

