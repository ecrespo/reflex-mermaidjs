"""Render ```mermaid fenced code blocks inside ``rx.markdown``."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import reflex as rx

from .mermaidjs import mermaid


def mermaid_component_map(**mermaid_props: Any) -> dict[str, Callable[..., rx.Component]]:
    """Component map for ``rx.markdown`` that turns ```mermaid blocks into diagrams.

    Other languages keep the regular ``rx.code_block`` rendering.

    Example:
        ```python
        rx.markdown(State.text, component_map=mermaid_component_map(theme="forest"))
        ```

    Args:
        **mermaid_props: Props forwarded to every generated ``mermaid`` component.

    Returns:
        The component map (merge it with your own if needed).
    """

    def _pre(text, language=None, **props) -> rx.Component:
        return rx.cond(
            language == "mermaid",
            mermaid(chart=text, **mermaid_props),
            rx.code_block(text, language=language, margin_y="1em", wrap_long_lines=True, **props),
        )

    return {"pre": _pre}


def markdown_with_mermaid(
    content, component_map: dict | None = None, mermaid_props: dict | None = None, **props
) -> rx.Component:
    """Shortcut for ``rx.markdown`` with mermaid code block support.

    Args:
        content: The markdown text (str or Var).
        component_map: Extra component overrides.
        mermaid_props: Props forwarded to the generated diagrams.
        **props: Props for ``rx.markdown``.

    Returns:
        The markdown component.
    """
    cmap = {**mermaid_component_map(**(mermaid_props or {})), **(component_map or {})}
    return rx.markdown(content, component_map=cmap, **props)
