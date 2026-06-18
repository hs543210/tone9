# Next batch plan

## Batch 010: first safe slot fill

Target only safe fields:

- `header.title`
- `header.tone_and_gospel`
- `header.service_rank_marker`
- `matins.gospel_cycle`

No row deletion. No table surgery. Render and compare after every change.

## Batch 011: service-sidecar driven generation

- Add `tone9 generate --service services/fixtures/...` support for nested
  `service.week_tone` overlays.
- Validate sidecar before selecting template.
- Write generation audit containing service ID, template, and slots changed.

## Batch 012: fixture visual regression runner

- Generate each fixture into `out/generated-fixtures/...`.
- Render generated and live fixture ODTs.
- Produce visual comparison reports.
- Fail on page-count mismatch.

## Batch 013: optional row/block prototype

Start with one low-risk omit/fill decision, probably Vespers readings or saint
Exapostilarion, after adding explicit slot anchors.
