from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path

from .common import contains_any, find_first, html_to_text


@dataclass
class LiturgyFacts:
    beatitudes_total: int | None = None
    beatitudes_oktoichos: int | None = None
    beatitudes_minaion: int | None = None
    second_prokeimenon: bool = False
    second_alleluia: bool = False
    second_communion: bool = False
    epistle_refs: str | None = None
    gospel_refs: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def extract_liturgy_facts(path: Path) -> LiturgyFacts:
    text = html_to_text(path)
    facts = LiturgyFacts()
    b = re.search(r"Beatitudes\s+on\s+(\d+)\s+Octoechos\s*:\s*(\d+)\s*;\s*(?:Great Martyr|Menaion|Minaion|Saint)[^0-9]*(\d+)", text, re.I)
    if b:
        facts.beatitudes_total = int(b.group(1))
        facts.beatitudes_oktoichos = int(b.group(2))
        facts.beatitudes_minaion = int(b.group(3))
    else:
        b2 = re.search(r"Beatitudes\s+on\s+(\d+)", text, re.I)
        if b2:
            facts.beatitudes_total = int(b2.group(1))

    facts.second_prokeimenon = bool(re.search(r"In the\s+\d+(?:st|nd|rd|th)?\s+Tone\s*:\s*The righteous man|2\s*nd\s*\[.*Proke", text, re.I))
    facts.second_alleluia = bool(re.search(r"In the\s+\d+(?:st|nd|rd|th)?\s+Tone\s*:\s*The righteous man shall flourish|2\s*nd\s*\[.*Alle", text, re.I))
    facts.second_communion = contains_any(text, ["In everlasting remembrance", "The righteous shall be in everlasting remembrance"])
    facts.epistle_refs = find_first(r"\[((?:Rom|II Tim|Tim|Heb|Gal|Eph|Cor)[^\]]+)\]", text)
    facts.gospel_refs = find_first(r"\[((?:Matt|Mt|Mark|Mk|Luke|Lk|John|Jn)[^\]]+)\]", text)
    return facts


def main() -> None:
    import argparse, yaml

    p = argparse.ArgumentParser()
    p.add_argument("liturgy_html", type=Path)
    args = p.parse_args()
    print(yaml.safe_dump(extract_liturgy_facts(args.liturgy_html).to_dict(), sort_keys=False))


if __name__ == "__main__":
    main()
