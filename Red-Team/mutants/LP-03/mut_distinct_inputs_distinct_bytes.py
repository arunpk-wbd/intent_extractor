"""MUTANT: constant canonical output for every valid document.

Defect: returns a fixed byte string for all structurally complete inputs,
erasing content distinctions while staying deterministic. Should fail only
test_lp03_distinct_inputs_distinct_bytes.
"""

from __future__ import annotations

from intent_extractor.parsed_document import ParsedDocument

EXPECTED_FAIL = ["test_lp03_distinct_inputs_distinct_bytes"]

_FIXED = b"lp03-mutant-constant-canonical-v1"


def _require_complete(doc: ParsedDocument) -> None:
    if doc.body is None:
        raise ValueError("ParsedDocument.body must not be null")
    if doc.headers is None:
        raise ValueError("ParsedDocument.headers must not be null")
    if doc.attachments is None:
        raise ValueError("ParsedDocument.attachments must not be null")


def canonicalize(doc: ParsedDocument) -> bytes:
    if doc is None or not isinstance(doc, ParsedDocument):
        raise TypeError(
            f"canonicalize expects ParsedDocument, got {type(doc).__name__}"
        )
    _require_complete(doc)
    return _FIXED  # defect: ignore logical content
