"""Make src/ and Verifier/ importable regardless of how pytest is launched
(so `from intent_extractor... import ...` and `import verifier` resolve).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for sub in ("src", "Verifier"):
    p = str(ROOT / sub)
    if p not in sys.path:
        sys.path.insert(0, p)
