# tone9

`tone9` is a headless Orthodox weekly outline generator/runtime.

It is intended to run as a normal CLI during development and as a rootless Podman/Quadlet job under systemd in production-like use.

## Runtime naming

- repo/tool: `tone9`
- Linux user/group: `tone9`
- state root: `/opt/tone9`
- runtime home: `/opt/tone9/home`
- active runtime tree: `/opt/tone9/current`
- generated outlines: `/opt/tone9/out`
- Quadlets: `tone9-*.container`
- systemd target: `tone9.target`

## Quick local smoke

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
tone9 generate --service services/examples/2026-06-08-tone-ii.yaml --out out/current.odt --audit
```

With LibreOffice installed:

```bash
tone9 generate --service services/examples/2026-06-08-tone-ii.yaml --out out/current.odt --pdf --audit
```

## Initial purpose

The first implementation intentionally does something simple and reliable: it selects the tone boilerplate ODT, copies it to the requested output path, optionally renders PDF, and writes an audit/metrics file. The generator logic can then grow slot-by-slot without losing the print-ready ODT workflow.
