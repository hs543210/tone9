# Slot fill plan

Do not treat ODT as arbitrary text. Treat it as a styled package with known slots.

## Implemented text slots

The generator fills stable text nodes in the v8 boilerplate ODTs:

- Header title
- Header Matins Gospel metadata
- Header ODS service-rank marker
- Matins Gospel cycle lines:
  - Gospel line incipit
  - Exapostilaria Gospel number
  - Resurrection Exapostilarion
  - Exapostilarion Theotokion
  - Evangelical Sticheron number and incipit

## Implemented structural slots

- `vespers.readings: omit` removes the Vespers 3 Readings placeholder paragraph.

This first structural pass is deliberately explicit-only. It does not yet infer
row/block omission from general shape-rule facts.

## Current guardrails

- Validate service sidecar first.
- Replace or remove only known slot text in known boilerplate paragraphs.
- Preserve existing styles by mutating XML text nodes, not by rebuilding layout.
- Record all slot changes in the generated audit.
- Generate all fixtures through `tools/tone9-generate-fixtures`.
- Compare all generated fixtures through `tools/tone9-fixture-regression`.
- Fail fixture regression on page-count mismatch.

## Still not automatic

- broad row deletion
- table surgery framework
- automatic incipit shortening
- cross-page layout changes
- shape-rule inference without explicit slot override
- silent fallback when a known slot anchor is missing

## Fixture-model expansion notes

The Peter/Paul Sunday major-feast merge establishes an important boundary:
source rubrics may contain larger canon arithmetic, but the generator must not
translate that arithmetic directly into printed Kanon rows. The reviewed service
sidecar and its `local_practice` / `print_profile` sections define the printed
compact form.

The header rank marker can now be intentionally blank for
`service_shape: sunday_major_feast_merge` with
`rank_marker_policy: blank_for_major_sunday_feast_merge`. This is a deliberate
print decision, not a missing field.
