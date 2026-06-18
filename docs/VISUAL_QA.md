# Visual QA and regression workflow

The reliable tone9 layout workflow is render-first:

```text
ODT -> PDF -> PNG pages -> image/contact-sheet review -> report
```

Batch 008 adds a visual comparison helper that can compare either ODT or PDF
inputs. For ODT input, it renders both documents with LibreOffice first. Then it
renders the PDFs to PNG pages and creates:

- `visual_compare_report.md`
- `visual_compare_report.json`
- `contact_sheet_expected_actual_diff.png`
- per-page diff PNGs under `diff_png/`

## Compare two ODTs

```bash
tools/tone9-visual-compare \
  --expected fixtures/live/2026-06-22-tone-iv-efsevios/outline.odt \
  --actual out/current.odt \
  --outdir out/visual_compare/efsevios
```

## Compare current output to a fixture

```bash
tools/tone9-compare-current-to-fixture \
  fixtures/live/2026-06-22-tone-iv-efsevios/outline.odt \
  out/current.odt \
  out/visual_compare/efsevios
```

## How to interpret results

- Page count mismatch is a hard failure.
- Very small pixel changes may be antialiasing/render noise.
- Large bounding boxes or high changed-percent values usually mean layout drift.
- The contact sheet is intended for quick visual review: expected, actual, diff.

Use this workflow before accepting any slot-fill or row-omit change that touches
ODT layout.
