"""Constants mirroring the mermaid-js v12 configuration schema."""

from __future__ import annotations

from typing import Literal

#: npm version of mermaid bundled by this component.
MERMAID_VERSION = "12.0.0"
TIDY_TREE_VERSION = "1.0.0"
ZENUML_VERSION = "1.0.0"
FONTAWESOME_VERSION = "7.3.1"
ICONIFY_LOGOS_VERSION = "1.2.14"
ICONIFY_MDI_VERSION = "1.2.3"
KATEX_VERSION = "0.16.47"

MermaidTheme = Literal[
    "default",
    "base",
    "dark",
    "forest",
    "neutral",
    "neo",
    "neo-dark",
    "redux",
    "redux-dark",
    "redux-color",
    "redux-dark-color",
    "null",
]
MermaidLook = Literal["classic", "handDrawn", "neo"]
MermaidSecurityLevel = Literal["strict", "loose", "antiscript", "sandbox"]
MermaidLogLevel = Literal["trace", "debug", "info", "warn", "error", "fatal"]
MermaidErrorMode = Literal["inline", "keep-last", "none"]
ControlsPosition = Literal["top-right", "top-left", "bottom-right", "bottom-left"]

#: All built-in themes (``"null"`` disables the pre-defined themes).
THEMES: list[str] = [
    "default",
    "base",
    "dark",
    "forest",
    "neutral",
    "neo",
    "neo-dark",
    "redux",
    "redux-dark",
    "redux-color",
    "redux-dark-color",
]

#: Visual looks.
LOOKS: list[str] = ["classic", "handDrawn", "neo"]

#: Layout algorithms available out of the box (ELK is bundled with mermaid 12,
#: ``tidy-tree`` is registered by this component).
LAYOUTS: list[str] = [
    "dagre",
    "elk",
    "elk.layered",
    "elk.stress",
    "elk.force",
    "elk.mrtree",
    "elk.radial",
    "elk.sporeOverlap",
    "elk.box",
    "elk.rectpacking",
    "tidy-tree",
]

SECURITY_LEVELS: list[str] = ["strict", "loose", "antiscript", "sandbox"]

#: Diagram keywords understood by mermaid 12 (plus the ZenUML plugin).
DIAGRAM_KEYWORDS: dict[str, str] = {
    "flowchart": "flowchart TD",
    "graph": "graph TD",
    "sequence": "sequenceDiagram",
    "class": "classDiagram",
    "state": "stateDiagram-v2",
    "er": "erDiagram",
    "journey": "journey",
    "gantt": "gantt",
    "pie": "pie",
    "quadrant": "quadrantChart",
    "requirement": "requirementDiagram",
    "gitgraph": "gitGraph",
    "c4": "C4Context",
    "mindmap": "mindmap",
    "timeline": "timeline",
    "zenuml": "zenuml",
    "sankey": "sankey-beta",
    "xychart": "xychart-beta",
    "block": "block-beta",
    "packet": "packet",
    "kanban": "kanban",
    "architecture": "architecture-beta",
    "radar": "radar-beta",
    "treemap": "treemap-beta",
    "venn": "venn-beta",
    "ishikawa": "ishikawa-beta",
    "usecase": "usecase-beta",
    "eventmodeling": "eventmodeling",
    "treeview": "treeView-beta",
    "wardley": "wardley-beta",
    "cynefin": "cynefin-beta",
    "railroad": "railroad-beta",
    "swimlane": "swimlane-beta",
    "agentflow": "agentflow-beta",
    "railroad-ebnf": "railroad-ebnf-beta",
    "railroad-abnf": "railroad-abnf-beta",
    "railroad-peg": "railroad-peg-beta",
}

#: Iconify packs registered by default (bundled npm packages, loaded lazily on first use).
DEFAULT_ICON_PACKS: list[str] = ["logos", "mdi"]
