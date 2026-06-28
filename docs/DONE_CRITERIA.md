# What done looks like for tone9

`t9` is done enough when it reliably turns reviewed service facts into a
print-ready compact Orthodox weekly outline without manual reconstruction.

## MVP done

- Runtime deploy works.
- Fixture smoke passes.
- Pytest passes.
- The three live fixtures validate.
- The generator fills safe header/Gospel/rank slots from reviewed sidecars.
- Generated ODTs render to PDF.
- Visual regression reports are produced.

## Useful weekly-tool done

- §1a, §1c, and §1d service shapes generate from reviewed sidecars.
- Optional rows/blocks work: Readings, Psalm 118, Polyeleos, saint sessionals,
  saint Exapostilarion, stichoi for 7&8, split Hours, second Liturgy rows.
- Counts and singular/plural labels are correct.
- Approved two-page shape is preserved unless explicitly reviewed.

## Mature done

- Source extractors prefill service overlays with confidence/evidence.
- Human review happens in YAML, not by reconstructing ODT layout.
- Fixture corpus grows without destabilizing old services.
- Rendering, visual comparison, audit, and metrics are routine.

## Fixture-model done

- The corpus includes ordinary Sunday, six-stichira, Polyeleos, and Sunday +
  major-feast merge profiles.
- A service may intentionally render with a blank ODS/rank marker when local
  practice says the Sunday/major-feast merge should not be classified as §1e or
  §1f2.
- Source rubrics are not automatically the printed outline; local compact
  practice controls printed Kanon total and rank marker.
- Printed Kanon totals remain compact unless the reviewed service sidecar
  explicitly changes the print profile.

## Peter/Paul fixture-model done criteria

Peter/Paul is not done merely because the header renders. It becomes a useful
fixture when:

- reviewed body slot fills compile into ODT without bare `var-incipit` failures;
- compact Kanon stays at six and uses the reviewed multi-saint allocation;
- paired liturgy fields render visibly where the boilerplate has safe anchors;
- a manually approved live `outline.odt` is added to visual regression;
- fit/page-count changes are reviewed visually rather than solved by clipping
  text or silently omitting required lines.
