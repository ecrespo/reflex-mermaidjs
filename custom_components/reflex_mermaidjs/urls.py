"""Pure-Python helpers to share diagrams with mermaid.live, mermaid.ink and kroki.

These mirror the serializers used by the official Mermaid Live Editor
(``pako:`` = zlib deflate + URL-safe base64, no padding), so links created here
open directly in https://mermaid.live.
"""

from __future__ import annotations

import base64
import json
import zlib
from typing import Any, Literal

MERMAID_LIVE_URL = "https://mermaid.live"
MERMAID_INK_URL = "https://mermaid.ink"
KROKI_URL = "https://kroki.io"


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    data = data.replace("+", "-").replace("/", "_")
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def build_state(
    code: str,
    config: dict[str, Any] | None = None,
    *,
    rough: bool = False,
    pan_zoom: bool = True,
    grid: bool = True,
    update_diagram: bool = True,
) -> dict[str, Any]:
    """Build a Mermaid Live Editor state object.

    Args:
        code: The diagram text.
        config: The mermaid configuration (serialized to JSON as the editor expects).
        rough: Hand-drawn rendering toggle.
        pan_zoom: Pan & zoom toggle.
        grid: Grid background toggle.
        update_diagram: Auto-sync toggle.

    Returns:
        The state dictionary.
    """
    return {
        "code": code,
        "mermaid": json.dumps(config or {}, indent=2),
        "autoSync": True,
        "rough": rough,
        "updateDiagram": update_diagram,
        "panZoom": pan_zoom,
        "grid": grid,
    }


def pako_encode(text: str) -> str:
    """Deflate ``text`` (zlib, level 9) and encode it as URL-safe base64 without padding."""
    return _b64url_encode(zlib.compress(text.encode("utf-8"), 9))


def pako_decode(data: str) -> str:
    """Inverse of :func:`pako_encode`."""
    return zlib.decompress(_b64url_decode(data)).decode("utf-8")


def serialize_state(state: dict[str, Any], serde: Literal["pako", "base64"] = "pako") -> str:
    """Serialize a live-editor state as ``pako:...`` or ``base64:...``."""
    payload = json.dumps(state, separators=(",", ":"))
    if serde == "pako":
        return f"pako:{pako_encode(payload)}"
    if serde == "base64":
        return f"base64:{_b64url_encode(payload.encode('utf-8'))}"
    msg = f"Unknown serde type: {serde}"
    raise ValueError(msg)


def deserialize_state(serialized: str) -> dict[str, Any]:
    """Parse a ``pako:``/``base64:`` state (as found after ``#`` in mermaid.live URLs)."""
    serialized = serialized.split("#", 1)[-1]
    if ":" in serialized:
        serde, data = serialized.split(":", 1)
    else:
        serde, data = "base64", serialized
    if serde == "pako":
        return json.loads(pako_decode(data))
    if serde == "base64":
        return json.loads(_b64url_decode(data).decode("utf-8"))
    msg = f"Unknown serde type: {serde}"
    raise ValueError(msg)


def mermaid_live_url(
    code: str,
    config: dict[str, Any] | None = None,
    *,
    mode: Literal["edit", "view"] = "edit",
    **state_options: Any,
) -> str:
    """URL that opens the diagram in the Mermaid Live Editor.

    Args:
        code: The diagram text.
        config: Optional mermaid configuration.
        mode: ``edit`` (editor) or ``view`` (full-screen view).
        **state_options: Extra options for :func:`build_state`.

    Returns:
        The URL.
    """
    state = build_state(code, config, **state_options)
    return f"{MERMAID_LIVE_URL}/{mode}#{serialize_state(state)}"


def mermaid_ink_url(
    code: str,
    config: dict[str, Any] | None = None,
    *,
    fmt: Literal["svg", "img", "pdf"] = "svg",
    image_type: Literal["png", "jpeg", "webp"] | None = None,
    theme: str | None = None,
    bg_color: str | None = None,
    width: int | None = None,
    height: int | None = None,
    scale: float | None = None,
) -> str:
    """URL of a server-rendered image of the diagram on mermaid.ink.

    Args:
        code: The diagram text.
        config: Optional mermaid configuration.
        fmt: ``svg``, ``img`` (raster) or ``pdf``.
        image_type: Raster type for ``fmt="img"``.
        theme: Theme override.
        bg_color: Background color (hex without ``#`` or ``!name``).
        width: Output width.
        height: Output height.
        scale: Output scale (requires width or height).

    Returns:
        The URL.
    """
    state = {"code": code, "mermaid": json.dumps(config or {})}
    url = f"{MERMAID_INK_URL}/{fmt}/{serialize_state(state)}"
    params = {
        "type": image_type,
        "theme": theme,
        "bgColor": bg_color,
        "width": width,
        "height": height,
        "scale": scale,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
    return f"{url}?{query}" if query else url


def kroki_url(code: str, fmt: Literal["svg", "png", "pdf"] = "svg") -> str:
    """URL of the diagram rendered by kroki.io."""
    return f"{KROKI_URL}/mermaid/{fmt}/{pako_encode(code)}"
