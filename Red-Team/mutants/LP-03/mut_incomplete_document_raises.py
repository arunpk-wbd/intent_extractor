"""MUTANT: tolerates structurally incomplete ParsedDocument (body is None).

Defect: skips the completeness check and serializes null body as empty text,
returning bytes instead of raising ValueError per §5. Should fail only
test_lp03_incomplete_document_raises.
"""

from __future__ import annotations

from intent_extractor.parsed_document import ParsedDocument

EXPECTED_FAIL = ["test_lp03_incomplete_document_raises"]


def _serialize(doc: ParsedDocument) -> bytes:
    body = "" if doc.body is None else doc.body
    headers = doc.headers if doc.headers is not None else {}
    attachments = doc.attachments if doc.attachments is not None else ()
    chunks: list[bytes] = [b"body:\n", body.encode("utf-8"), b"\nheaders:\n"]
    for key in sorted(headers):
        value = headers[key]
        chunks.extend(
            (key.encode("utf-8"), b"=", value.encode("utf-8"), b"\n")
        )
    chunks.append(b"attachments:\n")
    for name, payload in sorted(attachments, key=lambda item: (item[0], item[1])):
        chunks.extend((name.encode("utf-8"), b"\0", payload, b"\n"))
    return b"".join(chunks)


def canonicalize(doc: ParsedDocument) -> bytes:
    if doc is None or not isinstance(doc, ParsedDocument):
        raise TypeError(
            f"canonicalize expects ParsedDocument, got {type(doc).__name__}"
        )
    # defect: no ValueError on incomplete fields
    return _serialize(doc)
