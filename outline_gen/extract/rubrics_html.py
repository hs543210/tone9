from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path

from .common import contains_any, find_first, html_to_text, normalize_ws

TONE_WORDS = {
    "1": "I", "one": "I", "i": "I",
    "2": "II", "two": "II", "ii": "II",
    "3": "III", "three": "III", "iii": "III",
    "4": "IV", "four": "IV", "iv": "IV",
    "5": "V", "five": "V", "v": "V",
    "6": "VI", "six": "VI", "vi": "VI",
    "7": "VII", "seven": "VII", "vii": "VII",
    "8": "VIII", "eight": "VIII", "viii": "VIII",
}


@dataclass
class RubricsFacts:
    title: str | None = None
    tone: str | None = None
    matins_gospel_number: str | None = None
    matins_gospel_reference: str | None = None
    lord_i_cried_total: int | None = None
    lord_i_cried_oktoichos: int | None = None
    lord_i_cried_minaion: int | None = None
    psalm_118: bool | None = None
    polyeleos: bool | None = None
    readings_count: int | None = None
    litia: bool | None = None
    praises_total: int | None = None
    praises_oktoichos: int | None = None
    praises_minaion: int | None = None
    praises_final_two_psalm_verses: bool | None = None
    split_hours: bool | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _roman_tone(value: str | None) -> str | None:
    if not value:
        return None
    return TONE_WORDS.get(value.strip().lower())


def _first_title(text: str) -> str | None:
    for pat in [
        r"\bSs\.\s+Peter\s+and\s+Paul\b",
        r"\b(?:App\.?|Apostles?)\s+Peter\s*(?:\+|and)\s*Paul\b",
        r"^\s*([^\n\r]{0,120}?(?:Martyr|Hierarch|Iona|Jonah|Efs[eé]vios|Theodore|Stratelates)[^\n\r]{0,80})",
    ]:
        hit = find_first(pat, text)
        if hit:
            return normalize_ws(hit)
    return None


def extract_rubrics_facts(path: Path) -> RubricsFacts:
    text = html_to_text(path)
    facts = RubricsFacts()

    facts.title = _first_title(text)
    facts.tone = _roman_tone(find_first(r"Tone\s+([IVX]+|[1-8]|one|two|three|four|five|six|seven|eight)\b", text))

    mg = re.search(r"Matins\s+Gospel\s+([0-9IVX]+)\s*,?\s*([^\.]{0,120}?§\d+\)?)", text, re.I)
    if mg:
        facts.matins_gospel_number = normalize_ws(mg.group(1))
        facts.matins_gospel_reference = normalize_ws(mg.group(2) or "") or None

    lic = re.search(
        r"Lord I have Cried[^:]*,?\s*Tone\s+[IVX0-9]+,?\s*on\s+(\d+)\s*:\s*Octoechos\s+(\d+)\s*;\s*(?:Great Martyr|Menaion|Minaion|Saint|Apostles?)[^0-9]*(\d+)",
        text,
        re.I,
    )
    if lic:
        facts.lord_i_cried_total = int(lic.group(1))
        facts.lord_i_cried_oktoichos = int(lic.group(2))
        facts.lord_i_cried_minaion = int(lic.group(3))

    facts.psalm_118 = contains_any(text, ["Blessed are the blameless", "Psalm 118"])
    facts.polyeleos = contains_any(text, ["Polyeleos", "Megalynarion", "Magnification"])
    facts.readings_count = 3 if re.search(r"\b3\s+Readings\b|Three\s+Readings|readings?\s+from", text, re.I) else 0
    facts.litia = bool(re.search(r"\bLitia\b", text, re.I))

    praises = re.search(
        r"Praises[^:]{0,80}\bon\s+(\d+)\s*:\s*(?:Resurrection|Octoechos)\s+(\d+)\s*;\s*(?:Apostles?|Menaion|Minaion|Saint)[^0-9]*(\d+)",
        text,
        re.I,
    )
    if praises:
        facts.praises_total = int(praises.group(1))
        facts.praises_oktoichos = int(praises.group(2))
        facts.praises_minaion = int(praises.group(3))
    else:
        pr = re.search(r"Praises[^\.]{0,120}on\s+(\d+)", text, re.I)
        if pr:
            facts.praises_total = int(pr.group(1))
    facts.praises_final_two_psalm_verses = contains_any(
        text,
        [
            "Their sound hath gone forth into all the earth",
            "The heavens declare the glory of God",
        ],
    )

    facts.split_hours = bool(re.search(r"1st\s*/\s*6th|third hour|3rd\s+hour", text, re.I))
    return facts


def main() -> None:
    import argparse, yaml

    p = argparse.ArgumentParser()
    p.add_argument("rubrics_html", type=Path)
    args = p.parse_args()
    print(yaml.safe_dump(extract_rubrics_facts(args.rubrics_html).to_dict(), sort_keys=False))


if __name__ == "__main__":
    main()
