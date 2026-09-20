"""MUTANT: treats the valid empty document as an error.

Defect: raises ValueError when body is empty-but-present with no attachments,
contrary to §5 defined behavior. Should fail only test_lp03_empty_document_canonical.
"""

from __future__ import annotations

from intent_extractor.parsed_document import ParsedDocument

EXPECTED_FAIL = ["test_lp03_empty_document_canonical"]


def _require_complete(doc: ParsedDocument) -> None:
    if doc.body is None:
        raise ValueError("ParsedDocument.body must not be null")
    if doc.headers is None:
        raise ValueError("ParsedDocument.headers must not be null")
    if doc.attachments is None:
        raise ValueError("ParsedDocument.attachments must not be null")


def _serialize(doc: ParsedDocument) -> bytes:
    chunks: list[bytes] = [b"body:\n", doc.body.encode("utf-8"), b"\nheaders:\n"]
    for key in sorted(doc.headers):
        value = doc.headers[key]
        chunks.extend(
            (key.encode("utf-8"), b"=", value.encode("utf-8"), b"\n")
        )
    chunks.append(b"attachments:\n")
    for name, payload in sorted(doc.attachments, key=lambda item: (item[0], item[1])):
        chunks.extend((name.encode("utf-8"), b"\0", payload, b"\n"))
    return b"".join(chunks)


def canonicalize(doc: ParsedDocument) -> bytes:
    if doc is None or not isinstance(doc, ParsedDocument):
        raise TypeError(
            f"canonicalize expects ParsedDocument, got {type(doc).__name__}"
        )
    _require_complete(doc)
    if doc.body == "" and not doc.attachments:
        raise ValueError("empty document rejected")  # defect: §5 empty is valid
    return _serialize(doc)
