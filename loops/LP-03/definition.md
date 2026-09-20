---
id: LP-03
epic: CAP-1
story: S-01
class: standard
historical: false
deps: [LP-01]
owns:
  write:
    - "src/intent_extractor/canonical.py"
  read:
    - "Verifier/tests/properties/test_lp03_canonical_determinism.py"
    - "src/intent_extractor/__init__.py"
    - "conftest.py"
    - "pyproject.toml"
    - "contracts/LP-03-canonical-determinism.md"
    - "loops/LP-03/definition.md"
---

# LP-03 — Canonical determinism

## Task
Canonicalization reduces a parsed document to a single canonical byte serialization such that the same logical input always produces exactly the same bytes.

## Seam (frozen — contract section 2, ADR-0024)

    from intent_extractor.canonical import canonicalize
    
    def canonicalize(doc: ParsedDocument) -> bytes: ...

## Verifier
Fixture-free property. Contract contracts/LP-03-canonical-determinism.md v0.5.
Evidence lives in the registry.

## Dependencies
LP-01.
