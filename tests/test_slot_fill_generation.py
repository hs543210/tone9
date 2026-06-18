from pathlib import Path
from zipfile import ZipFile

import pytest
from lxml import etree

from outline_gen.cli import main

ROOT = Path(__file__).resolve().parents[1]
TEXT_NS = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"


def odt_paragraphs(path: Path) -> list[str]:
    root = etree.fromstring(ZipFile(path).read("content.xml"))
    paragraphs = []
    for p in root.xpath("//text:p|//text:h", namespaces={"text": TEXT_NS}):
        text = " ".join("".join(p.itertext()).split())
        if text:
            paragraphs.append(text)
    return paragraphs


@pytest.mark.parametrize(
    ("service", "slot_count", "expected"),
    [
        (
            "2026-06-08-tone-ii-theodorou.yaml",
            10,
            [
                "GM Theodórou Stratilátis",
                "Matins Gospel III: Mk 16:9-20 (§71)",
                "[ §1c – 6-stichira svc ]",
                "Matins Gospel III [Mk 16:9-20 (§71)] “At that time, when Jesus was risen early the”…",
                "Exaposteilaria: Matins Gospel III",
                "“Glory”… [Evang. Stichiron III]“When Mary Magdalene announced the”…",
            ],
        ),
        (
            "2026-06-22-tone-iv-efsevios.yaml",
            11,
            [
                "HM Efsévios of Samosata",
                "Matins Gospel V: Lk 24:12-35 (§113)",
                "[ §1a – Simple svc ]",
                "Matins Gospel V [Lk 24:12-35 (§113)] “At that time, Peter arose and ran unto the”…",
                "Exaposteilaria: Matins Gospel V",
                "“Glory”… [Evang. Stichiron V]“O, Thine all-wise judgements, O Christ! How”…",
            ],
        ),
        (
            "2026-06-28-tone-iii-iona-polyeleos.yaml",
            10,
            [
                "St Iona, Metr. Moscow + All Russia",
                "Matins Gospel IV: Lk 24:1-12 (§112)",
                "[ §1d – Polyeleos svc ]",
                "Matins Gospel IV [Lk 24:1-12 (§112)] “At that time, upon the first day of the week,”…",
                "Exaposteilaria: Matins Gospel IV",
                "“Glory”… [Evang. Stichiron IV]“It was very early in the morning, and the”…",
            ],
        ),
    ],
)
def test_generate_fills_first_safe_slots(tmp_path: Path, service: str, slot_count: int, expected: list[str]):
    out = tmp_path / service.replace(".yaml", ".odt")
    rc = main(["generate", "--root", str(ROOT), "--service", str(ROOT / "services" / "fixtures" / service), "--out", str(out), "--audit"])
    assert rc == 0
    paragraphs = odt_paragraphs(out)
    for text in expected:
        assert text in paragraphs

    audit = out.with_suffix(".audit.md").read_text(encoding="utf-8")
    assert f"slot_fill_count: {slot_count}" in audit
    assert "bare_var_incipit_count: 0" in audit


def test_simple_service_explicitly_omits_vespers_readings(tmp_path: Path):
    out = tmp_path / "efsevios.odt"
    rc = main([
        "generate",
        "--root",
        str(ROOT),
        "--service",
        str(ROOT / "services" / "fixtures" / "2026-06-22-tone-iv-efsevios.yaml"),
        "--out",
        str(out),
        "--audit",
    ])
    assert rc == 0
    paragraphs = odt_paragraphs(out)
    assert "3 Readings: [Minai.]“A Reading from ___”…" not in paragraphs
    assert "vespers.readings" in out.with_suffix(".audit.md").read_text(encoding="utf-8")


def test_non_explicit_services_keep_vespers_readings_placeholder_for_now(tmp_path: Path):
    out = tmp_path / "iona.odt"
    rc = main([
        "generate",
        "--root",
        str(ROOT),
        "--service",
        str(ROOT / "services" / "fixtures" / "2026-06-28-tone-iii-iona-polyeleos.yaml"),
        "--out",
        str(out),
    ])
    assert rc == 0
    paragraphs = odt_paragraphs(out)
    assert "3 Readings: [Minai.]“A Reading from ___”…" in paragraphs


def test_generate_rejects_invalid_service_before_writing(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("service:\n  title: Missing required fields\n", encoding="utf-8")
    out = tmp_path / "bad.odt"

    with pytest.raises(SystemExit) as exc:
        main(["generate", "--root", str(ROOT), "--service", str(bad), "--out", str(out)])

    assert exc.value.code == 1
    assert not out.exists()
