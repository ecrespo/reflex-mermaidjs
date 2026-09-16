"""reflex-mermaidjs: mermaid-js diagrams for Reflex."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _package_version

from . import actions
from .actions import (
    copy_svg,
    export_png,
    export_svg,
    fit_view,
    fullscreen,
    get_png_data_url,
    get_svg,
    reset_view,
    set_zoom,
    zoom_in,
    zoom_out,
)
from .constants import (
    DIAGRAM_KEYWORDS,
    LAYOUTS,
    LOOKS,
    MERMAID_VERSION,
    SECURITY_LEVELS,
    THEMES,
)
from .examples import get_default_example, get_diagram_examples
from .markdown import markdown_with_mermaid, mermaid_component_map
from .mermaidjs import (
    ErrorEvent,
    IconPack,
    Mermaid,
    NodeClickEvent,
    RenderEvent,
    ZoomEvent,
    mermaid,
)
from .urls import (
    build_state,
    deserialize_state,
    kroki_url,
    mermaid_ink_url,
    mermaid_live_url,
    pako_decode,
    pako_encode,
    serialize_state,
)

# pyproject.toml is the single source of truth for the version; read it back
# from the installed metadata so the two can never drift.
try:
    __version__ = _package_version("reflex-mermaidjs")
except PackageNotFoundError:  # pragma: no cover - source tree without an install
    __version__ = "0.0.0.dev0"

__all__ = [
    "DIAGRAM_KEYWORDS",
    "LAYOUTS",
    "LOOKS",
    "MERMAID_VERSION",
    "SECURITY_LEVELS",
    "THEMES",
    "ErrorEvent",
    "IconPack",
    "Mermaid",
    "NodeClickEvent",
    "RenderEvent",
    "ZoomEvent",
    "actions",
    "build_state",
    "copy_svg",
    "deserialize_state",
    "export_png",
    "export_svg",
    "fit_view",
    "fullscreen",
    "get_default_example",
    "get_diagram_examples",
    "get_png_data_url",
    "get_svg",
    "kroki_url",
    "markdown_with_mermaid",
    "mermaid",
    "mermaid_component_map",
    "mermaid_ink_url",
    "mermaid_live_url",
    "pako_decode",
    "pako_encode",
    "reset_view",
    "serialize_state",
    "set_zoom",
    "zoom_in",
    "zoom_out",
]
