loop: LP-03
write_scope:
- "src/intent_extractor/canonical.py"
read_scope:
- "Verifier/tests/properties/test_lp03_canonical_determinism.py"
- "src/intent_extractor/__init__.py"
- "conftest.py"
- "pyproject.toml"
- "contracts/LP-03-canonical-determinism.md"
- "loops/LP-03/definition.md"
---

You are running inside a git worktree for loop LP-03. Only the paths in
`write_scope` / `read_scope` are checked out; everything else is intentionally
absent. `check_prompt` refuses launch unless this header matches the registry
`owns` exactly, so do not edit the header to widen or narrow scope — that is done
by changing the definition and re-deriving owns (`reset --to defined`).

## The task

Implement `src/intent_extractor/canonical.py` — `def canonicalize(doc: ParsedDocument) -> bytes: ...` — per the frozen seam
(contract §2) and the verifier's docstring.

Invariant (transcribed from contract §4):

`canonicalize` is a pure, total function of its single argument. For any `ParsedDocument` `d`:
- Repeated evaluation yields **byte-identical** results (`canonicalize(d) == canonicalize(d)`), including across process restarts.
- The result is independent of the iteration order of unordered fields (e.g. header maps, attachment sets), host locale, host timezone / wall-clock, any process-level randomness, and the **construction path or object identity** of the argument — two independently constructed, logically-equal documents canonicalize to identical bytes.
- Two documents that are logically equal produce identical bytes; two documents that differ in content produce different bytes (the canonical form preserves, rather than erases, content distinctions).

Run the verifier:

    python -m pytest Verifier/tests/properties/test_lp03_canonical_determinism.py

Iterate until the suite is green, then stage and commit the owned file on the
current branch with message `LP-03: green`.

## Standing rules (every loop, no exceptions)

- Touch nothing outside `write_scope`. The gate makes out-of-scope changes
  unlandable, and a per-worktree pre-commit hook rejects them early.
- **Do not modify, patch, or reassign attributes of any imported class or module —
  if the verifier cannot pass without doing so, stop and report the conflict.**
  (Reassigning `__init__`/`__class__`, `setattr`/`object.__setattr__` on an imported
  name, or mutating `sys.modules` is an isolation violation and dies at the gate,
  even when every changed file is inside scope. A green suite bought that way is a
  quarantine, not a merge.)
- Do not modify the frozen verifier or any test. If a fixture constructs a type
  off-seam and you cannot pass without patching it, that is a verifier defect —
  stop and report it for re-gate.
- When green, commit only the owned file(s) on the current branch with a clear
  message. Do not leave out-of-scope untracked files behind; they are refused at
  merge.

## Documentation standard (world-class; documented, not decorated)

Write the code so a reviewer reads intent, not mechanics:
- **Module docstring** — one paragraph: what this module implements, the contract
  + seam it satisfies, and the core invariant (from the contract §4). Reference the
  contract path.
- **Every public function/class docstring** — purpose; Args; Returns; Raises
  (the exact exceptions the contract §4/§5 specifies, e.g. ValueError on mismatch,
  TypeError on malformed). One-line summary first, then detail.
- **Inline comments ONLY where logic is non-obvious** — explain the WHY, never
  restate the WHAT. No line-by-line narration. If the code needs a comment to be
  understood, prefer a clearer name or structure first.
- **No drift-prone comments** — do not describe values/behavior that the code
  already states literally (those rot). Comment rationale, edge-case reasoning,
  and contract linkage.
- Docstrings/comments must not change behavior — they are written alongside the
  implementation and the frozen verifier still governs correctness.
