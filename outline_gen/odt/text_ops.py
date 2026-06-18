from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .package import OdtPackage


@dataclass(frozen=True)
class ReplacementResult:
    count: int
    output: Path


def replace_content_xml_text(input_odt: Path, output_odt: Path, replacements: dict[str, str]) -> ReplacementResult:
    """Literal XML text replacement in content.xml.

    This is intentionally simple and conservative. It is suitable for stable
    placeholder fields such as `[ §___ – ___ svc ]`, not arbitrary rich layout
    changes. Rich slot work should eventually use XML-aware patching.
    """
    pkg = OdtPackage(input_odt)
    content = pkg.read_text("content.xml")
    total = 0
    for old, new in replacements.items():
        n = content.count(old)
        content = content.replace(old, new)
        total += n
    pkg.write_replacements(output_odt, {"content.xml": content})
    return ReplacementResult(count=total, output=Path(output_odt))
