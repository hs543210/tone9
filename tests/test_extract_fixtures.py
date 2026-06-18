from pathlib import Path

import pytest

from outline_gen.extract.liturgy_html import extract_liturgy_facts
from outline_gen.extract.rubrics_html import extract_rubrics_facts
from outline_gen.extract.minaion_odt import extract_minaion_facts

ROOT = Path(__file__).resolve().parents[1]


def fixture_path(*parts: str) -> Path:
    p = ROOT.joinpath("fixtures", "source", *parts)
    if not p.exists():
        pytest.skip(f"fixture missing: {p}")
    return p


def test_tone_ii_theodorou_basic_extraction():
    base = "2026-06-08-tone-ii-theodorou"
    rubrics = extract_rubrics_facts(fixture_path(base, "rubrics.htm"))
    liturgy = extract_liturgy_facts(fixture_path(base, "liturgy.htm"))
    minaion = extract_minaion_facts(fixture_path(base, "minaion.odt"))
    assert rubrics.tone == "II"
    assert rubrics.matins_gospel_number in {"3", "III"}
    assert rubrics.polyeleos is False
    assert liturgy.beatitudes_total == 10
    assert liturgy.second_prokeimenon is True
    assert liturgy.second_alleluia is True
    assert liturgy.second_communion is True
    assert minaion.has_saint_exapostilarion is True


def test_tone_iv_efsevios_basic_extraction():
    base = "2026-06-22-tone-iv-efsevios"
    rubrics = extract_rubrics_facts(fixture_path(base, "rubrics.htm"))
    liturgy = extract_liturgy_facts(fixture_path(base, "liturgy.htm"))
    minaion = extract_minaion_facts(fixture_path(base, "minaion.odt"))
    assert rubrics.tone == "IV"
    assert rubrics.polyeleos is False
    assert liturgy.second_prokeimenon is False
    assert liturgy.second_alleluia is False
    assert liturgy.second_communion is False
    assert minaion.has_saint_exapostilarion is False


def test_tone_iii_iona_polyeleos_basic_extraction():
    base = "2026-06-28-tone-iii-iona-polyeleos"
    rubrics = extract_rubrics_facts(fixture_path(base, "rubrics.htm"))
    liturgy = extract_liturgy_facts(fixture_path(base, "liturgy.htm"))
    minaion = extract_minaion_facts(fixture_path(base, "minaion.odt"))
    assert rubrics.tone == "III"
    assert rubrics.polyeleos is True
    assert liturgy.beatitudes_total == 10
    assert liturgy.second_prokeimenon is True
    assert liturgy.second_alleluia is True
    assert liturgy.second_communion is True
    assert minaion.has_polyeleos_material is True
