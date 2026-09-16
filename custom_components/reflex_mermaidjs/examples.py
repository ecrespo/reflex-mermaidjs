"""Sample diagrams for every mermaid diagram type.

The samples are taken from the official ``@mermaid-js/examples`` package (the
same ones listed under "Sample Diagrams" in mermaid.live), plus Agentflow,
Swimlane and ZenUML samples from the mermaid docs.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import TypedDict


class Example(TypedDict, total=False):
    """A single sample diagram."""

    title: str
    code: str
    isDefault: bool


class DiagramMetadata(TypedDict):
    """A diagram type and its samples."""

    id: str
    name: str
    description: str
    examples: list[Example]


@lru_cache
def get_diagram_examples() -> list[DiagramMetadata]:
    """Return every diagram type with its sample definitions."""
    path = Path(__file__).with_name("examples.json")
    return json.loads(path.read_text(encoding="utf-8"))


def get_default_example(diagram_id: str) -> str:
    """Return the default sample code for a diagram id (``flowchart-v2``, ``sequence``, ...)."""
    for diagram in get_diagram_examples():
        if diagram["id"] == diagram_id:
            examples = diagram["examples"]
            default = next((e for e in examples if e.get("isDefault")), examples[0])
            return default["code"]
    msg = f"Unknown diagram id: {diagram_id}"
    raise KeyError(msg)
