from pathlib import Path

import pytest

from outline_gen.service_schema import validate_service_overlay

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("path", sorted((ROOT / "services" / "fixtures").glob("*.yaml")))
def test_fixture_service_overlays_validate(path: Path):
    if not path.exists():
        pytest.skip("fixture service overlays not present")
    result = validate_service_overlay(path)
    assert result.ok, result.to_dict()
