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
    if "header_marker" in service:
        return str(service.get("header_marker") or "")
    override = explicit_slot_override(overlay, "header.service_rank_marker")
    if override is not None:
        return str(override)
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




def get_path(data: dict[str, Any], *keys: str) -> Any:
    node: Any = data
    for key in keys:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


def print_slots(overlay: dict[str, Any]) -> dict[str, Any]:
    value = overlay.get("print_slots")
    return value if isinstance(value, dict) else {}




def _find_first(root: etree._Element, exact_text: str) -> etree._Element:
    for p in iter_paragraphs(root):
        if normalized_paragraph_text(p) == exact_text:
            return p
    raise SlotFillError(f"expected at least one paragraph {exact_text!r}, found 0")


def _replace_first_text_across_pieces(
    root: etree._Element,
    *,
    slot_id: str,
    exact_text: str,
    replacements: list[tuple[str, str]],
) -> SlotChange:
    elem = _find_first(root, exact_text)
    missing: list[str] = []
    for old, new in replacements:
        replaced = False
        for piece in text_pieces(elem):
            if old in piece.value:
                piece.value = piece.value.replace(old, new, 1)
                replaced = True
                break
        if not replaced:
            missing.append(old)
    if missing:
        raise SlotFillError(f"could not replace {missing!r} in first {exact_text!r}")
    return SlotChange(slot_id, exact_text, normalized_paragraph_text(elem))


def _replace_text_across_pieces(
    root: etree._Element,
    *,
    slot_id: str,
    exact_text: str,
    replacements: list[tuple[str, str]],
    require_all: bool = True,
) -> SlotChange:
    elem = _find_one(root, exact_text)
    missing: list[str] = []
    for old, new in replacements:
        replaced = False
        for piece in text_pieces(elem):
            if old in piece.value:
                piece.value = piece.value.replace(old, new, 1)
                replaced = True
                break
        if not replaced:
            missing.append(old)
    if require_all and missing:
        raise SlotFillError(f"could not replace {missing!r} in {exact_text!r}")
    return SlotChange(slot_id, exact_text, normalized_paragraph_text(elem))




def _set_first_matching_piece_and_clear_rest(root: etree._Element, *, slot_id: str, exact_text: str, replacement: str) -> SlotChange:
    elem = _find_first(root, exact_text)
    pieces = [piece for piece in text_pieces(elem) if piece.value]
    if not pieces:
        raise SlotFillError(f"cannot safely replace empty paragraph {exact_text!r}")
    pieces[0].value = replacement
    for piece in pieces[1:]:
        piece.value = ""
    return SlotChange(slot_id, exact_text, normalized_paragraph_text(elem))


def _set_first_piece_and_clear_rest(root: etree._Element, *, slot_id: str, exact_text: str, replacement: str) -> SlotChange:
    elem = _find_one(root, exact_text)
    pieces = [piece for piece in text_pieces(elem) if piece.value]
    if not pieces:
        raise SlotFillError(f"cannot safely replace empty paragraph {exact_text!r}")
    pieces[0].value = replacement
    for piece in pieces[1:]:
        piece.value = ""
    return SlotChange(slot_id, exact_text, normalized_paragraph_text(elem))


def _clone_row_after_exact_paragraph(root: etree._Element, *, slot_id: str, exact_text: str) -> etree._Element:
    paragraph = _find_one(root, exact_text)
    row = _ancestor(paragraph, TABLE_ROW)
    if row is not None and row.getparent() is not None:
        new_row = etree.fromstring(etree.tostring(row))
        row.addnext(new_row)
        return new_row
    if paragraph.getparent() is None:
        raise SlotFillError(f"cannot safely clone paragraph for {exact_text!r}")
    new_paragraph = etree.fromstring(etree.tostring(paragraph))
    paragraph.addnext(new_paragraph)
    return new_paragraph


def _replace_in_subtree(elem: etree._Element, replacements: list[tuple[str, str]]) -> None:
    for old, new in replacements:
        replaced = False
        for piece in text_pieces(elem):
            if old in piece.value:
                piece.value = piece.value.replace(old, new, 1)
                replaced = True
                break
        if not replaced:
            raise SlotFillError(f"could not replace {old!r} in cloned subtree")


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



def _fill_peter_paul_vespers(root: etree._Element, slots: dict[str, Any]) -> list[SlotChange]:
    pp = get_path(slots, "vespers")
    if not isinstance(pp, dict):
        return []
    changes: list[SlotChange] = []
    lic = pp.get("lord_i_cried") if isinstance(pp.get("lord_i_cried"), dict) else {}
    if lic:
        changes.append(_replace_text_across_pieces(
            root,
            slot_id="vespers.lord_i_cried.oktoichos_count",
            exact_text='___ stichira:[Oktoichos,T.V]“By Thy Precious Cross didst Thou put the devil”…',
            replacements=[("___", str(lic.get("oktoichos_count", "")))],
        ))
        changes.append(_replace_text_across_pieces(
            root,
            slot_id="vespers.lord_i_cried.minaion_count",
            exact_text='___” [Minai.,T.___] “”…',
            replacements=[
                ("___", str(lic.get("minaion_count", ""))),
                ("___", str(lic.get("minaion_tone", ""))),
                ('“”…', f'“{lic.get("minaion_incipit", "")}”…'),
            ],
        ))
        changes.append(_replace_text_across_pieces(
            root,
            slot_id="vespers.lord_i_cried.glory",
            exact_text='“Glory”… ⮡[T.___] “”…',
            replacements=[
                ("___", str(lic.get("glory_tone", ""))),
                ('“”…', f'“{lic.get("glory_incipit", "")}”…'),
            ],
        ))
    aposticha = pp.get("aposticha") if isinstance(pp.get("aposticha"), dict) else {}
    if aposticha:
        changes.append(_replace_text_across_pieces(
            root,
            slot_id="vespers.aposticha.glory",
            exact_text='“Glory”… [Minai.,T.___] “”…',
            replacements=[
                ("___", str(aposticha.get("glory_tone", ""))),
                ('“”…', f'“{aposticha.get("glory_incipit", "")}”…'),
            ],
        ))
        changes.append(_set_first_piece_and_clear_rest(
            root,
            slot_id="vespers.aposticha.now",
            exact_text='“Now”… [Oktoich.,T.V] “Thou art the temple and portal, the palace”…',
            replacement=f'“Now”… [Minai.,T.{aposticha.get("now_tone", "")}] “{aposticha.get("now_incipit", "")}”…',
        ))
    return changes


def _fill_peter_paul_matins(root: etree._Element, slots: dict[str, Any]) -> list[SlotChange]:
    matins = get_path(slots, "matins")
    if not isinstance(matins, dict):
        return []
    changes: list[SlotChange] = []
    troparia = matins.get("troparia") if isinstance(matins.get("troparia"), dict) else {}
    if troparia:
        changes.append(_replace_text_across_pieces(
            root,
            slot_id="matins.troparia.glory",
            exact_text='“Glory”… [Minai.,T.___] 1x “”…',
            replacements=[
                ("___", str(troparia.get("glory_tone", ""))),
                ('“”…', f'“{troparia.get("glory_incipit", "")}”…'),
            ],
        ))
        changes.append(_set_first_piece_and_clear_rest(
            root,
            slot_id="matins.troparia.now",
            exact_text='“Now”…Theotok.[Oktoich.,T.V] “Rejoice, impassable gate of the Lord! Rejoice,”…',
            replacement=f'“Now”…Theotok. [Oktoich.,T.{troparia.get("now_tone", "")}] “{troparia.get("now_incipit", "")}”…',
        ))
    mag = matins.get("magnification") if isinstance(matins.get("magnification"), dict) else {}
    if mag:
        changes.append(_set_first_piece_and_clear_rest(
            root,
            slot_id="matins.polyeleos.magnification",
            exact_text='Megalynarion[Minai.]“We magnify thee, O holy ___”…',
            replacement=f'Megalynarion [Minai.] “{mag.get("incipit", "")}”…',
        ))
    sessionals = matins.get("sessionals") if isinstance(matins.get("sessionals"), list) else []
    exacts = [
        '⮡[1st chant/Psalt.,T.___]“”…',
        '⮡[2nd chant/Psalt.,T.___]“”…',
        '“Glory”…“Now”…*⮡[aft.Polyelei,T.___]“”…',
    ]
    for item, exact in zip(sessionals, exacts):
        if not isinstance(item, dict):
            continue
        changes.append(_replace_text_across_pieces(
            root,
            slot_id=f'matins.sessional.{item.get("slot", "unknown")}',
            exact_text=exact,
            replacements=[
                ("___", str(item.get("tone", ""))),
                ('“”…', f'“{item.get("incipit", "")}”…'),
            ],
        ))
    exap = matins.get("exapostilaria") if isinstance(matins.get("exapostilaria"), dict) else {}
    if exap:
        changes.append(_replace_text_across_pieces(
            root,
            slot_id="matins.exapostilaria.glory",
            exact_text='“Glory”… [Minai.] “”…',
            replacements=[('“”…', f'“{exap.get("glory_incipit", "")}”…')],
        ))
    return changes


def _fill_peter_paul_kanon(root: etree._Element, slots: dict[str, Any]) -> list[SlotChange]:
    canon = get_path(slots, "matins", "canon")
    if not isinstance(canon, dict):
        return []
    allocation = canon.get("allocation") if isinstance(canon.get("allocation"), list) else []
    if len(allocation) != 4:
        return []
    changes: list[SlotChange] = []
    # Keep the total and Resurrection row, then map the remaining three fixed rows to
    # Theotokos / Apostle Peter / Apostle Paul. This is intentionally exact-template-only.
    second, third, fourth = allocation[1], allocation[2], allocation[3]
    changes.append(_set_first_piece_and_clear_rest(
        root,
        slot_id="matins.kanon.compact_allocation.theotokos",
        exact_text='1 Cross/Resurr.⮡“Glory to Thy precious Cross& Resurrection, O Lord”',
        replacement=f'{second.get("count")} {second.get("label")} ⮡ “{second.get("refrain")}”',
    ))
    changes.append(_set_first_piece_and_clear_rest(
        root,
        slot_id="matins.kanon.compact_allocation.peter",
        exact_text='1Theotokos⮡“Most Holy Theotokos, save us”',
        replacement=f'{third.get("count")} {third.get("label")} [{third.get("source")}] “{third.get("refrain")}”',
    ))
    changes.append(_replace_text_across_pieces(
        root,
        slot_id="matins.kanon.compact_allocation.paul",
        exact_text='3___ [Minai.] “___, pray to God for us”',
        replacements=[
            ("3", str(fourth.get("count", ""))),
            ("___", f" {fourth.get("label", "")}"),
            ("___", str(fourth.get("refrain", "")).replace(", pray to God for us", "")),
        ],
    ))
    after = canon.get("after_ode_iii") if isinstance(canon.get("after_ode_iii"), dict) else {}
    if after:
        changes.append(_replace_text_across_pieces(
            root,
            slot_id="matins.kanon.after_ode_iii.kontakion",
            exact_text='Kontak.[Minai.,aft. Ode VI,T.___]“”…',
            replacements=[
                ("___", str(after.get("kontakion_tone", ""))),
                ('“”…', f'“{after.get("kontakion_incipit", "")}”…'),
            ],
        ))
        changes.append(_replace_text_across_pieces(
            root,
            slot_id="matins.kanon.after_ode_iii.ikos",
            exact_text='+ Ichos “”…',
            replacements=[('“”…', f'“{after.get("ikos_incipit", "")}”…')],
        ))
        changes.append(_replace_text_across_pieces(
            root,
            slot_id="matins.kanon.after_ode_iii.hypakoe",
            exact_text='Sess. hymn ⮡[aft. Ode III,T.___]“”…',
            replacements=[
                ("___", str(after.get("hypakoe_tone", ""))),
                ('“”…', f'“{after.get("hypakoe_incipit", "")}”…'),
            ],
        ))
    return changes


def _fill_peter_paul_praises(root: etree._Element, slots: dict[str, Any]) -> list[SlotChange]:
    praises = get_path(slots, "praises") or get_path(slots, "matins", "praises")
    if not isinstance(praises, dict):
        return []
    changes: list[SlotChange] = []
    changes.append(_replace_text_across_pieces(
        root,
        slot_id="praises.total",
        exact_text='Lauds / Praises [Orolog.,p.75] ___ total',
        replacements=[("___ total", str(praises.get("total", "")))],
    ))
    changes.append(_replace_text_across_pieces(
        root,
        slot_id="praises.oktoichos_count",
        exact_text='___ [Oktoich.,T.V] “O Lord, when the tomb had been sealed by the”…',
        replacements=[("___", str(praises.get("oktoichos_count", "")))],
    ))
    changes.append(_replace_text_across_pieces(
        root,
        slot_id="praises.minaion_count",
        exact_text='___ [Minai.,T.___] “”…',
        replacements=[
            ("___", str(praises.get("minaion_count", ""))),
            ("___", str(praises.get("minaion_tone", ""))),
            ('“”…', f'“{praises.get("minaion_incipit", "")}”…'),
        ],
    ))
    verses = praises.get("stichoi_for_7_and_8") if isinstance(praises.get("stichoi_for_7_and_8"), list) else []
    if len(verses) >= 2:
        changes.append(_set_first_matching_piece_and_clear_rest(root, slot_id="praises.stichos_7", exact_text='“”', replacement=f'“{verses[0]}”'))
        changes.append(_set_first_matching_piece_and_clear_rest(root, slot_id="praises.stichos_8", exact_text='“”', replacement=f'“{verses[1]}”'))
    return changes


def _fill_peter_paul_hours_and_liturgy(root: etree._Element, slots: dict[str, Any]) -> list[SlotChange]:
    changes: list[SlotChange] = []
    hours = get_path(slots, "hours")
    if isinstance(hours, dict):
        changes.append(_replace_first_text_across_pieces(
            root,
            slot_id="hours.troparia.1_6.apostles",
            exact_text='[Minai.]“”…',
            replacements=[('“”…', f'“{hours.get("apostle_troparion", "")}”…')],
        ))
        changes.append(_replace_first_text_across_pieces(
            root,
            slot_id="hours.troparia.3.apostles",
            exact_text='[Minai.]“”…',
            replacements=[('“”…', f'“{hours.get("apostle_troparion", "")}”…')],
        ))
        changes.append(_replace_text_across_pieces(
            root,
            slot_id="hours.kontakia.alternating_apostles",
            exact_text='Kontak. ⮡ “”…',
            replacements=[('“”…', f'“{hours.get("apostle_kontakion", "")}”…')],
        ))
    liturgy = get_path(slots, "liturgy")
    if isinstance(liturgy, dict):
        changes.append(_replace_text_across_pieces(
            root,
            slot_id="liturgy.beatitudes.total",
            exact_text='Beatitudes: [Orolog.,p.136]___ total',
            replacements=[("___ total", f'{liturgy.get("beatitudes_total", "")} total')],
        ))
        changes.append(_replace_text_across_pieces(
            root,
            slot_id="liturgy.beatitudes.oktoichos_count",
            exact_text='___ [Oktoich.,T.V] “Believing Thee to be God, O Christ, the thief on”…',
            replacements=[("___", str(liturgy.get("oktoichos_beatitudes", "")))],
        ))
        peter = liturgy.get("peter_beatitudes") if isinstance(liturgy.get("peter_beatitudes"), dict) else {}
        paul = liturgy.get("paul_beatitudes") if isinstance(liturgy.get("paul_beatitudes"), dict) else {}
        exact_beat = '4[Minai.,Ode ___]“”…'
        if peter:
            changes.append(_replace_text_across_pieces(
                root,
                slot_id="liturgy.beatitudes.peter",
                exact_text=exact_beat,
                replacements=[
                    ("___", str(peter.get("ode", ""))),
                    ('“”…', f'“{peter.get("incipit", "")}”…'),
                ],
            ))
        if paul:
            new_row = _clone_row_after_exact_paragraph(root, slot_id="liturgy.beatitudes.paul", exact_text=f'4[Minai.,Ode {peter.get("ode", "")}]“{peter.get("incipit", "")}”…')
            _replace_in_subtree(new_row, [(str(peter.get("ode", "")), str(paul.get("ode", ""))), (str(peter.get("incipit", "")), str(paul.get("incipit", "")))])
            changes.append(SlotChange("liturgy.beatitudes.paul", exact_beat, f'4 [Minai.,Ode {paul.get("ode", "")}] “{paul.get("incipit", "")}”…'))
        changes.append(_replace_first_text_across_pieces(
            root,
            slot_id="liturgy.second_prokeimenon",
            exact_text='2nd[Minai.,T.___]“”…',
            replacements=[
                ("___", str(liturgy.get("second_prokeimenon_tone", ""))),
                ('“”…', f'“{liturgy.get("second_prokeimenon_incipit", "")}”…'),
            ],
        ))
        changes.append(_replace_first_text_across_pieces(
            root,
            slot_id="liturgy.second_alleluia",
            exact_text='2nd[Minai.,T.___]“”…',
            replacements=[
                ("___", str(liturgy.get("second_alleluia_tone", ""))),
                ('“”…', f'“{liturgy.get("second_alleluia_incipit", "")}”…'),
            ],
        ))
        changes.append(_replace_text_across_pieces(
            root,
            slot_id="liturgy.second_communion",
            exact_text='“”…',
            replacements=[('“”…', f'“{liturgy.get("second_communion_incipit", "")}”…')],
        ))
    return changes


def fill_reviewed_body_slots(root: etree._Element, overlay: dict[str, Any]) -> list[SlotChange]:
    slots = print_slots(overlay)
    if not slots:
        return []
    changes: list[SlotChange] = []
    changes.extend(_fill_peter_paul_vespers(root, slots))
    changes.extend(_fill_peter_paul_matins(root, slots))
    changes.extend(_fill_peter_paul_kanon(root, slots))
    changes.extend(_fill_peter_paul_praises(root, slots))
    changes.extend(_fill_peter_paul_hours_and_liturgy(root, slots))
    return changes


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

    changes.extend(fill_reviewed_body_slots(root_xml, overlay))

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
