from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable

import yaml
from lxml import etree

from .odt.package import OdtPackage

TEXT_NS = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
TABLE_NS = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
TEXT = f"{{{TEXT_NS}}}"
TABLE = f"{{{TABLE_NS}}}"
PARA_TAGS = {f"{TEXT}p", f"{TEXT}h"}
TABLE_ROW = f"{TABLE}table-row"

GOSPEL_NUMBER_NAMES = {
    "1": "I",
    "2": "II",
    "3": "III",
    "4": "IV",
    "5": "V",
    "6": "VI",
    "7": "VII",
    "8": "VIII",
    "9": "IX",
    "10": "X",
    "11": "XI",
    "I": "I",
    "II": "II",
    "III": "III",
    "IV": "IV",
    "V": "V",
    "VI": "VI",
    "VII": "VII",
    "VIII": "VIII",
    "IX": "IX",
    "X": "X",
    "XI": "XI",
}


@dataclass(frozen=True)
class SlotChange:
    slot_id: str
    target: str
    replacement: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class SlotFillResult:
    output: Path
    changes: list[SlotChange]

    @property
    def count(self) -> int:
        return len(self.changes)

    def to_dict(self) -> dict[str, Any]:
        return {"output": str(self.output), "count": self.count, "changes": [c.to_dict() for c in self.changes]}


class SlotFillError(RuntimeError):
    pass


class _Piece:
    def __init__(self, elem: etree._Element, attr: str):
        self.elem = elem
        self.attr = attr

    @property
    def value(self) -> str:
        return getattr(self.elem, self.attr) or ""

    @value.setter
    def value(self, new: str) -> None:
        setattr(self.elem, self.attr, new)


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SlotFillError(f"YAML root must be a mapping: {path}")
    return data


def normalize_gospel_number(value: Any) -> str:
    key = str(value).strip()
    try:
        return GOSPEL_NUMBER_NAMES[key]
    except KeyError as e:
        raise SlotFillError(f"unsupported Matins Gospel number: {value!r}") from e


def load_matins_gospel_cycle(path: Path) -> dict[str, dict[str, str]]:
    data = load_yaml(path)
    cycle = data.get("matins_gospels")
    if not isinstance(cycle, dict):
        raise SlotFillError(f"missing matins_gospels mapping: {path}")
    return cycle


def service_mapping(overlay: dict[str, Any]) -> dict[str, Any]:
    service = overlay.get("service")
    if not isinstance(service, dict):
        raise SlotFillError("service overlay must contain a service mapping")
    return service


def service_rank(service: dict[str, Any]) -> str:
    value = service.get("ods_rank") or service.get("proposed_ods_rank") or service.get("rank")
    if not value:
        raise SlotFillError("service.ods_rank or service.proposed_ods_rank is required")
    return str(value).strip()


def service_pericope(service: dict[str, Any], gospel_entry: dict[str, str]) -> str:
    mg = service.get("matins_gospel")
    if not isinstance(mg, dict):
        raise SlotFillError("service.matins_gospel mapping is required")
    reference = str(mg.get("reference") or "").strip()
    section = str(mg.get("section") or "").strip()
    if reference and section:
        return f"{reference} ({section})"
    if reference:
        return reference
    pericope = gospel_entry.get("pericope")
    if pericope:
        return str(pericope)
    raise SlotFillError("Matins Gospel reference is required")


def service_marker(overlay: dict[str, Any], service: dict[str, Any]) -> str:
    exact = service.get("header_marker")
    if exact:
        return str(exact)
    for touchups_key in ("user_touchups_v3", "user_touchups_v2", "user_touchups"):
        touchups = overlay.get(touchups_key)
        if isinstance(touchups, dict):
            marker = touchups.get("rank_marker")
            if isinstance(marker, str) and "[" in marker and "]" in marker:
                return marker[marker.index("[") : marker.rindex("]") + 1]
    rank = service_rank(service)
    label = str(service.get("rank_label") or "svc").strip()
    return f"[ {rank} – {label} ]"


def paragraph_text(elem: etree._Element) -> str:
    return "".join(elem.itertext())


def normalized_paragraph_text(elem: etree._Element) -> str:
    return " ".join(paragraph_text(elem).split())


def text_pieces(elem: etree._Element) -> list[_Piece]:
    pieces: list[_Piece] = []

    def visit(node: etree._Element) -> None:
        if node.text is not None:
            pieces.append(_Piece(node, "text"))
        for child in node:
            visit(child)
            if child.tail is not None:
                pieces.append(_Piece(child, "tail"))

    visit(elem)
    return pieces


def iter_paragraphs(root: etree._Element) -> Iterable[etree._Element]:
    for elem in root.iter():
        if elem.tag in PARA_TAGS:
            yield elem


def _find_one(root: etree._Element, exact_text: str) -> etree._Element:
    matches = [p for p in iter_paragraphs(root) if normalized_paragraph_text(p) == exact_text]
    if len(matches) != 1:
        raise SlotFillError(f"expected exactly one paragraph {exact_text!r}, found {len(matches)}")
    return matches[0]


def _replace_exact_text(root: etree._Element, *, slot_id: str, exact_text: str, replacement: str) -> SlotChange:
    elem = _find_one(root, exact_text)
    pieces = text_pieces(elem)
    non_empty = [piece for piece in pieces if piece.value]
    if len(non_empty) != 1:
        raise SlotFillError(f"cannot safely replace {exact_text!r}; paragraph has {len(non_empty)} text pieces")
    non_empty[0].value = replacement
    return SlotChange(slot_id, exact_text, replacement)


def _replace_placeholders(
    root: etree._Element,
    *,
    slot_id: str,
    exact_text: str,
    replacements: list[str],
) -> SlotChange:
    elem = _find_one(root, exact_text)
    pieces = text_pieces(elem)
    needed = len(replacements)
    seen = 0
    for piece in pieces:
        value = piece.value
        while "___" in value and seen < needed:
            value = value.replace("___", replacements[seen], 1)
            seen += 1
        piece.value = value
    if seen != needed:
        raise SlotFillError(f"expected {needed} placeholders in {exact_text!r}, replaced {seen}")
    return SlotChange(slot_id, exact_text, normalized_paragraph_text(elem))


def _replace_phrase_in_paragraph(
    root: etree._Element,
    *,
    slot_id: str,
    exact_text: str,
    old: str,
    new: str,
) -> SlotChange:
    elem = _find_one(root, exact_text)
    hits = 0
    for piece in text_pieces(elem):
        if old in piece.value:
            piece.value = piece.value.replace(old, new, 1)
            hits += 1
            break
    if hits != 1:
        raise SlotFillError(f"expected one phrase {old!r} in {exact_text!r}, found {hits}")
    return SlotChange(slot_id, exact_text, normalized_paragraph_text(elem))


def _ancestor(elem: etree._Element, tag: str) -> etree._Element | None:
    node = elem.getparent()
    while node is not None:
        if node.tag == tag:
            return node
        node = node.getparent()
    return None


def _remove_block_for_exact_paragraph(root: etree._Element, *, slot_id: str, exact_text: str) -> SlotChange:
    paragraph = _find_one(root, exact_text)
    row = _ancestor(paragraph, TABLE_ROW)
    if row is not None and row.getparent() is not None:
        row.getparent().remove(row)
        return SlotChange(slot_id, exact_text, "omit table row")
    if paragraph.getparent() is None:
        raise SlotFillError(f"cannot safely omit paragraph {exact_text!r}; no parent")
    paragraph.getparent().remove(paragraph)
    return SlotChange(slot_id, exact_text, "omit paragraph")


def explicit_slot_override(overlay: dict[str, Any], key: str) -> Any:
    overrides = overlay.get("slot_overrides")
    if isinstance(overrides, dict):
        return overrides.get(key)
    return None


def should_omit_vespers_readings(overlay: dict[str, Any]) -> bool:
    # Keep this deliberately explicit for the first structural pass.
    # Shape-rule inference can come later after fixture-wide regression is routine.
    return explicit_slot_override(overlay, "vespers.readings") == "omit"


def build_safe_slot_values(overlay: dict[str, Any], root: Path) -> dict[str, str]:
    service = service_mapping(overlay)
    mg = service.get("matins_gospel")
    if not isinstance(mg, dict):
        raise SlotFillError("service.matins_gospel mapping is required")
    gospel_no = normalize_gospel_number(mg.get("number"))
    cycle = load_matins_gospel_cycle(root / "registries" / "matins_gospel_cycle_v1.yaml")
    gospel_entry = cycle.get(gospel_no)
    if not gospel_entry:
        raise SlotFillError(f"Matins Gospel {gospel_no} not found in registry")
    pericope = service_pericope(service, gospel_entry)
    return {
        "title": str(service.get("title") or "").strip(),
        "tone": str(service.get("week_tone") or "").strip(),
        "gospel_no": gospel_no,
        "gospel_pericope": pericope,
        "header_marker": service_marker(overlay, service),
        "gospel_incipit": str(gospel_entry.get("gospel_incipit") or "").strip(),
        "exapostilarion": str(gospel_entry.get("exapostilarion") or "").strip(),
        "exapostilarion_theotokion": str(gospel_entry.get("exapostilarion_theotokion") or "").strip(),
        "evangelikal_sticheron": str(gospel_entry.get("evangelikal_sticheron") or "").strip(),
    }


def fill_safe_slots(input_odt: Path, output_odt: Path, overlay: dict[str, Any], root: Path) -> SlotFillResult:
    values = build_safe_slot_values(overlay, root)
    pkg = OdtPackage(input_odt)
    xml = pkg.read_bytes("content.xml")
    root_xml = etree.fromstring(xml)

    changes: list[SlotChange] = []
    changes.append(_replace_exact_text(root_xml, slot_id="header.title", exact_text="___", replacement=values["title"]))
    changes.append(
        _replace_placeholders(
            root_xml,
            slot_id="header.tone_and_gospel",
            exact_text="Matins Gospel ___: ___",
            replacements=[values["gospel_no"], values["gospel_pericope"]],
        )
    )
    changes.append(
        _replace_exact_text(
            root_xml,
            slot_id="header.service_rank_marker",
            exact_text="[ §___ – ___ svc ]",
            replacement=values["header_marker"],
        )
    )
    changes.append(
        _replace_placeholders(
            root_xml,
            slot_id="matins.gospel_cycle",
            exact_text="Matins Gospel ___ [___] “”…",
            replacements=[values["gospel_no"], values["gospel_pericope"]],
        )
    )
    changes.append(
        _replace_phrase_in_paragraph(
            root_xml,
            slot_id="matins.gospel_cycle",
            exact_text=f"Matins Gospel {values['gospel_no']} [{values['gospel_pericope']}] “”…",
            old="“”…",
            new=f"“{values['gospel_incipit']}”…",
        )
    )
    changes.append(
        _replace_placeholders(
            root_xml,
            slot_id="matins.gospel_cycle",
            exact_text="Exaposteilaria: Matins Gospel ___",
            replacements=[values["gospel_no"]],
        )
    )
    changes.append(
        _replace_phrase_in_paragraph(
            root_xml,
            slot_id="matins.gospel_cycle",
            exact_text="[Oktoich.] “”…",
            old="“”…",
            new=f"“{values['exapostilarion']}”…",
        )
    )
    changes.append(
        _replace_phrase_in_paragraph(
            root_xml,
            slot_id="matins.gospel_cycle",
            exact_text="“Now”… [Oktoich.] “”…",
            old="“”…",
            new=f"“{values['exapostilarion_theotokion']}”…",
        )
    )
    changes.append(
        _replace_placeholders(
            root_xml,
            slot_id="matins.gospel_cycle",
            exact_text="“Glory”… [Evang. Stichiron ___]“”…",
            replacements=[values["gospel_no"]],
        )
    )
    changes.append(
        _replace_phrase_in_paragraph(
            root_xml,
            slot_id="matins.gospel_cycle",
            exact_text=f"“Glory”… [Evang. Stichiron {values['gospel_no']}]“”…",
            old="“”…",
            new=f"“{values['evangelikal_sticheron']}”…",
        )
    )

    if should_omit_vespers_readings(overlay):
        changes.append(
            _remove_block_for_exact_paragraph(
                root_xml,
                slot_id="vespers.readings",
                exact_text="3 Readings: [Minai.]“A Reading from ___”…",
            )
        )

    new_xml = etree.tostring(root_xml, encoding="UTF-8", xml_declaration=True)
    pkg.write_replacements(output_odt, {"content.xml": new_xml})
    return SlotFillResult(Path(output_odt), changes)
