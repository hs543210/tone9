# Render and audit harness

Batch 005 separated render and audit logic into importable modules:

- `outline_gen.render`: LibreOffice PDF render, PDF page count, PDF-to-PNG pages.
- `outline_gen.audit`: ODT zip/XML checks.

Batch 007 corrected the `bare_var_incipit_count` rule: the audit now counts only
applied text style references in `content.xml`, not harmless style definitions in
`styles.xml`. The project rule is that visible text should not use exact bare
`var-incipit`; retaining an old named style definition is not itself a failure.
