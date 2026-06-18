# Visual QA

Visual QA compares generated ODT/PDF output against user-approved fixture ODTs.

## One-off compare

```bash
 tools/tone9-render-current
 tools/tone9-compare-current-to-fixture \
   fixtures/live/2026-06-22-tone-iv-efsevios/outline.odt \
   out/current.odt \
   out/visual_compare/efsevios
```

## Manifest-wide generated fixture pass

```bash
 tools/tone9-generate-fixtures
```

This writes generated ODTs under:

```text
out/generated-fixtures/<fixture-id>/outline.odt
```

and writes a summary:

```text
out/generated-fixtures/generated_fixture_summary.md
```

## Manifest-wide visual regression

```bash
 tools/tone9-fixture-regression
```

This generates all manifest fixtures, compares them against the approved live
fixtures, and writes:

```text
out/fixture-regression/fixture_regression_summary.md
```

The command fails on invalid generated ODTs, applied bare `var-incipit`, or page
count mismatch. Non-zero visual deltas are expected until more structural slots
are implemented.
