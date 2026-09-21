"""Ungoverned stand-in for the ComponentRegistry seam dependency (LP-04).

Hand-written stub — NOT governed by a contract, mirroring the pattern of
`parsed_document.py` (committed as addba5d) so the LP-04 reference/verifier can
import and construct the seam's parameter type before `src/` proper exists.

Design ruling (LP-04 §7a): PERMISSIVE by construction.
  * Component ids are NOT de-duplicated — a registry CAN hold two components with
    the same id. The duplicate-id invariant therefore lives in the *governed*
    seam (`intent_extractor.component_versions`), not in this ungoverned stub,
    and `duplicate_component_raises` stays a testable §7 case.
  * A component's version may be None or "" (undeclared) so the seam's
    `missing_version_raises` case is constructible.
  * Parsers and OCR engines are distinguishable (via `kind`) so the seam's
    `every_parser_present` / `every_ocr_engine_present` cases are observable.
  * An empty registry is representable (`empty_registry_empty_manifest`).

If a later decision makes the registry de-duplicate at construction, flip
`register()` to reject/collapse duplicates and move `duplicate_component_raises`
from §7 to a §5 (undefined-behavior) note — but then that invariant would sit in
this ungoverned stub, which is why the ruling above keeps it in the seam.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator, List, Optional


class ComponentKind(Enum):
    PARSER = "parser"
    OCR = "ocr"


@dataclass(frozen=True)
class Component:
    """A registered document-processing component.

    `version` is Optional: None or "" represents an undeclared version, which the
    governed seam must reject (missing_version_raises).
    """

    id: str
    version: Optional[str]
    kind: ComponentKind


@dataclass
class ComponentRegistry:
    """Ordered collection of registered components. No de-duplication by design."""

    components: List[Component] = field(default_factory=list)

    def register(self, component: Component) -> None:
        # No dedup: duplicate ids are permitted so the seam can raise on them.
        self.components.append(component)

    def parsers(self) -> List[Component]:
        return [c for c in self.components if c.kind is ComponentKind.PARSER]

    def ocr_engines(self) -> List[Component]:
        return [c for c in self.components if c.kind is ComponentKind.OCR]

    def __iter__(self) -> Iterator[Component]:
        return iter(self.components)

    def __len__(self) -> int:
        return len(self.components)
