from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class SlotDefinition:
    id: str
    section: str
    kind: str
    description: str
    default_policy: str = "keep"
    style_rule: str | None = None
    sources: list[str] = field(default_factory=list)


def load_slot_registry(path: Path) -> list[SlotDefinition]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    slots = data.get("slots", [])
    return [SlotDefinition(**slot) for slot in slots]


def slot_ids(path: Path) -> list[str]:
    return [s.id for s in load_slot_registry(path)]


def slots_by_section(path: Path) -> dict[str, list[SlotDefinition]]:
    out: dict[str, list[SlotDefinition]] = {}
    for slot in load_slot_registry(path):
        out.setdefault(slot.section, []).append(slot)
    return out
