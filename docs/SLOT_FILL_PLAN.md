# Slot fill plan

Do not treat ODT as arbitrary text. Treat it as a styled package with known slots.

## Safe first slots

- Header title
- Tone line / Matins Gospel metadata
- ODS rank marker
- Matins Gospel cycle incipits

## Required guardrails

- Validate service sidecar first.
- Replace only known slot text.
- Preserve existing styles.
- Audit applied styles after mutation.
- Render to PDF.
- Compare against fixture when a fixture exists.

## Not first

- Row deletion
- Table surgery
- automatic incipit shortening
- cross-page layout changes
