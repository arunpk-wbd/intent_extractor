"""Deterministic canonical byte serialization for parsed documents (LP-03).

Implements ``canonicalize`` per ``contracts/LP-03-canonical-determinism.md`` §2
(seam) and §4: a pure, total function of ``ParsedDocument`` whose output is
byte-identical on repeat and across host locale, timezone, randomness, unordered
field iteration order, and construction path — logically equal documents yield
equal bytes and content distinctions are preserved.
"""

from __future__ import annotations

import struct

from intent_extractor.parsed_document import ParsedDocument

_CANONICAL_VERSION = 1
_UTF8 = "utf-8"


def _require_complete(doc: ParsedDocument) -> None:
    """Reject structurally incomplete documents (contract §5)."""
    if doc.body is None:
        raise ValueError("ParsedDocument.body must not be None")
    if doc.headers is None:
        raise ValueError("ParsedDocument.headers must not be None")
    if doc.attachments is None:
        raise ValueError("ParsedDocument.attachments must not be None")
    if not isinstance(doc.body, str):
        raise ValueError("ParsedDocument.body must be a str")
    if not isinstance(doc.headers, dict):
        raise ValueError("ParsedDocument.headers must be a dict")
    if not isinstance(doc.attachments, tuple):
        raise ValueError("ParsedDocument.attachments must be a tuple")


def _encode_text(text: str) -> bytes:
    return text.encode(_UTF8)


def _attachment_sort_key(item: tuple[str, bytes]) -> tuple[str, bytes]:
    name, payload = item
    return (name, payload)


def _serialize(doc: ParsedDocument) -> bytes:
    chunks: list[bytes] = [struct.pack(">B", _CANONICAL_VERSION)]

    body_bytes = _encode_text(doc.body)
    chunks.append(struct.pack(">I", len(body_bytes)))
    chunks.append(body_bytes)

    header_items = sorted(doc.headers.items(), key=lambda kv: kv[0])
    chunks.append(struct.pack(">I", len(header_items)))
    for key, value in header_items:
        key_b = _encode_text(key)
        val_b = _encode_text(value)
        chunks.append(struct.pack(">II", len(key_b), len(val_b)))
        chunks.append(key_b)
        chunks.append(val_b)

    attachments = sorted(doc.attachments, key=_attachment_sort_key)
    chunks.append(struct.pack(">I", len(attachments)))
    for name, payload in attachments:
        name_b = _encode_text(name)
        chunks.append(struct.pack(">II", len(name_b), len(payload)))
        chunks.append(name_b)
        chunks.append(payload)

    return b"".join(chunks)


def canonicalize(doc: ParsedDocument) -> bytes:
    """Return the canonical byte serialization of a parsed document.

    Pure function of ``doc``'s logical content: repeated calls and independent
    constructions of equal documents yield identical bytes (contract §4).

    Args:
        doc: A structurally complete ``ParsedDocument`` (contract §3).

    Returns:
        Deterministic ``bytes`` identity for ``doc``.

    Raises:
        TypeError: If ``doc`` is ``None`` or not a ``ParsedDocument`` (§5).
        ValueError: If ``doc`` is a ``ParsedDocument`` but a required field is
            missing in the sense of ``None`` or wrong container type (§5).
    """
    if doc is None:
        raise TypeError("canonicalize expects ParsedDocument, got None")
    if type(doc) is not ParsedDocument:
        raise TypeError(
            f"canonicalize expects ParsedDocument, got {type(doc).__name__}"
        )

    _require_complete(doc)
    return _serialize(doc)
