# Source extraction notes

Batch 003 adds deliberately conservative source extractors. They do not try to
produce a final outline directly. They extract reviewable facts from:

- rubrics HTML;
- liturgy HTML;
- Minaion ODT source text.

The first goal is to test the extractor against the three live source fixtures.
The generator should still prefer a reviewed service sidecar YAML over fully
automatic generation.
