"""Event helpers that drive a rendered diagram from Python.

Every ``mermaid(...)`` created with an ``id`` registers an imperative API in the
browser (``window.__reflexMermaid[id]``). These helpers return
``rx.call_script`` events, so they can be returned from event handlers or used
directly as triggers::

    rx.button("Export PNG", on_click=export_png("diagram", "flow.png"))
"""

from __future__ import annotations

import json

import reflex as rx
from reflex.event import EventSpec


def _call(diagram_id: str, method: str, *args: object, callback=None) -> EventSpec:
    js_args = ", ".join(json.dumps(a) for a in args)
    script = (
        f"(async () => {{ const api = window.__reflexMermaid?.[{json.dumps(diagram_id)}];"
        f" if (!api) {{ console.warn('reflex-mermaidjs: no diagram with id', {json.dumps(diagram_id)}); return null; }}"
        f" return await api.{method}({js_args}); }})()"
    )
    if callback is not None:
        return rx.call_script(script, callback=callback)
    return rx.call_script(script)


def zoom_in(diagram_id: str) -> EventSpec:
    """Zoom in one step (requires ``pan_zoom=True``)."""
    return _call(diagram_id, "zoomIn")


def zoom_out(diagram_id: str) -> EventSpec:
    """Zoom out one step (requires ``pan_zoom=True``)."""
    return _call(diagram_id, "zoomOut")


def set_zoom(diagram_id: str, zoom: float) -> EventSpec:
    """Set an absolute zoom factor (requires ``pan_zoom=True``)."""
    return _call(diagram_id, "setZoom", zoom)


def fit_view(diagram_id: str) -> EventSpec:
    """Fit the diagram into its viewport."""
    return _call(diagram_id, "fit")


def reset_view(diagram_id: str) -> EventSpec:
    """Show the diagram at 100% centered."""
    return _call(diagram_id, "reset")


def fullscreen(diagram_id: str) -> EventSpec:
    """Open the diagram in fullscreen."""
    return _call(diagram_id, "fullscreen")


def export_svg(diagram_id: str, filename: str = "diagram.svg", background: str | None = None) -> EventSpec:
    """Download the rendered diagram as an SVG file."""
    return _call(diagram_id, "exportSvg", filename, background)


def export_png(
    diagram_id: str,
    filename: str = "diagram.png",
    scale: float = 2,
    background: str = "white",
) -> EventSpec:
    """Download the rendered diagram as a PNG (``background="transparent"`` for no fill)."""
    return _call(diagram_id, "exportPng", filename, scale, background)


def copy_svg(diagram_id: str) -> EventSpec:
    """Copy the SVG markup to the clipboard."""
    return _call(diagram_id, "copySvg")


def get_svg(diagram_id: str, callback) -> EventSpec:
    """Send the current SVG markup to ``callback`` (an event handler taking one str)."""
    return _call(diagram_id, "getSvg", callback=callback)


def get_png_data_url(diagram_id: str, callback, scale: float = 2, background: str = "white") -> EventSpec:
    """Send a ``data:image/png;base64,...`` URL of the diagram to ``callback``."""
    return _call(diagram_id, "exportPng", None, scale, background, callback=callback)
