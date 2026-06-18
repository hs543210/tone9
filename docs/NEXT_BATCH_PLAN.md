# Next batch plan

## Batch 010: first safe slot fill — done in patch batch

Implemented conservative service-sidecar driven fills for:

- `header.title`
- `header.tone_and_gospel`
- `header.service_rank_marker`
- `matins.gospel_cycle`

Guardrails now in place:

- `tone9 generate` validates the reviewed service overlay before writing ODT output.
- Slot fill is limited to known v8 boilerplate paragraphs/placeholders.
- Styles are preserved by replacing text nodes inside existing ODT XML spans.
- Generation audit records validation status plus exact slot changes.
- Tests cover all three reviewed fixture sidecars and invalid-service rejection.

Still intentionally not implemented:

- row deletion
- table surgery
- automatic incipit shortening
- arbitrary ODT text replacement outside known safe slots

## Batch 011: generated-fixture regression runner

- Add a runner that generates each `services/fixtures/*.yaml` sidecar into
  `out/generated-fixtures/<fixture>/outline.odt`.
- Optionally render generated ODTs to PDF/PNG.
- Compare generated fixture outputs against approved live fixtures.
- Keep comparison non-blocking at first except for ODT validity and page-count
  mismatch.

## Batch 012: first structural shape pass

Start with one low-risk omit/fill decision after explicit anchors and tests.
Likely candidates:

- simple-service Vespers readings omission; or
- saint Exapostilarion omission/fill.

Do not begin broad row deletion until the generated-fixture runner exists.
