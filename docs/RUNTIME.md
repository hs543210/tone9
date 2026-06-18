# tone9 runtime notes

## Deploy

```bash
cd ~/src/tone9
ansible-playbook -i inventory.ini playbooks/bootstrap-tone9-host.yml -K
ansible-playbook -i inventory.ini playbooks/deploy-tone9-runtime.yml -K
```

## Check rootless Podman

```bash
tools/tone9-podman-info
```

## Run Quadlet job

```bash
tools/tone9-run
```

## Inspect

```bash
tools/tone9-status
tools/tone9-journal
tools/tone9-metrics-cat
```

## Storage note

LibreOffice makes the container image large. On `pisa`, `/opt/tone9` is allowed
to be a symlink to `/home/tone9-state` so that rootless Podman storage has enough
space.
