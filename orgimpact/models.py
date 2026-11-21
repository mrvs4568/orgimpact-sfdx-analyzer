from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

Status = Literal["added", "modified", "deleted"]


@dataclass(frozen=True)
class Component:
    id: str
    kind: str
    name: str
    paths: tuple[str, ...]

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Reference:
    source: str
    target: str
    relation: str
    path: str
    line: int | None = None

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Snapshot:
    components: dict[str, Component] = field(default_factory=dict)
    references: list[Reference] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "components": [c.as_dict() for c in sorted(self.components.values(), key=lambda c: c.id)],
            "references": [e.as_dict() for e in sorted(self.references, key=lambda e: (e.source, e.target, e.relation, e.path))],
            "warnings": self.warnings,
        }


@dataclass(frozen=True)
class Change:
    path: str
    status: Status

    def as_dict(self) -> dict:
        return asdict(self)
