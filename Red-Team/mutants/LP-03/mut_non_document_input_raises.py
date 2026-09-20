"""MUTANT: accepts wrong-typed input instead of raising TypeError.

Defect: drops the ParsedDocument type guard and coerces any mapping-like or
other object into bytes, so None and stand-ins never raise TypeError. Should
fail only test_lp03_non_document_input_raises.
"""

from __future__ import annotations

from intent_extractor.parsed_document import ParsedDocument

EXPECTED_FAIL = ["test_lp03_non_document_input_raises"]


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
    if isinstance(doc, ParsedDocument):
        _require_complete(doc)
        return _serialize(doc)
    # defect: wrong types silently canonicalized
    return repr(doc).encode("utf-8")
