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
    assert "slot_fill_count:" in audit
    assert "bare_var_incipit_count: 0" in audit


def test_peter_paul_reviewed_body_slots_are_filled(tmp_path: Path):
    out = tmp_path / "peter-paul-body.odt"
    rc = main(["generate", "--root", str(ROOT), "--service", str(SERVICE), "--out", str(out), "--audit"])
    assert rc == 0

    paragraphs = odt_paragraphs(out)

    assert '4 stichira:[Oktoichos,T.V]“By Thy Precious Cross didst Thou put the devil”…' in paragraphs
    assert '6” [Minai.,T.II] “With what wreaths of praise”…' in paragraphs
    assert '“Glory”… ⮡[T.IV] “By His thrice-repeated question”…' in paragraphs
    assert '“Now”… [Minai.,T.VI] “Christ the Lord”…' in paragraphs

    assert 'Megalynarion [Minai.] “We magnify you, O apostles of Christ, Peter and Paul; by your teaching the whole world hath been enlightened, and all the ends of it brought unto Christ”…' in paragraphs
    assert '⮡[1st chant/Psalt.,T.VIII]“Forsaking the fishing of the deep”…' in paragraphs
    assert '⮡[2nd chant/Psalt.,T.VIII]“Receiving from Christ a heavenly calling”…' in paragraphs

    assert '1 Cross/Resurr.⮡“Glory to Thy precious Cross& Resurrection, O Lord”' not in paragraphs
    assert '1 Theotokos ⮡ “Most Holy Theotokos, save us”' in paragraphs
    assert '2 Apostle Peter [Minai.] “Holy Apostle Peter, pray to God for us”' in paragraphs
    assert '2 Apostle Paul [Minai.] “Holy Apostle Paul, pray to God for us”' in paragraphs
    assert 'Kontak.[Minai.,aft. Ode VI,T.II]“Thou hast taken to Thyself, O Lord”…' in paragraphs
    assert '+ Ichos “Fill my tongue with light”…' in paragraphs

    assert 'Lauds / Praises [Orolog.,p.75] 8+2 total' in paragraphs
    assert '4 [Minai.,T.IV] “When the Savior questioned”…' in paragraphs
    assert '“Their sound hath gone forth into all the earth, and their words unto the ends of the world”' in paragraphs
    assert '“The heavens declare the glory of God, and the firmament proclaimeth the work of His hands”' in paragraphs

    assert 'Beatitudes: [Orolog.,p.136]12 total' in paragraphs
    assert '4[Minai.,Ode III]“The sweet mouth of Christ God”…' in paragraphs
    assert '4[Minai.,Ode VI]“Spurning all the beautiful things of the world”…' in paragraphs
    assert '2nd[Minai.,T.VIII]“Their sound hath gone forth”…' in paragraphs
    assert '2nd[Minai.,T.I]“The heavens shall confess Thy wonders, O Lord”…' in paragraphs
    assert '“Their sound hath gone forth”…' in paragraphs
