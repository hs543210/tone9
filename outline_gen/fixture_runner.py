from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import yaml

from .audit import audit_odt
from .render import pdf_page_count, render_pdf
from .visual_compare import compare_documents


@dataclass(frozen=True)
class FixtureGeneration:
    id: str
    service_overlay: str
    expected_outline: str
    output_odt: str
    output_pdf: str | None
    audit: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FixtureCompare:
    id: str
    expected_outline: str
    actual_outline: str
    report: str
    expected_page_count: int
    actual_page_count: int
    page_count_match: bool
    max_changed_percent: float
    max_rms: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def load_manifest(path: Path) -> list[dict[str, Any]]:
    data = load_yaml(path)
    fixtures = data.get("fixtures") or []
    if not isinstance(fixtures, list):
        raise ValueError(f"fixtures must be a list: {path}")
    return [f for f in fixtures if isinstance(f, dict)]


def fixture_output_dir(base_outdir: Path, fixture: dict[str, Any]) -> Path:
    return Path(base_outdir) / str(fixture["id"])


def generate_fixture(
    fixture: dict[str, Any],
    *,
    root: Path,
    outdir: Path,
    generate_one,
    pdf: bool = False,
    libreoffice_profile: Path | None = None,
) -> FixtureGeneration:
    fid = str(fixture["id"])
    service_overlay = Path(fixture["service_overlay"])
    expected_outline = Path(fixture["final_outline"])
    workdir = fixture_output_dir(outdir, fixture)
    workdir.mkdir(parents=True, exist_ok=True)
    output_odt = workdir / "outline.odt"
    audit = generate_one(service_overlay, output_odt)
    output_pdf: Path | None = None
    if pdf:
        output_pdf = render_pdf(output_odt, workdir, libreoffice_profile)
        audit["pdf"] = str(output_pdf)
        audit["pdf_page_count"] = pdf_page_count(output_pdf)
    return FixtureGeneration(
        id=fid,
        service_overlay=str(service_overlay),
        expected_outline=str(expected_outline),
        output_odt=str(output_odt),
        output_pdf=str(output_pdf) if output_pdf else None,
        audit=audit,
    )


def write_generation_summary(results: list[FixtureGeneration], path: Path) -> None:
    lines = ["# tone9 generated fixture summary", ""]
    lines.append("| fixture | output | zip ok | bare var incipit | slot changes | pdf pages |")
    lines.append("|---|---|:---:|---:|---:|---:|")
    for r in results:
        audit = r.audit
        lines.append(
            f"| `{r.id}` | `{r.output_odt}` | {audit.get('zip_ok')} | "
            f"{audit.get('bare_var_incipit_count', 0)} | {audit.get('slot_fill_count', 0)} | "
            f"{audit.get('pdf_page_count', '')} |"
        )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def compare_fixture(
    fixture: dict[str, Any],
    *,
    generated_outdir: Path,
    compare_outdir: Path,
    libreoffice_profile: Path | None = None,
) -> FixtureCompare:
    fid = str(fixture["id"])
    expected = Path(fixture["final_outline"])
    actual = fixture_output_dir(generated_outdir, fixture) / "outline.odt"
    outdir = Path(compare_outdir) / fid
    report = compare_documents(expected, actual, outdir, profile_dir=libreoffice_profile)
    return FixtureCompare(
        id=fid,
        expected_outline=str(expected),
        actual_outline=str(actual),
        report=str(Path(report.outdir) / "visual_compare_report.md"),
        expected_page_count=report.expected_page_count,
        actual_page_count=report.actual_page_count,
        page_count_match=report.page_count_match,
        max_changed_percent=report.max_changed_percent,
        max_rms=report.max_rms,
    )


def write_compare_summary(results: list[FixtureCompare], path: Path) -> None:
    lines = ["# tone9 fixture visual regression summary", ""]
    lines.append("| fixture | pages | page count match | max changed % | max RMS | report |")
    lines.append("|---|---:|:---:|---:|---:|---|")
    for r in results:
        lines.append(
            f"| `{r.id}` | {r.expected_page_count}/{r.actual_page_count} | {r.page_count_match} | "
            f"{r.max_changed_percent:.4f} | {r.max_rms:.4f} | `{r.report}` |"
        )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
