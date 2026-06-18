from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import yaml

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


def load_service(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"service file is not a mapping: {path}")
    return data


def norm_tone(value: object) -> str:
    if value is None:
        raise SystemExit("service file must contain tone")
    key = str(value).strip()
    if key not in TONE_NAMES:
        raise SystemExit(f"unsupported tone {value!r}; expected I-VIII or 1-8")
    return TONE_NAMES[key]


def repo_root() -> Path:
    # Installed package fallback: current working directory is the project root in the container.
    return Path.cwd()


def default_template_for_tone(tone: str, root: Path) -> Path:
    p = root / "templates" / "boilerplate" / f"outline_Tone_{tone}_boilerplate_v8.odt"
    if not p.exists():
        raise SystemExit(f"missing template: {p}")
    return p


def render_pdf(odt: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "soffice", "--headless", "--convert-to", "pdf:writer_pdf_Export",
        "--outdir", str(out_dir), str(odt),
    ]
    subprocess.run(cmd, check=True)
    pdf = out_dir / (odt.stem + ".pdf")
    if not pdf.exists():
        raise SystemExit(f"LibreOffice did not produce expected PDF: {pdf}")
    return pdf


def audit_odt(path: Path) -> dict:
    result = {
        "odt_exists": path.exists(),
        "odt_size_bytes": path.stat().st_size if path.exists() else 0,
        "zip_ok": False,
        "has_content_xml": False,
        "has_styles_xml": False,
        "bare_var_incipit_count": None,
    }
    if not path.exists():
        return result
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        result["zip_ok"] = True
        result["has_content_xml"] = "content.xml" in names
        result["has_styles_xml"] = "styles.xml" in names
        if "content.xml" in names:
            text = z.read("content.xml").decode("utf-8", errors="replace")
            result["bare_var_incipit_count"] = text.count('text:style-name="var-incipit"')
    return result


def write_audit(audit: dict, path: Path) -> None:
    lines = ["# tone9 audit", ""]
    for k, v in audit.items():
        lines.append(f"- {k}: {v}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_metrics(audit: dict, metrics_path: Path, started: float, ok: bool) -> None:
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    duration = time.time() - started
    now = int(time.time())
    page_count = audit.get("pdf_page_count", 0) or 0
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
tone9_bare_var_incipit_count {audit.get('bare_var_incipit_count') or 0}
"""
    metrics_path.write_text(metrics, encoding="utf-8")


def pdf_page_count(pdf: Path) -> int:
    try:
        out = subprocess.check_output(["pdfinfo", str(pdf)], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            if line.startswith("Pages:"):
                return int(line.split(":", 1)[1].strip())
    except Exception:
        return 0
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    started = time.time()
    ok = False
    audit = {}
    try:
        service = load_service(Path(args.service))
        tone = norm_tone(service.get("tone"))
        root = Path(args.root).resolve() if args.root else repo_root()
        template = Path(args.template).resolve() if args.template else default_template_for_tone(tone, root)
        out = Path(args.out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(template, out)
        audit = audit_odt(out)
        audit.update({
            "service": str(Path(args.service)),
            "tone": tone,
            "template": str(template),
            "output": str(out),
        })
        if args.pdf:
            pdf = render_pdf(out, out.parent)
            audit["pdf"] = str(pdf)
            audit["pdf_page_count"] = pdf_page_count(pdf)
        if args.audit:
            write_audit(audit, out.with_suffix(".audit.md"))
        ok = True
        return 0
    finally:
        if args.metrics:
            write_metrics(audit, Path(args.metrics), started, ok)


def cmd_audit(args: argparse.Namespace) -> int:
    audit = audit_odt(Path(args.odt))
    write_audit(audit, Path(args.out) if args.out else Path(args.odt).with_suffix(".audit.md"))
    print(yaml.safe_dump(audit, sort_keys=True), end="")
    return 0


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
    g.set_defaults(func=cmd_generate)
    a = sub.add_parser("audit")
    a.add_argument("odt")
    a.add_argument("--out")
    a.set_defaults(func=cmd_audit)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
