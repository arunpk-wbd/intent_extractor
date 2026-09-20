# Contract — LP-03: Canonical document determinism
**File:** `contracts/LP-03-canonical-determinism.md` · **Version:** 0.5 — DRAFT (NOT frozen)
**Layer:** contracts/ (ADR-0015, ADR-0024) · **Authorship:** human-authored judgment (seam + conditions); Planning-drafted body; §7 restructured 2026-09-20 (Claude-drafted, pending ratification); ratify + freeze pending
**Type:** fixture-free property · **Dependencies:** NONE (Wave 0) — the determinism property is self-contained; see §3 for a promise-level upstream assumption on LP-01.
**Epic/Story:** CAP-1 · Document & Record / S-01 · **owns.write:** `src/intent_extractor/canonical.py`

## 1. Promise
Canonicalization reduces a parsed document to a single canonical byte serialization such that the same logical input always produces exactly the same bytes. This byte string is the stable identity that versioning, deduplication, and hashing downstream rely on: if canonicalization is not deterministic, every guarantee built on the canonical form is unsound.

## 2. Seam signature (MANDATORY — human-set against INTENT, not copied from src/)
```
from intent_extractor.canonical import canonicalize

def canonicalize(doc: ParsedDocument) -> bytes: ...
```
This is a pure intent ruling. `ParsedDocument` is the fully-parsed intermediate produced upstream (LP-01). The verifier binds to `canonicalize`; the return is the canonical byte serialization of `doc`. If `src/` does not exist yet, this ruling stands on intent alone. If `src/` exists and differs, that difference is a finding, not the truth.

## 3. Pre-conditions
`doc` is a structurally complete `ParsedDocument`: it is of the declared type and every field required by the parser contract is populated. Callers do not pass partially-constructed or externally-mutated documents.

LP-03 additionally assumes its input is already normalized at the encoding level by upstream parsing (LP-01, "MIME parse to canonical text"): line endings, byte-order mark, and Unicode form are settled before `canonicalize` runs. LP-03 does **not** itself normalize encoding-level equivalences (see §7c ruling); the §1 dedup-identity promise depends on this upstream guarantee holding.

## 4. Post-condition / invariant
`canonicalize` is a pure, total function of its single argument. For any `ParsedDocument` `d`:
- Repeated evaluation yields **byte-identical** results (`canonicalize(d) == canonicalize(d)`), including across process restarts.
- The result is independent of the iteration order of unordered fields (e.g. header maps, attachment sets), host locale, host timezone / wall-clock, any process-level randomness, and the **construction path or object identity** of the argument — two independently constructed, logically-equal documents canonicalize to identical bytes.
- Two documents that are logically equal produce identical bytes; two documents that differ in content produce different bytes (the canonical form preserves, rather than erases, content distinctions).

## 5. Undefined behavior (the error-semantics section)
- `doc` is `None` → raises `TypeError`.
- `doc` is not a `ParsedDocument` (wrong type) → raises `TypeError`.
- `doc` is structurally incomplete — a required field **present but null/empty** (e.g. `body is None`), since a strict `ParsedDocument` dataclass cannot be constructed with a field truly absent → raises `ValueError`; this is outside the contract, not a silently-tolerated input. (The distinction from the wrong-type case above is deliberate: wrong *type* → `TypeError`; right type, *incomplete content* → `ValueError`.)
- `doc` is a valid but empty document — an *empty-but-present* body (`body == ""`) and no attachments → returns the canonical bytes for the empty document; this is defined behavior, not an error. (Contrast the incomplete case above: `body == ""` is valid and returns bytes; `body is None` is incomplete and raises `ValueError`.)

## 6. Determinism
Pure function of its inputs. No wall-clock, locale, network, randomness, or iteration-order dependence. Byte-stable across processes and hosts.

Determinism is **one** property, not a family of independent ones. It is proven by a single env-matrix case (§7 `determinism_across_env_matrix`) rather than one case per environmental dimension, because a genuine non-determinism defect trips every such dimension at once and so cannot be isolated to any one of them — splitting it across cases makes those cases non-orthogonal and unkillable in isolation (see §7 isolability invariant). The env-matrix witness must make each dimension **actually observable**, or the case is green while the property is untested. In particular the locale dimension is inert unless both hold: (a) the fixture carries a value whose magnitude crosses the locale grouping threshold (≥ 4 significant digits), and (b) the numeric locale is truly activated — `setlocale(LC_ALL, "")` inside the subprocess, because Python activates only `LC_CTYPE` at startup and an `LC_ALL` environment variable alone leaves `LC_NUMERIC` at `C`. A witness that skips either does not observe the property it claims to.

## 7. Acceptance / mutant-kill cases (enumerated case-IDs — ADR-0030)
Test name is `test_lp_03_<id>` — the ADR-0030 pure function `test_<LP_ID_normalized>_<id>` with LP-ID hyphen→underscore (`LP-03` → `lp_03`). One test function per id (bijective); **no pytest parametrization**. A case that needs a matrix of conditions loops internally within its single test function, keeping the pytest node-id byte-stable — the id *is* the node.

**Isolability invariant (ADR-0025 / ADR-0030 exact-set gate).** Each case below is the *sole* detector of exactly one defect class: for every id there exists a mutant that fails that id's test and no other, and no two cases vary the same dimension such that one case's varied-set is a subset of another's. Two cases whose tests reduce to the same assertion (differing only in what they vary between calls) can never both be independently killed, so a §7 that splits one property across them can never satisfy the exact-set gate (per mutant: declared-fail set must equal actual-fail set). That is a **structural** defect, not a mutant-quality one — no amount of re-authoring fixes it. Each case's detail (§7a) names its **witness** (what makes the property observable) and the defect class (**kills**) it is the sole detector of.

**Schema note (why this block is thin).** The machine-parsed block below carries only `id` + `desc` — the schema the §7 parser / test-name deriver already accepts, under which this contract reached `verifier-built`. The per-case `property` / `witness` / `kills` live in §7a as prose, so **no parser change is required to author against this contract**. Promoting those to parsed schema fields, plus an authoring-preflight that refuses a non-isolable case set (any `varies(A) ⊆ varies(B)`, or an empty witness) *before* an agent spawns, is a separate ADR-0024 §7 amendment — routed to Architect, not asserted here.

    §7 cases:
      - id: determinism_across_env_matrix
        desc: "output depends only on logical content — byte-identical across repeat, process restart, host locale, host timezone/wall-clock, process randomness, field insertion order, and construction path/object identity. Subsumes the six facets a prior draft split (byte_identical_on_repeat, stable_across_equal_inputs, iteration_order_independent, locale_independent, timezone_independent, randomness_independent). Detail: §7a."
      - id: distinct_inputs_distinct_bytes
        desc: "logically different documents -> different bytes (canonical form preserves content distinctions). Detail: §7a."
      - id: empty_document_canonical
        desc: "valid empty document (empty-but-present body, no attachments) -> returns bytes, does not raise. Detail: §7a."
      - id: non_document_input_raises
        desc: "None or wrong-typed argument -> raises TypeError. Detail: §7a."
      - id: incomplete_document_raises
        desc: "right-typed ParsedDocument with a null/empty required field -> raises ValueError. Detail: §7a."

A §7 that is bare prose, omits ids for property/determinism cases, or contains any case that is not independently killable (per the isolability invariant) is NOT freezable (ADR-0030 §7 + ADR-0025 exact-set gate; ADR-0030 already amends ADR-0024 with the case-ID requirement).

### 7a. Per-case detail — property · witness · kills
The **kills** entry names the defect *class* each case is the sole detector of; it is required to reason about isolability and is **illustrative, not a mutant list to transcribe**. A red-team author intended to evidence *independent convergence* (not merely tool liveness) authors blind to these — see the closure-run note in §7b.

**determinism_across_env_matrix**
- *property:* output depends ONLY on the document's logical content — invariant across repeated calls, process restart, locale, timezone/wall-clock, randomness, insertion order of unordered fields, and construction path/object identity.
- *witness:* **200 generated inputs**, each satisfying the §7b observability requirements. Each input is its own baseline: canonicalize it once, then re-canonicalize it across the environment legs and assert every result equals **that input's own baseline** (no baseline is shared across inputs — a shared baseline is what dragged the old facets into each other's fail-sets). Environment legs: repeat in-process; a fresh subprocess; header + attachment insertion-order permutations; `PYTHONHASHSEED ∈ {0, 1, random}`; `TZ ∈ {UTC, America/New_York, Asia/Kolkata}`; an **activated** numeric locale `∈ {C, de_DE.UTF-8}`. Every input gets the repeat / subprocess / order legs; the locale × TZ × hashseed combinations are **sampled across the 200** so each value appears many times and every pairwise combination appears at least once (bounds runtime while keeping input-shape breadth *and* env depth). The hashseed dimension MUST be witnessed by ≥1 input canonicalized in a subprocess whose seed differs from that input's baseline seed — otherwise a dict-iteration defect is invisible on that input. ACTIVATED locale = the subprocess calls `setlocale(LC_ALL, "")` (per §6). A locale absent on the host **fails** the case — never `continue`/skip, or a C-only CI container silently no-ops while appearing to cover the set.
- *kills:* any single environmental-dependence defect — embedding `random.random()`, reading `datetime.now()`, serializing headers/attachments in iteration order, formatting a value through the active locale, or keying output on `id(doc)`. Each such mutant fails this test and only this test. A constant-but-deterministic mutant does NOT fail it (that is `distinct_inputs_distinct_bytes`).

**distinct_inputs_distinct_bytes**
- *property:* the canonical form preserves rather than erases content distinctions.
- *witness:* two documents differing in body content, environment held fixed → different bytes.
- *kills:* the constant-output / echo mutant (returns a fixed byte string, or ignores its argument). It is fully deterministic, so it passes `determinism_across_env_matrix` and fails only here.

**empty_document_canonical**
- *property:* a valid empty document (empty-but-present body, no attachments) is DEFINED input, not an error.
- *witness:* `canonicalize(ParsedDocument(body="", headers={}, attachments=()))` returns a `bytes` value and does not raise. Assert **no-raise + returns-bytes only** — NOT equality to a golden byte string. A golden here would re-couple this case to every variability mutant (any determinism defect would also change these bytes), rebuilding the over-kill this restructure removed.
- *kills:* a mutant that special-cases the empty document to raise, or to return a non-`bytes` value. The non-empty baselines used elsewhere leave every other case intact, so it fails only here.

**non_document_input_raises**
- *property:* wrong-*typed* input is rejected loudly, not coerced or silently accepted.
- *witness:* `canonicalize(None)`, `canonicalize(<a non-ParsedDocument object>)`, and `canonicalize(<a dict stand-in>)` each raise `TypeError`.
- *kills:* a mutant that drops the type guard and proceeds, or raises the wrong exception type. The completeness check is untouched, so `incomplete_document_raises` still passes and this fails only here.

**incomplete_document_raises**
- *property:* a right-typed but structurally incomplete `ParsedDocument` is outside the contract and raises `ValueError` — distinct from the `TypeError` of wrong-typed input.
- *witness:* a `ParsedDocument` that **constructs successfully** but carries a null/empty required field — e.g. `ParsedDocument(body=None, headers={}, attachments=())` (the dataclass does not runtime-enforce `body: str`, so this constructs; the seam's completeness validation is what must raise). → raises `ValueError`, not `TypeError`, not a silent return. (This resolves the ambiguity in a strict-dataclass stub, where a field cannot be *omitted* at construction.)
- *kills:* a mutant that tolerates the incomplete document (returns bytes) or conflates it with the `TypeError` case. Wrong-typed inputs still raise `TypeError`, so `non_document_input_raises` still passes and this fails only here.

### 7b. Witness observability requirements (binding on the verifier's fixture generator)
The env-matrix case fails *silently* — a real determinism defect goes undetected inside a green case — unless every generated input makes each varied dimension observable in the output. The v0.1 escape was exactly this hole: a genuinely locale-dependent code path that only executes past 1000 characters, left inert by a 25-character fixture — the input sat entirely on one side of a processing threshold, so the buggy path never ran and the case passed blindly (a false PASS, not a kill). Each of the 200 generated inputs MUST contain:
- a **numeric field of ≥ 4 significant digits** — so a locale's digit-grouping rule can change the bytes (locale observable);
- a **value rendered from a date or time** — so a timezone / wall-clock read can change the bytes (TZ observable);
- a **mapping with ≥ 2 keys AND ≥ 2 attachments** — so hash-order / insertion-order serialization can change the bytes (order observable);
- a **body that crosses the locale processing threshold** — comfortably past 1000 characters, so a length-gated locale/formatting path actually executes; this is the specific v0.1 escape. The corpus MUST additionally include inputs straddling the boundary (e.g. 999 / 1000 / 1001 characters) so a threshold-gated defect is caught precisely rather than by luck, and the groupable number above MUST fall inside the processed region — crossing the length alone reveals nothing.

These are **hand-tuned** witnesses — a floor, not a guarantee. A defect whose trigger falls outside this enumerated list (a decimal-separator bug needing a fractional value; a case-folding bug needing a locale outside the matrix set) stays inert across the whole corpus and escapes. Replacing the fixed list with generated inputs plus a per-axis "witness fired or the run fails" check is parked in the backlog (`BL-01 · generated-witness observability`), to revisit after this lands.

*Closure-run vs independence-grade proof.* For this week's goal — proving the pipeline runs end-to-end — a red-team author may use §7a `kills` as guidance and a green five-of-five gate is sufficient. To use the same green gate as evidence for the program's **independent-convergence** thesis, the red-team author must be blind to §7a (author mutants from the properties alone); otherwise the gate demonstrates a shared crib, not convergence. Record which claim the run is making.

### 7c. Normalization scope — RULED (owner, 2026-09-20)
Encoding-level normalization (CRLF/LF line endings, BOM, Unicode NFC) is **out of scope for LP-03**. LP-03 guarantees deterministic serialization only; producing canonical *text* is LP-01's responsibility by its own name ("MIME parse to canonical text"), with LP-02 isolating the live request. The `normalizes_line_endings_and_bom` case from the original tool repo is therefore **not** added here, and the five-case set stands. The dependency is recorded as a §3 pre-condition (input already encoding-normalized upstream).

**Remaining external action (tracked against LP-01, not a §7 blocker for LP-03):** when LP-01 is authored it MUST carry the normalization promise in its §4. If it does not, normalization falls back to LP-03 and this ruling reopens — adding one further orthogonal case (killed by a no-normalization mutant) without disturbing the five above. Until LP-01 is authored, this assumption is unverified; it does not block LP-03's determinism verifier, which is self-contained.

## 8. Freeze discipline (ADR-0015)
Human-only writes. A change bumps every dependent loop back to verifier-built.

## Version history
| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-09-18 | Draft |
| 0.2 | 2026-09-20 | DRAFT — §7 restructured to satisfy the exact-set gate: folded the six determinism facets into one `determinism_across_env_matrix` case (the split left two ids unkillable in isolation, so the gate could never pass); added witness/kills per case and the isolability invariant; §6 gained the LC_NUMERIC/subprocess rationale; raised the `normalizes_line_endings_and_bom` divergence as an open ratification note. |
| 0.3 | 2026-09-20 | DRAFT — merge + fixes. (1) Machine-parsed block reverted to `id`+`desc`; `property`/`witness`/`kills` moved to §7a prose, schema promotion deferred to an ADR-0024 §7 amendment (Architect). (2) `incomplete_document_raises` witness made constructible against a strict `ParsedDocument` stub (`body=None` → `ValueError`, distinct from wrong-type `TypeError`); §5 clarified. (3) Restored 200-input breadth: each input its own baseline, env legs sampled across the set. (4) `kills` reframed as illustrative defect-classes; added closure-run vs independence-grade note (§7b). §4 gained construction-path/object-identity as an explicit independence dimension. |
| 0.4 | 2026-09-20 | DRAFT — review fixes (owner). (1) Test-name prefix corrected `test_lp03_` → `test_lp_03_` to match the ADR-0030 deriver (LP-ID hyphen→underscore = `lp_03`); the mismatch would have desynced B2/B5 blind name derivation and prevented the exact-set gate from closing. (2) Normalization ruled out of scope for LP-03 (§7c) and recorded as a §3 upstream pre-condition; LP-01 flagged to carry the promise in its §4. (3) §5 empty-document disambiguated (`body==""` returns bytes vs `body is None` raises `ValueError`); empty-case desc aligned. (4) §7b/§7a: hashseed dimension must be witnessed by ≥1 input run under a subprocess seed differing from its baseline. (5) Dependencies line notes the promise-level upstream assumption. Five-case set unchanged; NOT ratified, NOT frozen; requires a verifier re-author to the five-case set. |
| 0.5 | 2026-09-20 | DRAFT — §7b hardened for the v0.1 escape. Corrected the escape's root cause (a length-gated locale path that only runs past 1000 characters, not merely a short body) and added a **body-size witness**: each input's body must cross the 1000-char processing threshold, with corpus inputs straddling the boundary (999/1000/1001) and the groupable number inside the processed region. Noted the witness list is a hand-tuned floor; generation parked as backlog `BL-01`. Fold and five-case set unchanged. NOT ratified, NOT frozen. |

> Created using Anthropic Claude — retain this line on internal drafts until a human has reviewed and verified the contract; remove or replace it on ratification.
