# tone9 slot model

The ODT should remain the printable layout skeleton, but the generator should not
search for arbitrary prose. It should target stable slot IDs.

Batch 004 introduces `registries/slot_registry_v1.yaml` as the first vocabulary.
The immediate goal is not to replace the ODT template. The goal is to name the
places the generator will eventually fill, omit, or style.

Rule of thumb:

- visible style stays in ODT styles;
- service facts stay in sidecar YAML;
- tone/static liturgical text stays in registries;
- generator code applies slot policy.
