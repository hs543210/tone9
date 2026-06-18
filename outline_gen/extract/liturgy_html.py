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


def _section(text: str, start_pat: str, end_pat: str) -> str:
    start = re.search(start_pat, text, re.I)
    if not start:
        return ""
    end = re.search(end_pat, text[start.end():], re.I)
    if not end:
        return text[start.end():]
    return text[start.end(): start.end() + end.start()]


def _has_second_reader_tone(block: str) -> bool:
    """Detect a second liturgical item introduced as `Reader: In the Nth Tone:`.

    This catches forms such as the St Iona fixture, whose second Prokeimenon is
    not introduced by the words `second prokeimenon`, but by a second reader cue
    before the Epistle reading.
    """
    return len(re.findall(r"Reader\s*:\s*In\s+the\s+[^:]{0,40}Tone\s*:", block, re.I)) >= 1


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

    prok_block = _section(text, r"The\s+Epistle|Prokimenon|Prokeimenon", r"The\s+Reading\s+is\s+from|\[\s*(?:Rom|II Tim|Tim|Heb|Gal|Eph|Cor)")
    alleluia_block = _section(text, r"Alleluia\s+in\s+the", r"\bGospel\b|\[\s*(?:Matt|Mt|Mark|Mk|Luke|Lk|John|Jn)")

    facts.second_prokeimenon = (
        _has_second_reader_tone(prok_block)
        or bool(re.search(r"2\s*nd\s*\[.*Proke", text, re.I))
        or bool(re.search(r"The righteous man shall rejoice in the Lord|Precious in the sight of the Lord", prok_block, re.I))
    )
    facts.second_alleluia = (
        _has_second_reader_tone(alleluia_block)
        or bool(re.search(r"2\s*nd\s*\[.*Alle", text, re.I))
        or bool(re.search(r"The righteous man shall flourish|Thy priests shall be clothed", alleluia_block, re.I))
    )
    facts.second_communion = contains_any(text, [
        "In everlasting remembrance",
        "The righteous shall be in everlasting remembrance",
    ])
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
