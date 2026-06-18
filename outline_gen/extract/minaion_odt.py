from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path

from .common import find_first, odt_to_text


@dataclass
class MinaionFacts:
    title: str | None = None
    vespers_lord_i_cried_stichera: int | None = None
    has_vespers_readings: bool = False
    has_polyeleos_material: bool = False
    has_saint_exapostilarion: bool = False
    kontakion_tone: str | None = None
    troparion_tone: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def extract_minaion_facts(path: Path) -> MinaionFacts:
    text = odt_to_text(path)
    facts = MinaionFacts()
    facts.title = find_first(r"(?:COMMEMORATION OF|Great Martyr|Holy Great Martyr|Hierarch)[^\.\n]{0,120}", text)
    st = re.search(r"On [“\"]Lord,? I have cried[^0-9]{0,80}(\d+)\s+stich", text, re.I)
    if st:
        facts.vespers_lord_i_cried_stichera = int(st.group(1))
    facts.has_vespers_readings = bool(re.search(r"(?:A|The) Reading from|readings? from", text, re.I))
    facts.has_polyeleos_material = bool(re.search(r"Polyeleos|Megalynarion|We magnify thee", text, re.I))
    facts.has_saint_exapostilarion = bool(re.search(r"Exapostilarion", text, re.I))
    facts.kontakion_tone = find_first(r"Kontakion,?\s+in\s+Tone\s+([IVX]+|[1-8])", text)
    facts.troparion_tone = find_first(r"Troparion,?\s+in\s+Tone\s+([IVX]+|[1-8])", text)
    return facts


def main() -> None:
    import argparse, yaml

    p = argparse.ArgumentParser()
    p.add_argument("minaion_odt", type=Path)
    args = p.parse_args()
    print(yaml.safe_dump(extract_minaion_facts(args.minaion_odt).to_dict(), sort_keys=False))


if __name__ == "__main__":
    main()
