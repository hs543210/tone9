from __future__ import annotations

import os
import subprocess
from pathlib import Path


def render_pdf(odt: Path, out_dir: Path, profile_dir: Path | None = None) -> Path:
    """Render an ODT to PDF with headless LibreOffice."""
    odt = Path(odt).resolve()
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["soffice", "--headless"]
    if profile_dir:
        profile_dir = Path(profile_dir).resolve()
        profile_dir.mkdir(parents=True, exist_ok=True)
        cmd.append(f"-env:UserInstallation=file://{profile_dir}")
    cmd += ["--convert-to", "pdf:writer_pdf_Export", "--outdir", str(out_dir), str(odt)]
    env = os.environ.copy()
    env.setdefault("HOME", str(out_dir))
    subprocess.run(cmd, check=True, env=env)
    pdf = out_dir / f"{odt.stem}.pdf"
    if not pdf.exists():
        raise FileNotFoundError(f"LibreOffice did not produce expected PDF: {pdf}")
    return pdf


def pdf_page_count(pdf: Path) -> int:
    try:
        out = subprocess.check_output(["pdfinfo", str(pdf)], text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return 0
    for line in out.splitlines():
        if line.startswith("Pages:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                return 0
    return 0


def render_png_pages(pdf: Path, out_dir: Path, prefix: str | None = None, dpi: int = 144) -> list[Path]:
    """Render a PDF to PNG pages using pdftoppm."""
    pdf = Path(pdf).resolve()
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = prefix or pdf.stem
    base = out_dir / prefix
    subprocess.run(["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(base)], check=True)
    return sorted(out_dir.glob(f"{prefix}-*.png"))
