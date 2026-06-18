# Render and audit harness

Batch 005 separates render and audit logic into importable modules:

- `outline_gen.render`: LibreOffice PDF render, PDF page count, PDF-to-PNG pages.
- `outline_gen.audit`: ODT zip/XML checks.

The generator remains conservative: it still copies the selected boilerplate ODT,
but it now has a cleaner place to grow rendering, page-count, and visual QA logic.
