from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import yaml

TONE_VALUES = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "1", "2", "3", "4", "5", "6", "7", "8"}
RANK_VALUES = {"§1a", "§1b", "§1c", "§1d", "§1e", "§1f"}
GOSPEL_VALUES = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"}


@dataclass
class ValidationResult:
    path: str
    ok: bool
    errors: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def _rank(service: dict[str, Any]) -> Any:
    return service.get("ods_rank") or service.get("proposed_ods_rank") or service.get("rank")


def validate_service_overlay(path: Path) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        data = load_yaml(path)
    except Exception as e:
        return ValidationResult(str(path), False, [str(e)], [])

    service = data.get("service")
    if not isinstance(service, dict):
        return ValidationResult(str(path), False, ["missing required mapping: service"], [])

    for key in ["date", "title", "week_tone"]:
        if not service.get(key):
            errors.append(f"service.{key} is required")

    tone = str(service.get("week_tone", "")).strip()
    if tone and tone not in TONE_VALUES:
        errors.append(f"service.week_tone has unsupported value: {tone!r}")

    mg = service.get("matins_gospel")
    if not isinstance(mg, dict):
        errors.append("service.matins_gospel mapping is required")
    else:
        for key in ["number", "reference"]:
            if not mg.get(key):
                errors.append(f"service.matins_gospel.{key} is required")
        number = str(mg.get("number", "")).strip()
        if number and number not in GOSPEL_VALUES:
            warnings.append(f"service.matins_gospel.number is unusual: {number!r}")
        if not mg.get("section"):
            warnings.append("service.matins_gospel.section is missing; useful for review provenance")

    rank = _rank(service)
    if not rank:
        errors.append("service.ods_rank or service.proposed_ods_rank is required")
    elif str(rank).strip() not in RANK_VALUES:
        warnings.append(f"service rank is unusual: {rank!r}")

    if not service.get("rank_label"):
        errors.append("service.rank_label is required")

    if "source_inputs" not in data:
        warnings.append("source_inputs missing; extraction provenance will be weaker")
    elif not isinstance(data.get("source_inputs"), dict):
        errors.append("source_inputs must be a mapping when present")

    has_shape_rules = isinstance(data.get("shape_rules_exercised"), dict)
    has_slot_overrides = isinstance(data.get("slot_overrides"), dict)
    if not has_shape_rules and not has_slot_overrides:
        warnings.append("neither shape_rules_exercised nor slot_overrides is present")

    return ValidationResult(str(path), not errors, errors, warnings)


def validate_many(paths: list[Path]) -> list[ValidationResult]:
    return [validate_service_overlay(p) for p in paths]


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(prog="tone9-validate-service")
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    results = validate_many(args.paths)
    if args.json:
        import json
        print(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            print(f"--- {r.path}")
            print(f"ok: {r.ok}")
            for e in r.errors:
                print(f"ERROR: {e}")
            for w in r.warnings:
                print(f"WARN: {w}")
    return 1 if any(not r.ok for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
