# Next batch plan

## Batch 010: first safe slot fill — done

Implemented conservative service-sidecar driven fills for:

- `header.title`
- `header.tone_and_gospel`
- `header.service_rank_marker`
- `matins.gospel_cycle`

## Batch 011: generated-fixture runner — done

Implemented:

- `tone9 generate-fixtures`
- `tools/tone9-generate-fixtures`
- manifest-driven generation into `out/generated-fixtures/<fixture>/outline.odt`
- `out/generated-fixtures/generated_fixture_summary.md`

The runner validates each reviewed sidecar through the normal `tone9 generate` path.

## Batch 012: fixture visual regression runner — done

Implemented:

- `tone9 fixture-regression`
- `tools/tone9-fixture-regression`
- generation of all manifest fixtures before compare
- visual compare of generated ODTs against approved live ODT fixtures
- `out/fixture-regression/fixture_regression_summary.md`
- failure on ODT/audit failure or page-count mismatch

The visual delta is expected to remain non-zero until structural slots are filled.

## Batch 013: first structural shape pass — done

Implemented one explicit low-risk structural omission:

- `vespers.readings: omit` removes the Vespers 3 Readings placeholder paragraph.

This is intentionally explicit-only. It does not yet infer omission from
`shape_rules_exercised.vespers.readings: 0`.

## Next recommended batch: structural shape pass 2

Candidate targets, in order:

1. simple-service saint Exapostilarion omission;
2. simple-service combined Glory/Now Dogmatic line;
3. singular/plural Liturgy labels;
4. Theodorou explicit Vespers readings omission, after adding/confirming a slot
   override.

Avoid broad table surgery until each omission/fill has a dedicated anchor and a
fixture test.

## Batch 014: Peter and Paul fixture model — done

Implemented model/schema/extractor support for:

- `2026-06-29-tone-v-peter-paul`
- `service_shape: sunday_major_feast_merge`
- blank header rank marker by local practice
- compact printed Kanon total 6 despite larger source canon arithmetic
- multi-saint compact Kanon allocation: Resurrection 1, Theotokos 1, Peter 2,
  Paul 2
- Liturgy Beatitudes on 12 with Octoechos 4, Peter 4, Paul 4
- paired Prokeimena, Alleluiaria, Epistles, Gospels, and Communion stichoi

This remains a fixture/model/extractor expansion only. The new Peter/Paul
service is not added to the live visual-regression manifest until its live
`outline.odt` is manually approved.

## Next recommended batch: Peter/Paul generation prep

Candidate targets:

1. add a candidate-fixture runner that can generate non-live services without
   requiring a user-approved `outline.odt`;
2. fill safe Kanon allocation rows from reviewed sidecar data;
3. fill paired Liturgy labels/refs from reviewed sidecar data;
4. only then add Peter/Paul to visual regression after manual outline approval.
