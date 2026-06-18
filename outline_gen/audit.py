from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from zipfile import BadZipFile, ZipFile


@dataclass
class OdtAudit:
    odt_exists: bool
    odt_size_bytes: int = 0
    zip_ok: bool = False
    has_content_xml: bool = False
    has_styles_xml: bool = False
    bare_var_incipit_count: int = 0
    content_xml_bytes: int = 0
    styles_xml_bytes: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


def audit_odt(path: Path) -> OdtAudit:
    path = Path(path)
    audit = OdtAudit(odt_exists=path.exists(), odt_size_bytes=path.stat().st_size if path.exists() else 0)
    if not path.exists():
        return audit
    try:
        with ZipFile(path) as zf:
            names = set(zf.namelist())
            audit.zip_ok = True
            audit.has_content_xml = "content.xml" in names
            audit.has_styles_xml = "styles.xml" in names
            content = zf.read("content.xml") if audit.has_content_xml else b""
            styles = zf.read("styles.xml") if audit.has_styles_xml else b""
            audit.content_xml_bytes = len(content)
            audit.styles_xml_bytes = len(styles)
            text = content.decode("utf-8", errors="ignore") + styles.decode("utf-8", errors="ignore")
            audit.bare_var_incipit_count = text.count('text:style-name="var-incipit"') + text.count('style:name="var-incipit"')
    except BadZipFile:
        audit.zip_ok = False
    return audit


def write_markdown_audit(data: dict, path: Path, title: str = "tone9 audit") -> None:
    lines = [f"# {title}", ""]
    for key, value in data.items():
        lines.append(f"- {key}: {value}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
