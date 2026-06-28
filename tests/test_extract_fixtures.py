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


def test_tone_v_peter_paul_sunday_major_feast_extraction():
    base = "2026-06-29-tone-v-peter-paul"
    rubrics = extract_rubrics_facts(fixture_path(base, "rubrics.htm"))
    liturgy = extract_liturgy_facts(fixture_path(base, "liturgy.htm"))
    minaion = extract_minaion_facts(fixture_path(base, "minaion.odt"))

    assert rubrics.title == "Ss. Peter and Paul"
    assert rubrics.tone == "V"
    assert rubrics.lord_i_cried_total == 10
    assert rubrics.lord_i_cried_oktoichos == 4
    assert rubrics.lord_i_cried_minaion == 6
    assert rubrics.readings_count == 3
    assert rubrics.litia is True
    assert rubrics.polyeleos is True
    assert rubrics.matins_gospel_number in {"6", "VI"}
    assert rubrics.matins_gospel_reference == "Luke 24:36-53 (§114)"
    assert rubrics.praises_total == 8
    assert rubrics.praises_oktoichos == 4
    assert rubrics.praises_minaion == 4
    assert rubrics.praises_final_two_psalm_verses is True

    assert liturgy.beatitudes_total == 12
    assert liturgy.beatitudes_oktoichos == 4
    assert liturgy.beatitudes_peter == 4
    assert liturgy.beatitudes_paul == 4
    assert liturgy.second_prokeimenon is True
    assert liturgy.second_alleluia is True
    assert liturgy.second_epistle is True
    assert liturgy.second_gospel is True
    assert liturgy.second_communion is True

    assert minaion.has_vespers_readings is True
    assert minaion.has_polyeleos_material is True
    assert minaion.has_saint_exapostilarion is True
