from pathlib import Path

from outline_gen.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_generate_fixtures_writes_all_manifest_outputs(tmp_path: Path):
    outdir = tmp_path / "generated-fixtures"
    rc = main([
        "generate-fixtures",
        "--root",
        str(ROOT),
        "--manifest",
        str(ROOT / "registries" / "live_fixture_manifest_v2.yaml"),
        "--outdir",
        str(outdir),
    ])
    assert rc == 0
    expected_ids = {
        "tone_ii_gm_theodorou_six_stichira_2026_06_08",
        "tone_iv_hm_efsevios_simple_2026_06_22",
        "tone_iii_st_iona_polyeleos_2026_06_28",
    }
    for fid in expected_ids:
        assert (outdir / fid / "outline.odt").exists()
    summary = (outdir / "generated_fixture_summary.md").read_text(encoding="utf-8")
    for fid in expected_ids:
        assert fid in summary
    assert "bare var incipit" in summary
