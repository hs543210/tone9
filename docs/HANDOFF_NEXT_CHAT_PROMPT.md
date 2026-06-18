We are continuing work on tone9, a headless Orthodox weekly outline generator/runtime.

Current repo:
- git@github.com:hs543210/tone9.git
- latest known commit: 8ffd620 Add visual regression workflow, followed by any local handoff/schema batch if applied
- host: pisa
- working tree: ~/src/tone9
- runtime root: /opt/tone9
- on pisa, /opt/tone9 -> /home/tone9-state
- runtime user/group: tone9
- rootless Podman and Quadlet deploy are working

Current operational status:
- Ansible bootstrap/deploy works.
- Container image builds rootlessly as tone9.
- Quadlet units render and user systemd reloads.
- tools/tone9-fixture-smoke passes.
- python3 -m outline_gen.cli fixture-smoke passes.
- python3 -m pytest passes.
- tools/tone9-visual-compare can compare ODT/PDF render output against live fixtures.

Important docs:
- docs/HANDOFF_2026-06-18.md
- docs/ARCHITECTURE.md
- docs/RUNTIME.md
- docs/VISUAL_QA.md
- docs/SLOT_MODEL.md
- docs/EXTRACTION.md
- docs/RENDER_AUDIT.md
- docs/DONE_CRITERIA.md
- docs/NEXT_BATCH_PLAN.md
- docs/SLOT_FILL_PLAN.md

Important fixtures:
- fixtures/live/2026-06-08-tone-ii-theodorou: §1c six-stichira service
- fixtures/live/2026-06-22-tone-iv-efsevios: §1a simple service
- fixtures/live/2026-06-28-tone-iii-iona-polyeleos: §1d Polyeleos service

Important registries:
- registries/slot_registry_v1.yaml
- registries/live_fixture_manifest_v2.yaml
- registries/matins_gospel_cycle_v1.yaml
- registries/oktoichos_praises_doxastika_v1.yaml
- registries/service_shape_classifier_v1.yaml
- registries/service_overlay_schema_v1.yaml if the final handoff batch has been applied

Project doctrine:
- ODT owns print layout and visible styles.
- YAML registries own static facts and rules.
- reviewed service sidecars own per-service facts.
- Python owns extraction, slot policy, generation, render, audit.
- Quadlet/systemd owns runtime lifecycle, cgroups, journald, repeatability.
- Do not mutate ODT layout aggressively without visual regression.
- Do not solve fit by clipping incipits or dropping final words.
- Exact bare applied var-incipit style is forbidden; old style definitions alone are not failures.

Next milestone:
Implement first safe slot-fill generation pass. Target only:
- header.title
- header.tone_and_gospel
- header.service_rank_marker
- matins.gospel_cycle

Do not attempt row deletion yet. Use v8 boilerplate ODTs and reviewed service_overlay YAML fixtures. Validate sidecar first, generate ODT, render PDF, audit, and visually compare against live fixtures.
