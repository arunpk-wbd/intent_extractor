"""ParsedDocument — the parsed-email intermediate produced upstream (LP-01).

This is the INPUT TYPE seam LP-03's verifier binds to: canonicalize(doc: ParsedDocument).
Minimal structural definition sufficient for the LP-03 contract's cases. In a full
build LP-01 owns this; here it is the upstream type seam so LP-03 can be proven.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ParsedDocument:
    """A fully-parsed document: body text, headers, and attachments.

    Fields:
        body: the document body text.
        headers: header name -> value.
        attachments: ordered (filename, bytes) pairs.
    """
    body: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    attachments: tuple[tuple[str, bytes], ...] = ()
