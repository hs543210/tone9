from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import yaml

from .audit import audit_odt, write_markdown_audit
from .render import pdf_page_count, render_pdf, render_png_pages
from .service_schema import validate_service_overlay
from .slot_fill import fill_safe_slots

TONE_NAMES = {
    "I": "I", "1": "I",
    "II": "II", "2": "II",
    "III": "III", "3": "III",
    "IV": "IV", "4": "IV",
    "V": "V", "5": "V",
    "VI": "VI", "6": "VI",
    "VII": "VII", "7": "VII",
    "VIII": "VIII", "8": "VIII",
}


def load_yaml(path: Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"YAML file is not a mapping: {path}")
    return data


def service_tone(service: dict) -> object:
    if "tone" in service:
        return service.get("tone")
    if "week_tone" in service:
        return service.get("week_tone")
    nested = service.get("service")
    if isinstance(nested, dict):
        return nested.get("tone") or nested.get("week_tone")
    return None


def norm_tone(value: object) -> str:
    if value is None:
        raise SystemExit("service file must contain tone or week_tone")
    key = str(value).strip()
    if key not in TONE_NAMES:
        raise SystemExit(f"unsupported tone {value!r}; expected I-VIII or 1-8")
    return TONE_NAMES[key]


def repo_root() -> Path:
    return Path.cwd()


def default_template_for_tone(tone: str, root: Path) -> Path:
    p = root / "templates" / "boilerplate" / f"outline_Tone_{tone}_boilerplate_v8.odt"
    if not p.exists():
        raise SystemExit(f"missing template: {p}")
    return p


def write_metrics(audit: dict, metrics_path: Path, started: float, ok: bool) -> None:
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    duration = time.time() - started
    now = int(time.time())
    page_count = audit.get("pdf_page_count", 0) or 0
    bare = audit.get("bare_var_incipit_count", 0) or 0
    metrics = f"""# HELP tone9_last_run_timestamp_seconds Unix timestamp of last tone9 run.
# TYPE tone9_last_run_timestamp_seconds gauge
tone9_last_run_timestamp_seconds {now}
# HELP tone9_last_run_success Whether the last tone9 run succeeded.
# TYPE tone9_last_run_success gauge
tone9_last_run_success {1 if ok else 0}
# HELP tone9_last_run_duration_seconds Duration of last tone9 run.
# TYPE tone9_last_run_duration_seconds gauge
tone9_last_run_duration_seconds {duration:.3f}
# HELP tone9_last_pdf_page_count PDF page count from last render, if known.
# TYPE tone9_last_pdf_page_count gauge
tone9_last_pdf_page_count {page_count}
# HELP tone9_bare_var_incipit_count Exact bare var-incipit style references found in output ODT.
# TYPE tone9_bare_var_incipit_count gauge
tone9_bare_var_incipit_count {bare}
"""
    metrics_path.write_text(metrics, encoding="utf-8")


def cmd_generate(args: argparse.Namespace) -> int:
    started = time.time()
    ok = False
    audit_data: dict = {}
    try:
        service_path = Path(args.service)
        validation = validate_service_overlay(service_path)
        if not validation.ok:
            for error in validation.errors:
                print(f"ERROR: {error}", file=sys.stderr)
            for warning in validation.warnings:
                print(f"WARN: {warning}", file=sys.stderr)
            raise SystemExit(1)

        service = load_yaml(service_path)
        tone = norm_tone(service_tone(service))
        root = Path(args.root).resolve() if args.root else repo_root()
        template = Path(args.template).resolve() if args.template else default_template_for_tone(tone, root)
        out = Path(args.out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)

        slot_fill = fill_safe_slots(template, out, service, root)
        audit_data = audit_odt(out).to_dict()
        audit_data.update(
            {
                "service": str(service_path),
                "tone": tone,
                "template": str(template),
                "output": str(out),
                "service_validation_ok": validation.ok,
                "service_validation_warnings": validation.warnings,
                "slot_fill_count": slot_fill.count,
                "slot_fill_changes": [c.to_dict() for c in slot_fill.changes],
            }
        )
        if args.pdf:
            pdf = render_pdf(out, out.parent, Path(args.libreoffice_profile) if args.libreoffice_profile else None)
            audit_data["pdf"] = str(pdf)
            audit_data["pdf_page_count"] = pdf_page_count(pdf)
        if args.audit:
            write_markdown_audit(audit_data, out.with_suffix(".audit.md"))
        ok = True
        return 0
    finally:
        if args.metrics:
            write_metrics(audit_data, Path(args.metrics), started, ok)


def cmd_render(args: argparse.Namespace) -> int:
    pdf = render_pdf(Path(args.odt), Path(args.outdir), Path(args.libreoffice_profile) if args.libreoffice_profile else None)
    print(pdf)
    if args.png:
        pages = render_png_pages(pdf, Path(args.png_dir) if args.png_dir else Path(args.outdir) / "png_review")
        for p in pages:
            print(p)
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    audit = audit_odt(Path(args.odt)).to_dict()
    if args.pdf:
        audit["pdf_page_count"] = pdf_page_count(Path(args.pdf))
    out = Path(args.out) if args.out else Path(args.odt).with_suffix(".audit.md")
    write_markdown_audit(audit, out)
    print(yaml.safe_dump(audit, sort_keys=True), end="")
    return 0


def cmd_fixture_list(args: argparse.Namespace) -> int:
    data = load_yaml(Path(args.manifest))
    for f in data.get("fixtures", []):
        print(f"{f['id']}: {f.get('service_shape')} | Tone {f.get('tone')} | {f.get('title')}")
    return 0


def cmd_fixture_smoke(args: argparse.Namespace) -> int:
    data = load_yaml(Path(args.manifest))
    failed = False
    for f in data.get("fixtures", []):
        outline = Path(f["final_outline"])
        audit = audit_odt(outline).to_dict()
        print(f"--- {f['id']}")
        print(yaml.safe_dump(audit, sort_keys=True), end="")
        if not audit.get("zip_ok") or audit.get("bare_var_incipit_count"):
            failed = True
    return 1 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tone9")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate")
    g.add_argument("--service", required=True)
    g.add_argument("--template")
    g.add_argument("--root")
    g.add_argument("--out", required=True)
    g.add_argument("--pdf", action="store_true")
    g.add_argument("--audit", action="store_true")
    g.add_argument("--metrics")
    g.add_argument("--libreoffice-profile")
    g.set_defaults(func=cmd_generate)

    r = sub.add_parser("render")
    r.add_argument("odt")
    r.add_argument("--outdir", required=True)
    r.add_argument("--libreoffice-profile")
    r.add_argument("--png", action="store_true")
    r.add_argument("--png-dir")
    r.set_defaults(func=cmd_render)

    a = sub.add_parser("audit")
    a.add_argument("odt")
    a.add_argument("--pdf")
    a.add_argument("--out")
    a.set_defaults(func=cmd_audit)

    fl = sub.add_parser("fixture-list")
    fl.add_argument("--manifest", default="registries/live_fixture_manifest_v2.yaml")
    fl.set_defaults(func=cmd_fixture_list)

    fs = sub.add_parser("fixture-smoke")
    fs.add_argument("--manifest", default="registries/live_fixture_manifest_v2.yaml")
    fs.set_defaults(func=cmd_fixture_smoke)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
