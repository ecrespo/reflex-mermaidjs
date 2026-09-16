"""Gallery: every diagram type supported by mermaid 12, rendered live."""

from __future__ import annotations

import reflex as rx
from reflex_mermaidjs import mermaid

from .state import EXAMPLES, EditorState
from .ui import page_shell, section_title


def gallery_card(diagram: dict, index: int) -> rx.Component:
    default = next((e for e in diagram["examples"] if e.get("isDefault")), diagram["examples"][0])
    return rx.box(
        rx.box(
            mermaid(
                default["code"],
                id=f"gallery-{index}",
                appearance=rx.color_mode_cond("light", "dark"),
                pan_zoom=True,
                show_controls=False,
                grid=False,
                height="240px",
                width="100%",
            ),
            background=rx.color("gray", 1),
            border_bottom=f"1px solid {rx.color('gray', 4)}",
        ),
        rx.vstack(
            rx.hstack(
                rx.heading(diagram["name"], size="3"),
                rx.spacer(),
                rx.badge(f"{len(diagram['examples'])} samples", variant="soft", color_scheme="gray"),
                width="100%",
                align="center",
            ),
            rx.text(diagram["description"], size="2", color_scheme="gray"),
            rx.hstack(
                rx.button(
                    rx.icon("pencil", size=14),
                    "Open in editor",
                    size="1",
                    on_click=EditorState.open_in_editor(index, -1),
                ),
                rx.code(diagram["id"], size="1", variant="ghost"),
                align="center",
                spacing="3",
            ),
            spacing="2",
            padding="12px 14px",
            align="start",
        ),
        border=f"1px solid {rx.color('gray', 4)}",
        border_radius="14px",
        overflow="hidden",
        background=rx.color("gray", 2),
        _hover={"border_color": rx.color("accent", 7)},
        transition="border-color 120ms",
    )


def gallery_page() -> rx.Component:
    return page_shell(
        section_title(
            f"Diagram gallery · {len(EXAMPLES)} types",
            "Every diagram type available in mermaid 12 (plus the ZenUML plugin), rendered by reflex-mermaidjs. Scroll to zoom, drag to pan.",
        ),
        rx.grid(
            *[gallery_card(d, i) for i, d in enumerate(EXAMPLES)],
            columns=rx.breakpoints(initial="1", sm="2", lg="3"),
            spacing="4",
            width="100%",
        ),
    )
