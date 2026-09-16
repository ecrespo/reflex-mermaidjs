"""Reflex custom component wrapping mermaid-js (https://mermaid.js.org).

The heavy lifting happens in ``mermaid_diagram.jsx`` — a small React component
shipped with this package as a shared asset. It lazily imports ``mermaid`` in
the browser, renders the diagram text to SVG, and exposes pan & zoom, export
and click events. This module declares the Python side: props, event triggers
and the npm dependencies.

Example:
    ```python
    import reflex as rx
    from reflex_mermaidjs import mermaid

    def index():
        return mermaid(
            "flowchart TD\\n  A[Christmas] -->|Get money| B(Go shopping)",
            theme="default",
            pan_zoom=True,
            height="400px",
        )
    ```
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

import reflex as rx
from reflex.components.component import NoSSRComponent
from reflex.event import passthrough_event_spec
from reflex.vars.base import Var

from .constants import (
    FONTAWESOME_VERSION,
    ICONIFY_LOGOS_VERSION,
    ICONIFY_MDI_VERSION,
    KATEX_VERSION,
    MERMAID_VERSION,
    TIDY_TREE_VERSION,
    ZENUML_VERSION,
    ControlsPosition,
    MermaidErrorMode,
    MermaidLogLevel,
    MermaidLook,
    MermaidSecurityLevel,
    MermaidTheme,
)

_JSX_ASSET = rx.asset("mermaid_diagram.jsx", shared=True)


class RenderEvent(TypedDict):
    """Payload sent to ``on_render`` after a successful render."""

    svg: str
    diagram_type: str
    render_id: str
    render_ms: int


class ErrorEvent(TypedDict):
    """Payload sent to ``on_error`` when the diagram text cannot be rendered."""

    message: str
    line: int | None
    expected: list[str] | None


class NodeClickEvent(TypedDict):
    """Payload sent to ``on_node_click``."""

    node_id: str
    callback: str | None
    label: str | None
    args: list[Any]


class ZoomEvent(TypedDict):
    """Payload sent to ``on_zoom_change``."""

    zoom: float
    x: float
    y: float


class IconPack(TypedDict, total=False):
    """An iconify icon pack: ``name`` is the prefix used in diagrams."""

    name: str
    url: str
    pack: str


class Mermaid(NoSSRComponent):
    """Render mermaid diagrams (flowchart, sequence, class, ER, gantt, ...) from text."""

    library = _JSX_ASSET.importable_path

    tag = "MermaidDiagram"

    lib_dependencies: list[str] = [
        f"mermaid@{MERMAID_VERSION}",
        f"@mermaid-js/layout-tidy-tree@{TIDY_TREE_VERSION}",
        f"@mermaid-js/mermaid-zenuml@{ZENUML_VERSION}",
        f"@fortawesome/fontawesome-free@{FONTAWESOME_VERSION}",
        f"@iconify-json/logos@{ICONIFY_LOGOS_VERSION}",
        f"@iconify-json/mdi@{ICONIFY_MDI_VERSION}",
        f"katex@{KATEX_VERSION}",
    ]

    # ----------------------------------------------------------------- content
    # The mermaid diagram definition (may include YAML front matter).
    chart: Var[str]

    # ----------------------------------------------------------- mermaid config
    # Raw MermaidConfig passed to ``mermaid.initialize`` (dedicated props win).
    config: Var[dict[str, Any]]

    # Theme: default, base, dark, forest, neutral, neo, neo-dark, redux, ...
    theme: Var[MermaidTheme]

    # Look: classic, handDrawn or neo.
    look: Var[MermaidLook]

    # Layout algorithm: dagre, elk, elk.stress, tidy-tree, ...
    layout: Var[str]

    # Level of trust for the diagram source. ``loose`` enables click callbacks.
    security_level: Var[MermaidSecurityLevel]

    # Font family used by the diagrams.
    font_family: Var[str]

    # Base font size.
    font_size: Var[int]

    # Seed used by the handDrawn look (0 = random).
    hand_drawn_seed: Var[int]

    # Tell themes to compute colors for a dark background.
    dark_mode: Var[bool]

    # Render labels as HTML (foreignObject) instead of SVG text.
    html_labels: Var[bool]

    # Maximum diagram text length.
    max_text_size: Var[int]

    # Maximum number of edges.
    max_edges: Var[int]

    # Wrap long labels automatically.
    wrap: Var[bool]

    # Generate deterministic ids (useful for snapshot tests).
    deterministic_ids: Var[bool]

    # mermaid log level.
    log_level: Var[MermaidLogLevel]

    # Theme variables (most useful with ``theme="base"``).
    theme_variables: Var[dict[str, Any]]

    # Extra CSS injected in the generated SVG.
    theme_css: Var[str]

    # When no theme is set, "dark" picks the dark variant of each diagram type's default theme (like mermaid.live).
    appearance: Var[Literal["light", "dark"]]

    # ------------------------------------------------------------------ plugins
    # Register the tidy-tree layout (``layout: tidy-tree``).
    tidy_tree: Var[bool]

    # Register the ZenUML diagram eagerly (it is also auto-enabled when the text starts with ``zenuml``).
    zenuml: Var[bool]

    # Load Font Awesome CSS so ``fa:fa-car`` icons render.
    font_awesome: Var[bool]

    # Iconify packs: names (``logos`` and ``mdi`` are bundled, others load from jsDelivr) or ``{"name": ..., "url": ...}`` dicts.
    icon_packs: Var[list[str | IconPack]]

    # ------------------------------------------------------------- behaviour/UI
    # Debounce re-renders (ms) when the chart text changes quickly.
    debounce: Var[int]

    # Enable mouse-wheel zoom and drag-to-pan. The component then fills its box: give it a height.
    pan_zoom: Var[bool]

    # Show the floating zoom toolbar (defaults to ``pan_zoom``).
    show_controls: Var[bool]

    # Toolbar position.
    controls_position: Var[ControlsPosition]

    # Minimum zoom factor.
    min_zoom: Var[float]

    # Maximum zoom factor.
    max_zoom: Var[float]

    # Relative zoom step used by the toolbar buttons.
    zoom_step: Var[float]

    # Pan & zoom mode: True fits after every render, False only on the first one,
    # "auto" (default) also refits when the diagram type or size changes a lot.
    fit_on_render: Var[bool | Literal["auto"]]

    # Largest zoom factor "fit" may use (1 = never enlarge small diagrams).
    max_fit_zoom: Var[float]

    # Draw a dotted grid behind the diagram.
    grid: Var[bool]

    # Center the SVG horizontally (static mode).
    center: Var[bool]

    # inline: show errors; keep-last: show errors and keep the last good SVG; none: hide errors.
    error_mode: Var[MermaidErrorMode]

    # Names used in ``click nodeId callbackName`` directives, routed to ``on_node_click``.
    click_callbacks: Var[list[str]]

    # Emit ``on_node_click`` for clicks on any node, even without ``click`` directives.
    node_click: Var[bool]

    # ------------------------------------------------------------------- events
    # Fired after a successful render.
    on_render: rx.EventHandler[passthrough_event_spec(RenderEvent)]

    # Fired when the diagram cannot be parsed or rendered.
    on_error: rx.EventHandler[passthrough_event_spec(ErrorEvent)]

    # Fired when a node is clicked (see ``node_click`` and ``click_callbacks``).
    on_node_click: rx.EventHandler[passthrough_event_spec(NodeClickEvent)]

    # Fired when the zoom or pan position changes.
    on_zoom_change: rx.EventHandler[passthrough_event_spec(ZoomEvent)]

    @classmethod
    def create(cls, *children, **props) -> rx.Component:
        """Create a mermaid diagram.

        The diagram text can be passed positionally or with ``chart=``.

        Args:
            *children: Optionally, the diagram text (str or string Var).
            **props: Component props.

        Returns:
            The component.
        """
        if children and "chart" not in props:
            chart, *rest = children
            if isinstance(chart, (str, Var)):
                props["chart"] = chart
                children = tuple(rest)
        if props.get("pan_zoom") is True and not any(
            key in props for key in ("height", "min_height", "style")
        ):
            props["height"] = "480px"
        return super().create(*children, **props)


mermaid = Mermaid.create
