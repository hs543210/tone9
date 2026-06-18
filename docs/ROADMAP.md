# tone9 roadmap

`t9` should stay operationally simple: a headless CLI wrapped by rootless
Podman/Quadlet, producing ODT/PDF/audit/metrics artifacts under `/opt/tone9`.

## Current state

- Python CLI exists and can copy the correct tone boilerplate by service YAML.
- Container image builds with LibreOffice and rendering tools.
- Rootless `tone9` user and Quadlets deploy under systemd.
- Prometheus textfile metrics are emitted for generator runs.
- v8 Tone I-VIII boilerplates are present.

## Batch 002: fixtures and registries

Import the first reliable working data from the chat:

- live outline fixtures for §1a, §1c, and §1d service shapes;
- source rubrics/liturgy/Minaion fixtures;
- Matins Gospel cycle registry;
- Oktoichos Praises Doxastika registry;
- service-shape classifier;
- manual-edit authority manifest.

## Batch 003: extractor skeleton

Add parsers for source fixtures:

- rubrics HTML extraction;
- liturgy HTML extraction;
- Minaion ODT text extraction;
- pytest checks that the three fixture services produce expected shape facts.

## Batch 004: slot model

Move from copy-only generation to slot-aware generation:

- stable slot IDs;
- include/omit rules;
- field replacement rules;
- style-aware count rendering.

## Batch 005: render and audit harness

Turn visual QA into a repeatable command:

- render ODT to PDF headlessly;
- render PDF to PNG/contact sheet;
- check page count;
- check no exact bare `var-incipit`;
- check required fixture strings;
- write Prometheus textfile metrics.

## Batch 006: runtime polish

Make Quadlet/systemd operation first-class:

- optional timer units;
- better journal/status tools;
- systemd unit metrics;
- deploy/run smoke checks.
