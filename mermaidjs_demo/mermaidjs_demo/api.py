"""API reference page generated from the component source."""

from __future__ import annotations

import inspect
import re

import reflex as rx
import reflex_mermaidjs
from reflex_mermaidjs import actions, markdown, mermaidjs, urls

from .ui import card, page_shell, section_title

USAGE = """import reflex as rx
from reflex_mermaidjs import mermaid, export_png, mermaid_live_url


class State(rx.State):
    code: str = "flowchart TD\\n    A[Christmas] -->|Get money| B(Go shopping)"
    clicked: str = ""

    @rx.event
    def on_click(self, event: dict):
        self.clicked = event["node_id"]


def index():
    return rx.vstack(
        mermaid(
            State.code,
            id="diagram",
            theme="forest",            # or leave unset + appearance="dark"
            look="handDrawn",
            layout="elk",
            pan_zoom=True,             # wheel zoom, drag pan, toolbar
            grid=True,
            node_click=True,
            on_node_click=State.on_click,
            height="480px",
        ),
        rx.button("PNG", on_click=export_png("diagram", "diagram.png")),
        rx.link("Open in mermaid.live", href=mermaid_live_url(State.code)),  # or a computed var
    )
"""


def _props() -> list[tuple[str, str, str]]:
    source = inspect.getsource(mermaidjs.Mermaid)
    rows: list[tuple[str, str, str]] = []
    comment: list[str] = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("# ---"):
            comment = []
            continue
        if stripped.startswith("#"):
            comment.append(stripped.lstrip("# ").strip())
            continue
        match = re.match(r"^(\w+): (rx\.EventHandler\[.*\]|Var\[.*\])$", stripped)
        if match and not match.group(1).startswith("_"):
            kind = match.group(2)
            kind = re.sub(r"passthrough_event_spec\((\w+)\)", r"\1", kind).replace("rx.EventHandler", "event")
            rows.append((match.group(1), kind, " ".join(comment)))
        comment = []
    return rows


def _functions(module) -> list[tuple[str, str, str]]:
    rows = []
    for name, fn in inspect.getmembers(module, inspect.isfunction):
        if name.startswith("_") or fn.__module__ != module.__name__:
            continue
        doc = (inspect.getdoc(fn) or "").split("\n\n")[0].replace("\n", " ")
        rows.append((name, str(inspect.signature(fn)).replace("reflex.event.", ""), doc))
    return rows


def props_table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Prop"),
                rx.table.column_header_cell("Type"),
                rx.table.column_header_cell("Description"),
            )
        ),
        rx.table.body(
            *[
                rx.table.row(
                    rx.table.cell(rx.code(name, size="2")),
                    rx.table.cell(
                        rx.text(kind, size="1", font_family="ui-monospace, monospace", color_scheme="gray")
                    ),
                    rx.table.cell(rx.text(desc, size="2")),
                )
                for name, kind, desc in _props()
            ]
        ),
        variant="surface",
        size="1",
        width="100%",
    )


def functions_table(title: str, module) -> rx.Component:
    return rx.box(
        rx.heading(title, size="4", margin="20px 0 8px"),
        rx.table.root(
            rx.table.body(
                *[
                    rx.table.row(
                        rx.table.cell(
                            rx.vstack(
                                rx.code(name, size="2"),
                                rx.text(
                                    sig, size="1", color_scheme="gray", font_family="ui-monospace, monospace"
                                ),
                                spacing="1",
                            )
                        ),
                        rx.table.cell(rx.text(doc, size="2")),
                    )
                    for name, sig, doc in _functions(module)
                ]
            ),
            variant="surface",
            size="1",
            width="100%",
        ),
    )


def api_page() -> rx.Component:
    return page_shell(
        section_title(
            f"API reference · reflex-mermaidjs {reflex_mermaidjs.__version__}",
            f"Wraps mermaid {reflex_mermaidjs.MERMAID_VERSION}. pip install reflex-mermaidjs",
        ),
        card(rx.code_block(USAGE, language="python", font_size="13px"), margin_bottom="24px"),
        rx.heading("mermaid(...) props", size="5", margin_bottom="8px"),
        props_table(),
        functions_table("Python actions (rx.call_script helpers)", actions),
        functions_table("Sharing helpers", urls),
        functions_table("Markdown", markdown),
    )
