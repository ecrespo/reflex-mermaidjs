"""Fail if pyproject.toml declares a trove classifier PyPI will reject.

`twine check` only validates README rendering, so an invalid classifier
otherwise survives every local check and is first rejected by PyPI itself —
during the upload, which is the one step that cannot be rehearsed.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

from trove_classifiers import classifiers as VALID


def main() -> int:
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    declared = tomllib.loads(pyproject.read_text())["project"].get("classifiers", [])

    invalid = [c for c in declared if c not in VALID]
    if invalid:
        for c in invalid:
            print(f"::error::Invalid trove classifier: {c!r}", file=sys.stderr)
        print(
            f"\n{len(invalid)} invalid classifier(s). See https://pypi.org/classifiers/ for the full list.",
            file=sys.stderr,
        )
        return 1

    print(f"All {len(declared)} classifiers are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
