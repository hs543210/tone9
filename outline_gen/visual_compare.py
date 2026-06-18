from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageChops, ImageOps, ImageStat

from .render import render_pdf, render_png_pages


@dataclass
class PageDiff:
    page: int
    expected_png: str | None
    actual_png: str | None
    diff_png: str | None
    expected_size: tuple[int, int] | None
    actual_size: tuple[int, int] | None
    size_match: bool
    diff_bbox: tuple[int, int, int, int] | None
    changed_pixels: int
    total_pixels: int
    changed_percent: float
    rms: float


@dataclass
class CompareReport:
    expected: str
    actual: str
    outdir: str
    expected_page_count: int
    actual_page_count: int
    page_count_match: bool
    max_changed_percent: float
    max_rms: float
    pages: list[PageDiff]

    def to_dict(self) -> dict:
        d = asdict(self)
        # dataclasses convert tuples to tuples; JSON can handle them as arrays.
        return d


def _ensure_pdf(path: Path, workdir: Path, label: str, profile_dir: Path | None = None) -> Path:
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        return path.resolve()
    if path.suffix.lower() == ".odt":
        return render_pdf(path, workdir / f"{label}_pdf", profile_dir)
    raise ValueError(f"expected .odt or .pdf: {path}")


def _render_pages(pdf: Path, workdir: Path, label: str, dpi: int) -> list[Path]:
    out = workdir / f"{label}_png"
    return render_png_pages(pdf, out, prefix=label, dpi=dpi)


def _count_changed_pixels(diff: Image.Image, threshold: int) -> tuple[int, int]:
    gray = ImageOps.grayscale(diff)
    # Convert to a 1-bit-ish mask through threshold.
    mask = gray.point(lambda p: 255 if p > threshold else 0)
    hist = mask.histogram()
    changed = hist[255]
    total = mask.size[0] * mask.size[1]
    return changed, total


def _open_rgb(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def _compare_pair(expected_png: Path | None, actual_png: Path | None, diff_path: Path, page: int, threshold: int) -> PageDiff:
    if expected_png is None or actual_png is None:
        return PageDiff(
            page=page,
            expected_png=str(expected_png) if expected_png else None,
            actual_png=str(actual_png) if actual_png else None,
            diff_png=None,
            expected_size=None,
            actual_size=None,
            size_match=False,
            diff_bbox=None,
            changed_pixels=0,
            total_pixels=0,
            changed_percent=100.0,
            rms=0.0,
        )

    exp = _open_rgb(expected_png)
    act = _open_rgb(actual_png)
    expected_size = exp.size
    actual_size = act.size
    size_match = expected_size == actual_size

    width = max(exp.width, act.width)
    height = max(exp.height, act.height)
    if exp.size != (width, height):
        canvas = Image.new("RGB", (width, height), "white")
        canvas.paste(exp, (0, 0))
        exp = canvas
    if act.size != (width, height):
        canvas = Image.new("RGB", (width, height), "white")
        canvas.paste(act, (0, 0))
        act = canvas

    diff = ImageChops.difference(exp, act)
    bbox = diff.getbbox()
    changed, total = _count_changed_pixels(diff, threshold)
    stat = ImageStat.Stat(diff)
    rms = sum(v * v for v in stat.rms) ** 0.5
    diff_path.parent.mkdir(parents=True, exist_ok=True)
    diff.save(diff_path)
    return PageDiff(
        page=page,
        expected_png=str(expected_png),
        actual_png=str(actual_png),
        diff_png=str(diff_path),
        expected_size=expected_size,
        actual_size=actual_size,
        size_match=size_match,
        diff_bbox=bbox,
        changed_pixels=changed,
        total_pixels=total,
        changed_percent=(changed / total * 100.0) if total else 0.0,
        rms=float(rms),
    )


def _make_contact_sheet(report: CompareReport, outdir: Path) -> Path | None:
    rows = []
    for page in report.pages:
        paths = [page.expected_png, page.actual_png, page.diff_png]
        if not all(paths):
            continue
        imgs = [Image.open(p).convert("RGB") for p in paths if p]
        thumb_h = 420
        thumbs = []
        for img in imgs:
            scale = thumb_h / img.height
            thumb = img.resize((max(1, int(img.width * scale)), thumb_h))
            thumbs.append(thumb)
        w = sum(t.width for t in thumbs) + 20 * (len(thumbs) + 1)
        h = thumb_h + 40
        row = Image.new("RGB", (w, h), "white")
        x = 20
        for t in thumbs:
            row.paste(t, (x, 20))
            x += t.width + 20
        rows.append(row)
    if not rows:
        return None
    width = max(r.width for r in rows)
    height = sum(r.height for r in rows)
    sheet = Image.new("RGB", (width, height), "white")
    y = 0
    for row in rows:
        sheet.paste(row, (0, y))
        y += row.height
    out = outdir / "contact_sheet_expected_actual_diff.png"
    sheet.save(out)
    return out


def compare_documents(
    expected: Path,
    actual: Path,
    outdir: Path,
    dpi: int = 144,
    threshold: int = 16,
    profile_dir: Path | None = None,
) -> CompareReport:
    outdir = Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    expected_pdf = _ensure_pdf(Path(expected), outdir, "expected", profile_dir)
    actual_pdf = _ensure_pdf(Path(actual), outdir, "actual", profile_dir)
    expected_pages = _render_pages(expected_pdf, outdir, "expected", dpi)
    actual_pages = _render_pages(actual_pdf, outdir, "actual", dpi)

    page_count = max(len(expected_pages), len(actual_pages))
    diffs: list[PageDiff] = []
    for idx in range(page_count):
        exp = expected_pages[idx] if idx < len(expected_pages) else None
        act = actual_pages[idx] if idx < len(actual_pages) else None
        diffs.append(_compare_pair(exp, act, outdir / "diff_png" / f"diff-page-{idx+1}.png", idx + 1, threshold))

    report = CompareReport(
        expected=str(expected),
        actual=str(actual),
        outdir=str(outdir),
        expected_page_count=len(expected_pages),
        actual_page_count=len(actual_pages),
        page_count_match=len(expected_pages) == len(actual_pages),
        max_changed_percent=max((d.changed_percent for d in diffs), default=0.0),
        max_rms=max((d.rms for d in diffs), default=0.0),
        pages=diffs,
    )
    (outdir / "visual_compare_report.json").write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_markdown(report, outdir / "visual_compare_report.md")
    _make_contact_sheet(report, outdir)
    return report


def _write_markdown(report: CompareReport, path: Path) -> None:
    lines = ["# tone9 visual compare", ""]
    lines.append(f"- expected: `{report.expected}`")
    lines.append(f"- actual: `{report.actual}`")
    lines.append(f"- expected pages: {report.expected_page_count}")
    lines.append(f"- actual pages: {report.actual_page_count}")
    lines.append(f"- page count match: {report.page_count_match}")
    lines.append(f"- max changed percent: {report.max_changed_percent:.4f}")
    lines.append(f"- max RMS: {report.max_rms:.4f}")
    lines.append("")
    lines.append("| page | size match | changed % | RMS | bbox |")
    lines.append("|---:|:---:|---:|---:|---|")
    for p in report.pages:
        lines.append(f"| {p.page} | {p.size_match} | {p.changed_percent:.4f} | {p.rms:.4f} | {p.diff_bbox} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="tone9-visual-compare")
    p.add_argument("--expected", required=True, type=Path)
    p.add_argument("--actual", required=True, type=Path)
    p.add_argument("--outdir", required=True, type=Path)
    p.add_argument("--dpi", type=int, default=144)
    p.add_argument("--threshold", type=int, default=16)
    p.add_argument("--libreoffice-profile", type=Path)
    p.add_argument("--fail-threshold-pct", type=float)
    args = p.parse_args(argv)
    report = compare_documents(args.expected, args.actual, args.outdir, args.dpi, args.threshold, args.libreoffice_profile)
    print(Path(report.outdir) / "visual_compare_report.md")
    if args.fail_threshold_pct is not None and report.max_changed_percent > args.fail_threshold_pct:
        return 1
    if not report.page_count_match:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
