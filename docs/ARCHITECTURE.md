# tone9 architecture

`t9` is a headless Orthodox weekly outline generator.

## Design split

- **ODT** owns print layout and visible styles.
- **YAML registries** own stable liturgical/static facts and rules.
- **Service sidecars** own per-service reviewed facts.
- **Python CLI** owns extraction, slot policy, generation, render, and audit.
- **Quadlet/systemd** owns runtime lifecycle, cgroups, journald, and repeatability.

## Current implementation phase

The current generator deliberately begins as a safe copy-based tool: it chooses a
Tone I-VIII boilerplate and copies it to the output path. This keeps the
printable ODT workflow intact while the slot model and extraction code mature.

## Target generation flow

```text
rubrics/liturgy/minaion sources
        ↓
extractor facts
        ↓
reviewed service YAML
        ↓
slot policy + registries
        ↓
ODT output
        ↓
PDF + PNG review + audit + metrics
```

## Runtime shape

```text
/opt/tone9 -> /home/tone9-state   # acceptable on pisa to keep storage off /
/opt/tone9/home                   # tone9 user home + rootless Podman storage
/opt/tone9/current                # deployed source snapshot
/opt/tone9/out                    # generated ODT/PDF/audit
/opt/tone9/data                   # cache + LibreOffice profile
/opt/tone9/current/metrics        # Prometheus textfile metrics
```

Keep `~/src/tone9` owned by the human developer and `/opt/tone9` owned by the
`tone9` runtime user.
