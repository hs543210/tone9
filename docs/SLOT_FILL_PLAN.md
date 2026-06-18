# Slot fill plan

Do not treat ODT as arbitrary text. Treat it as a styled package with known slots.

## Implemented safe first slots

The first generator pass fills only stable text nodes in the v8 boilerplate ODTs:

- Header title
- Header Matins Gospel metadata
- Header ODS service-rank marker
- Matins Gospel cycle lines:
  - Gospel line incipit
  - Exapostilaria Gospel number
  - Resurrection Exapostilarion
  - Exapostilarion Theotokion
  - Evangelical Sticheron number and incipit

## Current guardrails

- Validate service sidecar first.
- Replace only known slot text in known boilerplate paragraphs.
- Preserve existing styles by mutating XML text nodes, not by rebuilding layout.
- Audit applied output after mutation.
- Record all slot changes in the generated audit.
- Render to PDF via existing `--pdf` flow.
- Compare against fixture when a fixture exists.

## Still not first

- Row deletion
- Table surgery
- automatic incipit shortening
- cross-page layout changes
- silent fallback when a known slot anchor is missing
