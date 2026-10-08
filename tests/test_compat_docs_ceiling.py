"""Public compatibility documents must agree with the declared plugin ceiling."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DOCS = ("README.md", "COMPATIBILITY.md", "CERTIFICATION.md")


def test_public_docs_do_not_claim_the_obsolete_47_fail_closed_ceiling() -> None:
    """The ceiling is 4.7.99, so 4.7.1 and later 4.7 patches are not refused."""
    for name in PUBLIC_DOCS:
        path = ROOT / name
        if not path.exists():
            continue
        text = " ".join(path.read_text(encoding="utf-8").split())
        assert "4.7.1 and later fail closed" not in text, name
        assert "4.7.1 and later releases fail closed" not in text, name
        assert "4.7.1+ are refused" not in text, name
        assert "`v4.7.1+` remains outside the tested contract" not in text, name
