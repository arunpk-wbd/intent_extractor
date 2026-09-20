"""LP-03 · S-01 — Canonical document determinism (PROPERTY, no goldens).

Contract under test: contracts/LP-03-canonical-determinism.md (v0.5; ADR-0015,
ADR-0024, ADR-0030).

Seam under test (contract §2):
    from intent_extractor.canonical import canonicalize
    def canonicalize(doc: ParsedDocument) -> bytes: ...

Invariant (contract §4):
    Pure, total function of ParsedDocument; byte-identical on repeat and across
    environment; order/locale/TZ/randomness/construction-path independent;
    logically equal -> equal bytes; logically distinct -> distinct bytes.

RED-first (ADR-0004): `canonicalize` is imported INSIDE each test body so its
absence is a clean assertion failure, never a collection error.

Fixture-free: no golden byte strings. ParsedDocument witnesses use only the
fields named in the contract (body, headers, attachments).
"""

from __future__ import annotations

import os
import pickle
import random
import subprocess
import sys
from datetime import datetime, timezone

import pytest

SEED = 20260903
N_INPUTS = 200

_TZ_VALUES = ("UTC", "America/New_York", "Asia/Kolkata")
_LOCALE_VALUES = ("C", "de_DE.UTF-8")
_HASHSEED_VALUES = ("0", "1", "random")

_BOUNDARY_BODY_LENGTHS = (999, 1000, 1001)


def _env_triples() -> list[tuple[str, str, str]]:
    triples = [
        (tz, loc, hs)
        for tz in _TZ_VALUES
        for loc in _LOCALE_VALUES
        for hs in _HASHSEED_VALUES
    ]
    assert len(triples) == 18
    return triples


def _assign_env_legs(n: int) -> list[tuple[str, str, str]]:
    triples = _env_triples()
    out = list(triples)
    while len(out) < n:
        out.append(triples[len(out) % len(triples)])
    return out[:n]


def _witness_headers(rng: random.Random, idx: int) -> dict[str, str]:
    num = rng.randint(100_000, 9_999_999)
    when = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc).isoformat()
    keys = [
        ("x-amount", str(num)),
        ("x-sent-at", when),
        ("x-index", str(idx)),
        ("x-token", rng.choice(["alpha", "beta", "gamma"])),
    ]
    rng.shuffle(keys)
    return {k: v for k, v in keys}


def _attachment_pair(rng: random.Random, tag: str) -> tuple[str, bytes]:
    name = f"{tag}-{rng.randint(0, 9999)}.bin"
    payload = f"payload-{tag}-{rng.randint(0, 1_000_000)}".encode()
    return (name, payload)


def _make_body(rng: random.Random, target_len: int, idx: int) -> str:
    num = rng.randint(10_000, 9_999_999)
    when = datetime(2024, 9, 20, 8, 21, tzinfo=timezone.utc).isoformat()
    tail = f" amount={num} sent={when} seq={idx} end."
    if target_len <= len(tail):
        return (tail * ((target_len // len(tail)) + 1))[:target_len]
    pad_len = target_len - len(tail)
    return ("p" * pad_len) + tail


def _build_document(rng: random.Random, idx: int, body_len: int, ParsedDocument):
    att_a = _attachment_pair(rng, "a")
    att_b = _attachment_pair(rng, "b")
    if rng.random() < 0.5:
        attachments = (att_a, att_b)
    else:
        attachments = (att_b, att_a)
    return ParsedDocument(
        body=_make_body(rng, body_len, idx),
        headers=_witness_headers(rng, idx),
        attachments=attachments,
    )


def _generate_corpus(rng: random.Random, ParsedDocument) -> list:
    docs = []
    for i, blen in enumerate(_BOUNDARY_BODY_LENGTHS):
        docs.append(_build_document(rng, i, blen, ParsedDocument))
    for idx in range(len(_BOUNDARY_BODY_LENGTHS), N_INPUTS):
        body_len = rng.randint(1001, 1400)
        docs.append(_build_document(rng, idx, body_len, ParsedDocument))
    assert len(docs) == N_INPUTS
    return docs


def _headers_insertion_permutation(headers: dict[str, str], rng: random.Random) -> dict[str, str]:
    items = list(headers.items())
    rng.shuffle(items)
    reordered: dict[str, str] = {}
    for k, v in items:
        reordered[k] = v
    return reordered


def _attachments_order_permutation(
    attachments: tuple[tuple[str, bytes], ...],
) -> tuple[tuple[str, bytes], ...]:
    if len(attachments) < 2:
        return attachments
    return tuple(reversed(attachments))


def _rebuild_equivalent(doc, ParsedDocument):
    half = len(doc.body) // 2
    body = doc.body[:half] + doc.body[half:]
    headers: dict[str, str] = {}
    for key in reversed(list(doc.headers)):
        headers[key] = doc.headers[key]
    attachments = tuple(reversed(doc.attachments))
    return ParsedDocument(body=body, headers=headers, attachments=attachments)


def _apply_hashseed(env: dict[str, str], hashseed: str) -> None:
    if hashseed == "random":
        env.pop("PYTHONHASHSEED", None)
    else:
        env["PYTHONHASHSEED"] = hashseed


def _subprocess_canonicalize(
    doc,
    *,
    tz: str | None = None,
    locale_name: str | None = None,
    hashseed: str | None = None,
    activate_locale: bool = False,
) -> bytes:
    env = os.environ.copy()
    if tz is not None:
        env["TZ"] = tz
    if locale_name is not None:
        env["LC_ALL"] = locale_name
    if hashseed is not None:
        _apply_hashseed(env, hashseed)
    if activate_locale:
        env["_LP03_ACTIVATE_LOCALE"] = "1"
    else:
        env.pop("_LP03_ACTIVATE_LOCALE", None)

    worker = """
import locale
import os
import pickle
import sys

if os.environ.get("_LP03_ACTIVATE_LOCALE") == "1":
    locale.setlocale(locale.LC_ALL, "")

from intent_extractor.canonical import canonicalize

doc = pickle.loads(sys.stdin.buffer.read())
sys.stdout.buffer.write(canonicalize(doc))
"""
    proc = subprocess.run(
        [sys.executable, "-c", worker],
        input=pickle.dumps(doc, protocol=pickle.HIGHEST_PROTOCOL),
        env=env,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        err = proc.stderr.decode(errors="replace")
        pytest.fail(
            "subprocess canonicalize failed "
            f"(tz={tz!r} locale={locale_name!r} hashseed={hashseed!r}): {err}"
        )
    return proc.stdout


def _hashseed_differs_from_baseline(subprocess_seed: str, baseline_seed: str | None) -> bool:
    if subprocess_seed == "random":
        return baseline_seed is not None
    return baseline_seed != subprocess_seed


def test_lp03_determinism_across_env_matrix():
    try:
        from intent_extractor.canonical import canonicalize
    except ImportError as e:
        pytest.fail(
            "intent_extractor.canonical.canonicalize not implemented yet "
            f"(LP-03 is RED by design; SEED={SEED}): {e}"
        )
    try:
        from intent_extractor.parsed_document import ParsedDocument
    except ImportError as e:
        pytest.fail(
            "intent_extractor.parsed_document.ParsedDocument not available "
            f"(LP-03 depends on LP-01 input type; SEED={SEED}): {e}"
        )

    import locale

    for loc in _LOCALE_VALUES:
        try:
            locale.setlocale(locale.LC_ALL, loc)
        except locale.Error as e:
            pytest.fail(
                f"required locale {loc!r} is not available on this host "
                f"(contract §7a — never skip): {e}"
            )

    rng = random.Random(SEED)
    corpus = _generate_corpus(rng, ParsedDocument)
    env_legs = _assign_env_legs(N_INPUTS)
    baseline_hashseed = os.environ.get("PYTHONHASHSEED")
    saw_hashseed_delta = False

    for idx, doc in enumerate(corpus):
        baseline = canonicalize(doc)

        assert canonicalize(doc) == baseline, (
            f"input #{idx}: in-process repeat differed from baseline "
            f"(SEED={SEED})"
        )

        assert _subprocess_canonicalize(doc) == baseline, (
            f"input #{idx}: fresh subprocess (inherit env) differed (SEED={SEED})"
        )

        assert canonicalize(_rebuild_equivalent(doc, ParsedDocument)) == baseline, (
            f"input #{idx}: construction-path rebuild differed (SEED={SEED})"
        )

        permuted = ParsedDocument(
            body=doc.body,
            headers=_headers_insertion_permutation(doc.headers, rng),
            attachments=_attachments_order_permutation(doc.attachments),
        )
        assert canonicalize(permuted) == baseline, (
            f"input #{idx}: header/attachment insertion-order permute differed "
            f"(SEED={SEED})"
        )

        tz, loc, hs = env_legs[idx]
        assert _subprocess_canonicalize(
            doc,
            tz=tz,
            locale_name=loc,
            hashseed=hs,
            activate_locale=True,
        ) == baseline, (
            f"input #{idx}: env leg TZ={tz!r} locale={loc!r} hashseed={hs!r} "
            f"differed (SEED={SEED})"
        )

        if _hashseed_differs_from_baseline(hs, baseline_hashseed):
            saw_hashseed_delta = True

    if not saw_hashseed_delta:
        doc = corpus[0]
        baseline = canonicalize(doc)
        alt_seed = "1" if baseline_hashseed != "1" else "0"
        assert _subprocess_canonicalize(
            doc,
            tz=_TZ_VALUES[0],
            locale_name=_LOCALE_VALUES[0],
            hashseed=alt_seed,
            activate_locale=True,
        ) == baseline, (
            "hashseed witness subprocess differed from baseline "
            f"(SEED={SEED})"
        )
        saw_hashseed_delta = True

    assert saw_hashseed_delta, (
        "hashseed dimension was not witnessed with a subprocess seed differing "
        f"from baseline (SEED={SEED})"
    )


def test_lp03_distinct_inputs_distinct_bytes():
    try:
        from intent_extractor.canonical import canonicalize
    except ImportError as e:
        pytest.fail(
            "intent_extractor.canonical.canonicalize not implemented yet "
            f"(LP-03 is RED by design; SEED={SEED}): {e}"
        )
    try:
        from intent_extractor.parsed_document import ParsedDocument
    except ImportError as e:
        pytest.fail(
            "intent_extractor.parsed_document.ParsedDocument not available "
            f"(LP-03 depends on LP-01 input type; SEED={SEED}): {e}"
        )

    rng = random.Random(SEED ^ 0x0303)
    base = _build_document(rng, 0, 1100, ParsedDocument)
    other = ParsedDocument(
        body=base.body + "distinct-marker",
        headers=dict(base.headers),
        attachments=base.attachments,
    )

    a = canonicalize(base)
    b = canonicalize(other)
    assert a != b, (
        "logically different documents produced identical canonical bytes "
        f"(SEED={SEED})"
    )


def test_lp03_empty_document_canonical():
    try:
        from intent_extractor.canonical import canonicalize
    except ImportError as e:
        pytest.fail(
            "intent_extractor.canonical.canonicalize not implemented yet "
            f"(LP-03 is RED by design; SEED={SEED}): {e}"
        )
    try:
        from intent_extractor.parsed_document import ParsedDocument
    except ImportError as e:
        pytest.fail(
            "intent_extractor.parsed_document.ParsedDocument not available "
            f"(LP-03 depends on LP-01 input type; SEED={SEED}): {e}"
        )

    result = canonicalize(
        ParsedDocument(body="", headers={}, attachments=())
    )
    assert isinstance(result, bytes), (
        f"empty document must return bytes, got {type(result)!r} (SEED={SEED})"
    )


def test_lp03_non_document_input_raises():
    try:
        from intent_extractor.canonical import canonicalize
    except ImportError as e:
        pytest.fail(
            "intent_extractor.canonical.canonicalize not implemented yet "
            f"(LP-03 is RED by design; SEED={SEED}): {e}"
        )

    with pytest.raises(TypeError):
        canonicalize(None)

    with pytest.raises(TypeError):
        canonicalize(object())

    with pytest.raises(TypeError):
        canonicalize({"body": "", "headers": {}, "attachments": ()})


def test_lp03_incomplete_document_raises():
    try:
        from intent_extractor.canonical import canonicalize
    except ImportError as e:
        pytest.fail(
            "intent_extractor.canonical.canonicalize not implemented yet "
            f"(LP-03 is RED by design; SEED={SEED}): {e}"
        )
    try:
        from intent_extractor.parsed_document import ParsedDocument
    except ImportError as e:
        pytest.fail(
            "intent_extractor.parsed_document.ParsedDocument not available "
            f"(LP-03 depends on LP-01 input type; SEED={SEED}): {e}"
        )

    with pytest.raises(ValueError):
        canonicalize(ParsedDocument(body=None, headers={}, attachments=()))
