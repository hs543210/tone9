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

## Local Debian host bootstrap

```bash
cat > inventory.ini <<'EOF_INV'
[tone9]
localhost ansible_connection=local
EOF_INV

ansible-playbook -i inventory.ini playbooks/bootstrap-tone9-host.yml -K
ansible-playbook -i inventory.ini playbooks/deploy-tone9-runtime.yml -K
```

Check rootless Podman for the runtime user from an accessible directory:

```bash
TONE9_UID="$(id -u tone9)"
sudo -u tone9 \
  XDG_RUNTIME_DIR="/run/user/$TONE9_UID" \
  DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$TONE9_UID/bus" \
  sh -c 'cd /opt/tone9 && podman info'
```

Run the default Quadlet job:

```bash
TONE9_UID="$(id -u tone9)"
sudo -u tone9 \
  XDG_RUNTIME_DIR="/run/user/$TONE9_UID" \
  DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$TONE9_UID/bus" \
  systemctl --user start tone9-gen.service
```

Expected output:

- `/opt/tone9/out/current.odt`
- `/opt/tone9/out/current.pdf`
- `/opt/tone9/out/current.audit.md`
- `/opt/tone9/current/metrics/tone9.prom`

## Initial purpose

The first implementation intentionally does something simple and reliable: it selects the tone boilerplate ODT, copies it to the requested output path, optionally renders PDF, and writes an audit/metrics file. The generator logic can then grow slot-by-slot without losing the print-ready ODT workflow.
