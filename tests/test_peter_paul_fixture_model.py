from pathlib import Path
from zipfile import ZipFile

import yaml
from lxml import etree

from outline_gen.cli import main
from outline_gen.service_schema import validate_service_overlay

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "services" / "fixtures" / "2026-06-29-tone-v-peter-paul.yaml"
TEXT_NS = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"


def odt_paragraphs(path: Path) -> list[str]:
    root = etree.fromstring(ZipFile(path).read("content.xml"))
    paragraphs = []
    for p in root.xpath("//text:p|//text:h", namespaces={"text": TEXT_NS}):
        text = " ".join("".join(p.itertext()).split())
        if text:
            paragraphs.append(text)
    return paragraphs


def test_peter_paul_overlay_allows_blank_rank_marker_and_keeps_compact_kanon():
    result = validate_service_overlay(SERVICE)
    assert result.ok, result.to_dict()

    data = yaml.safe_load(SERVICE.read_text(encoding="utf-8"))
    assert data["service"]["service_shape"] == "sunday_major_feast_merge"
    assert data["service"]["ods_rank"] == ""
    assert data["service"]["rank_label"] == ""
    assert data["service"]["rank_marker_policy"] == "blank_for_major_sunday_feast_merge"
    assert data["print_profile"]["kanon_compact_total"] == 6
    assert data["shape_rules_exercised"]["canon"]["compact_total"] == 6
    assert sum(item["count"] for item in data["shape_rules_exercised"]["canon"]["allocation"]) == 6


def test_peter_paul_safe_header_slot_fill_with_blank_rank_marker(tmp_path: Path):
    out = tmp_path / "peter-paul.odt"
    rc = main(["generate", "--root", str(ROOT), "--service", str(SERVICE), "--out", str(out), "--audit"])
    assert rc == 0

    paragraphs = odt_paragraphs(out)
    assert "App. Peter + Paul" in paragraphs
    assert "Matins Gospel VI: Lk 24:36-53 (§114)" in paragraphs
    assert "[ §___ – ___ svc ]" not in paragraphs
    assert "[ §1e – Vigil-rank svc ]" not in paragraphs
    assert "[ §1f2 – Polyeleos/Vigil-rank svc ]" not in paragraphs
    assert "Matins Gospel VI [Lk 24:36-53 (§114)] “At that time, Jesus rose from the dead,”…" in paragraphs

    audit = out.with_suffix(".audit.md").read_text(encoding="utf-8")
    assert "slot_fill_count: 10" in audit
    assert "bare_var_incipit_count: 0" in audit
