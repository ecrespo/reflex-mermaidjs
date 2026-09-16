"""The live editor page, modelled after https://mermaid.live."""

from __future__ import annotations

import reflex as rx
from reflex_mermaidjs import (
    LAYOUTS,
    LOOKS,
    MERMAID_VERSION,
    SECURITY_LEVELS,
    THEMES,
    copy_svg,
    export_png,
    export_svg,
    mermaid,
)

from .state import DIAGRAM_ID, EXAMPLES, EditorState
from .ui import ACCENT, navbar

MONO = "'JetBrains Mono', 'Fira Code', ui-monospace, SFMono-Regular, Menlo, monospace"
PANEL_BG = rx.color("gray", 2)
BORDER = f"1px solid {rx.color('gray', 4)}"


# ----------------------------------------------------------------------- header
def history_popover() -> rx.Component:
    return rx.popover.root(
        rx.popover.trigger(
            rx.box(
                rx.tooltip(
                    rx.icon_button(rx.icon("history", size=20), variant="ghost", size="3"), content="History"
                )
            ),
        ),
        rx.popover.content(
            rx.vstack(
                rx.hstack(
                    rx.text("History", weight="bold"),
                    rx.spacer(),
                    rx.button(
                        rx.icon("bookmark-plus", size=14),
                        "Save current",
                        size="1",
                        variant="soft",
                        on_click=EditorState.save_to_history,
                    ),
                    rx.button(
                        "Clear",
                        size="1",
                        variant="ghost",
                        color_scheme="gray",
                        on_click=EditorState.clear_history,
                    ),
                    width="100%",
                    align="center",
                ),
                rx.cond(
                    EditorState.history.length() == 0,
                    rx.text(
                        "Nothing saved yet. Loaded samples and imports appear here.",
                        size="2",
                        color_scheme="gray",
                    ),
                ),
                rx.scroll_area(
                    rx.vstack(
                        rx.foreach(
                            EditorState.history,
                            lambda entry, i: rx.popover.close(
                                rx.hstack(
                                    rx.text(entry["time"], size="1", color_scheme="gray", font_family=MONO),
                                    rx.text(
                                        entry["note"],
                                        size="2",
                                        trim="both",
                                        overflow="hidden",
                                        text_overflow="ellipsis",
                                        white_space="nowrap",
                                    ),
                                    spacing="3",
                                    align="center",
                                    width="100%",
                                    padding="6px 8px",
                                    border_radius="8px",
                                    cursor="pointer",
                                    _hover={"background": rx.color("accent", 3)},
                                    on_click=EditorState.restore(i),
                                )
                            ),
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    max_height="320px",
                    type="auto",
                ),
                width="100%",
                spacing="2",
            ),
            width="380px",
        ),
    )


def copy_row(label: str, value: rx.Var[str]) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="1", weight="medium", color_scheme="gray"),
        rx.hstack(
            rx.input(value=value, read_only=True, size="2", width="100%", font_family=MONO),
            rx.tooltip(
                rx.icon_button(
                    rx.icon("copy", size=14),
                    variant="soft",
                    on_click=[rx.set_clipboard(value), rx.toast.success(f"{label} copied")],
                ),
                content="Copy",
            ),
            rx.tooltip(
                rx.link(
                    rx.icon_button(rx.icon("external-link", size=14), variant="soft"),
                    href=value,
                    is_external=True,
                ),
                content="Open",
            ),
            width="100%",
        ),
        spacing="1",
        width="100%",
    )


def share_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(rx.button("Share", variant="soft", color_scheme="gray", size="2")),
        rx.dialog.content(
            rx.dialog.title("Share diagram"),
            rx.dialog.description(
                "Links are generated in Python with reflex_mermaidjs.mermaid_live_url / mermaid_ink_url / kroki_url.",
                size="2",
                margin_bottom="12px",
            ),
            rx.vstack(
                copy_row("mermaid.live editor link", EditorState.live_url),
                copy_row("mermaid.ink SVG", EditorState.ink_svg_url),
                copy_row("mermaid.ink PNG", EditorState.ink_png_url),
                copy_row("kroki.io SVG", EditorState.kroki_svg_url),
                rx.divider(),
                rx.text("Import from a mermaid.live link", size="2", weight="bold"),
                rx.hstack(
                    rx.input(
                        placeholder="https://mermaid.live/edit#pako:…",
                        value=EditorState.import_url,
                        on_change=EditorState.set_import_url,
                        width="100%",
                    ),
                    rx.dialog.close(rx.button("Import", on_click=EditorState.import_from_url)),
                    width="100%",
                ),
                rx.cond(
                    EditorState.import_error != "",
                    rx.callout(EditorState.import_error, color_scheme="red", size="1", icon="triangle-alert"),
                ),
                rx.divider(),
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("Python", value="py"), rx.tabs.trigger("Markdown", value="md")
                    ),
                    rx.tabs.content(
                        rx.code_block(EditorState.python_snippet, language="python", font_size="12px"),
                        value="py",
                    ),
                    rx.tabs.content(
                        rx.code_block(EditorState.markdown_snippet, language="markdown", font_size="12px"),
                        value="md",
                    ),
                    default_value="py",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            rx.flex(
                rx.dialog.close(rx.button("Close", variant="soft", color_scheme="gray")),
                justify="end",
                margin_top="16px",
            ),
            max_width="640px",
        ),
    )


def save_menu() -> rx.Component:
    return rx.menu.root(
        rx.menu.trigger(
            rx.button(
                rx.icon("download", size=16),
                "Save diagram",
                size="2",
                style={"background": ACCENT, "color": "white"},
            ),
        ),
        rx.menu.content(
            rx.menu.item(
                rx.icon("image", size=14),
                "PNG",
                on_click=export_png(DIAGRAM_ID, "mermaid-diagram.png", 2, "white"),
            ),
            rx.menu.item(
                rx.icon("image-off", size=14),
                "PNG (transparent)",
                on_click=export_png(DIAGRAM_ID, "mermaid-diagram.png", 2, "transparent"),
            ),
            rx.menu.item(
                rx.icon("file-code", size=14), "SVG", on_click=export_svg(DIAGRAM_ID, "mermaid-diagram.svg")
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.icon("clipboard", size=14),
                "Copy SVG markup",
                on_click=[copy_svg(DIAGRAM_ID), rx.toast.success("SVG copied")],
            ),
            rx.menu.item(
                rx.icon("clipboard-type", size=14),
                "Copy code",
                on_click=[rx.set_clipboard(EditorState.code), rx.toast.success("Code copied")],
            ),
            rx.menu.item(
                rx.icon("file-down", size=14),
                "Download .mmd",
                on_click=rx.download(data=EditorState.code, filename="diagram.mmd"),
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.icon("bookmark-plus", size=14), "Save to history", on_click=EditorState.save_to_history
            ),
        ),
    )


# ------------------------------------------------------------------ left panel
def numbered_textarea(value, on_change, line_numbers, rows, **props) -> rx.Component:
    """A monospace textarea with a synced line-number gutter."""
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.foreach(
                    line_numbers,
                    lambda n: rx.text(n, as_="div", line_height="22px", size="1", font_family=MONO),
                ),
                spacing="0",
                align="end",
                padding="8px 10px 8px 8px",
                min_width="44px",
                color=rx.color("gray", 9),
                user_select="none",
                position="sticky",
                left="0",
                background=rx.color("gray", 2),
            ),
            rx.el.textarea(
                value=value,
                on_change=on_change,
                rows=rows,
                spell_check=False,
                wrap="off",
                auto_complete="off",
                auto_capitalize="off",
                style={
                    "fontFamily": MONO,
                    "fontSize": "13px",
                    "lineHeight": "22px",
                    "padding": "8px 8px 8px 4px",
                    "border": "none",
                    "outline": "none",
                    "resize": "none",
                    "background": "transparent",
                    "color": "var(--gray-12)",
                    "width": "100%",
                    "flex": "1",
                    "minWidth": "0",
                    "overflowX": "auto",
                    "overflowY": "hidden",
                    "whiteSpace": "pre",
                    "tabSize": "4",
                },
                **props,
            ),
            spacing="0",
            align="start",
            width="100%",
        ),
        overflow="auto",
        height="100%",
        width="100%",
    )


def code_editor() -> rx.Component:
    return rx.box(
        rx.cond(
            EditorState.left_tab == "code",
            numbered_textarea(
                EditorState.code,
                EditorState.set_code.debounce(250),
                EditorState.line_numbers,
                EditorState.code_rows,
                id="code-editor",
            ),
            config_editor(),
        ),
        flex="1",
        min_height="0",
        width="100%",
        background=rx.color("gray", 2),
        border_top=BORDER,
    )


def labeled_select(label: str, options: list[str], value, on_change) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="1", color_scheme="gray", weight="medium"),
        rx.select(["auto", *options], value=value, on_change=on_change, size="1", width="100%"),
        spacing="1",
        width="100%",
    )


def config_editor() -> rx.Component:
    return rx.vstack(
        rx.grid(
            labeled_select("Theme", THEMES, EditorState.theme, EditorState.set_theme),
            labeled_select("Look", LOOKS, EditorState.look, EditorState.set_look),
            labeled_select("Layout", LAYOUTS, EditorState.layout, EditorState.set_layout),
            rx.vstack(
                rx.text("Security", size="1", color_scheme="gray", weight="medium"),
                rx.select(
                    SECURITY_LEVELS,
                    value=EditorState.security_level,
                    on_change=EditorState.set_security_level,
                    size="1",
                    width="100%",
                ),
                spacing="1",
                width="100%",
            ),
            columns="4",
            spacing="2",
            width="100%",
            padding="10px 12px 0",
        ),
        rx.text(
            "MermaidConfig (JSON) — merged under the selectors above",
            size="1",
            color_scheme="gray",
            padding_x="12px",
        ),
        rx.box(
            numbered_textarea(
                EditorState.config_text,
                EditorState.set_config_text.debounce(400),
                EditorState.config_line_numbers,
                EditorState.config_rows,
                id="config-editor",
            ),
            flex="1",
            min_height="0",
            width="100%",
        ),
        rx.cond(
            EditorState.config_error != "",
            rx.callout(
                EditorState.config_error,
                icon="triangle-alert",
                color_scheme="red",
                size="1",
                margin="0 12px 8px",
            ),
        ),
        spacing="2",
        height="100%",
        width="100%",
    )


def tab_button(label: str, value: str, icon: str) -> rx.Component:
    active = EditorState.left_tab == value
    return rx.button(
        rx.icon(icon, size=16),
        label,
        variant="ghost",
        size="2",
        color=rx.cond(active, rx.color("gray", 12), rx.color("gray", 10)),
        border_bottom=rx.cond(active, f"2px solid {ACCENT}", "2px solid transparent"),
        border_radius="0",
        padding_y="18px",
        on_click=EditorState.set_left_tab(value),
    )


def editor_card() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            tab_button("Code", "code", "square-code"),
            tab_button("Config", "config", "settings"),
            rx.spacer(),
            rx.cond(
                EditorState.is_dirty,
                rx.tooltip(
                    rx.badge("unsynced", color_scheme="amber", variant="soft"), content="Auto sync is off"
                ),
            ),
            rx.link(
                rx.button(
                    rx.icon("book-open", size=16),
                    "Docs",
                    variant="ghost",
                    size="2",
                    color=rx.color("gray", 11),
                ),
                href="https://mermaid.js.org/intro/",
                is_external=True,
            ),
            padding_x="12px",
            width="100%",
            align="center",
        ),
        code_editor(),
        rx.hstack(
            rx.cond(
                EditorState.error != "",
                rx.hstack(
                    rx.icon("circle-x", size=14, color=rx.color("red", 10)),
                    rx.text("Syntax error", size="1", color=rx.color("red", 10)),
                    spacing="1",
                    align="center",
                ),
                rx.hstack(
                    rx.icon("circle-check", size=14, color=rx.color("green", 10)),
                    rx.text(EditorState.diagram_type, size="1", font_family=MONO),
                    rx.text("·", size="1", color_scheme="gray"),
                    rx.text(EditorState.render_ms, "ms", size="1", color_scheme="gray"),
                    spacing="1",
                    align="center",
                ),
            ),
            rx.spacer(),
            rx.text(EditorState.line_numbers.length(), " lines", size="1", color_scheme="gray"),
            padding="6px 12px",
            border_top=BORDER,
            width="100%",
        ),
        spacing="0",
        border=BORDER,
        border_radius="14px",
        background=PANEL_BG,
        overflow="hidden",
        flex="1",
        min_height="260px",
        width="100%",
    )


def sample_button(diagram, index: int) -> rx.Component:
    return rx.hstack(
        rx.button(
            diagram["name"].replace(" Diagram", "").replace("Diagram (", "("),
            on_click=EditorState.load_example(index, -1),
            size="1",
            variant="soft",
            color_scheme="indigo",
            flex="1",
            border_radius="8px 0 0 8px",
            white_space="nowrap",
            title=diagram["description"],
        ),
        rx.menu.root(
            rx.menu.trigger(
                rx.icon_button(
                    rx.icon("chevron-down", size=14),
                    size="1",
                    variant="soft",
                    color_scheme="indigo",
                    border_radius="0 8px 8px 0",
                ),
            ),
            rx.menu.content(
                rx.text(diagram["name"], size="1", weight="bold", color_scheme="gray", padding="4px 8px"),
                *[
                    rx.menu.item(example["title"], on_click=EditorState.load_example(index, j))
                    for j, example in enumerate(diagram["examples"])
                ],
            ),
        ),
        spacing="0",
        flex="1 1 auto",
    )


def collapsible(title: str, icon: str, is_open, on_toggle, body: rx.Component) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.icon(icon, size=18),
            rx.text(title, size="3", weight="medium"),
            rx.spacer(),
            rx.cond(is_open, rx.icon("chevrons-down-up", size=16), rx.icon("chevrons-up-down", size=16)),
            on_click=on_toggle,
            cursor="pointer",
            padding="12px 14px",
            align="center",
            width="100%",
        ),
        rx.cond(is_open, rx.box(body, padding="0 12px 12px")),
        border=BORDER,
        border_radius="14px",
        background=PANEL_BG,
        width="100%",
    )


def samples_panel() -> rx.Component:
    return collapsible(
        "Sample Diagrams",
        "network",
        EditorState.samples_open,
        EditorState.toggle_samples,
        rx.scroll_area(
            rx.flex(*[sample_button(d, i) for i, d in enumerate(EXAMPLES)], wrap="wrap", gap="8px"),
            max_height="210px",
            type="auto",
            scrollbars="vertical",
        ),
    )


def switch_row(label: str, checked, on_change, hint: str = "") -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text(label, size="2"),
            rx.cond(hint != "", rx.text(hint, size="1", color_scheme="gray")),
            spacing="0",
        ),
        rx.spacer(),
        rx.switch(checked=checked, on_change=on_change),
        width="100%",
        align="center",
    )


def actions_panel() -> rx.Component:
    return collapsible(
        "Actions",
        "square-arrow-up",
        EditorState.actions_open,
        EditorState.toggle_actions,
        rx.vstack(
            switch_row("Auto sync", EditorState.auto_sync, EditorState.set_auto_sync, "Render while typing"),
            rx.cond(
                ~EditorState.auto_sync,
                rx.button(
                    rx.icon("refresh-cw", size=14),
                    "Sync diagram",
                    on_click=EditorState.sync,
                    size="1",
                    width="100%",
                ),
            ),
            switch_row(
                "Pan & zoom", EditorState.pan_zoom, EditorState.set_pan_zoom, "Wheel to zoom, drag to pan"
            ),
            switch_row(
                "Node click events",
                EditorState.node_click,
                EditorState.set_node_click,
                "on_node_click → toast",
            ),
            rx.grid(
                rx.button(
                    rx.icon("image", size=14),
                    "PNG",
                    size="1",
                    variant="soft",
                    on_click=export_png(DIAGRAM_ID, "mermaid-diagram.png"),
                ),
                rx.button(
                    rx.icon("file-code", size=14),
                    "SVG",
                    size="1",
                    variant="soft",
                    on_click=export_svg(DIAGRAM_ID, "mermaid-diagram.svg"),
                ),
                rx.link(
                    rx.button(
                        rx.icon("external-link", size=14),
                        "mermaid.live",
                        size="1",
                        variant="soft",
                        width="100%",
                    ),
                    href=EditorState.live_url,
                    is_external=True,
                ),
                rx.button(
                    rx.icon("rotate-ccw", size=14),
                    "Reset",
                    size="1",
                    variant="soft",
                    color_scheme="gray",
                    on_click=EditorState.reset_editor,
                ),
                columns="2",
                spacing="2",
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
    )


def left_panel() -> rx.Component:
    return rx.vstack(
        editor_card(),
        samples_panel(),
        actions_panel(),
        spacing="4",
        width=["100%", "100%", "40%", "36%"],
        min_width=["auto", "auto", "420px"],
        height=["auto", "auto", "100%"],
        padding=["12px", "16px", "0 0 0 24px"],
    )


# ----------------------------------------------------------------- right panel
def floating(child: rx.Component, **position) -> rx.Component:
    return rx.box(
        child,
        position="absolute",
        z_index="5",
        background=rx.color("gray", 3),
        border=BORDER,
        border_radius="12px",
        padding="4px",
        **position,
    )


def toggle_icon(icon: str, active, on_click, tip: str) -> rx.Component:
    return rx.tooltip(
        rx.icon_button(
            rx.icon(icon, size=18),
            on_click=on_click,
            variant=rx.cond(active, "solid", "ghost"),
            color_scheme=rx.cond(active, "indigo", "gray"),
            size="2",
        ),
        content=tip,
    )


def canvas() -> rx.Component:
    return rx.box(
        mermaid(
            EditorState.rendered_code,
            id=DIAGRAM_ID,
            config=EditorState.mermaid_config,
            appearance=rx.color_mode_cond("light", "dark"),
            pan_zoom=EditorState.pan_zoom,
            grid=EditorState.grid,
            fit_on_render="auto",
            node_click=EditorState.node_click,
            controls_position="top-right",
            error_mode="keep-last",
            debounce=150,
            on_render=EditorState.on_render,
            on_error=EditorState.on_error,
            on_node_click=EditorState.on_node_click,
            on_zoom_change=EditorState.on_zoom,
            height="100%",
            width="100%",
            overflow=rx.cond(EditorState.pan_zoom, "hidden", "auto"),
            style={"--mermaid-grid-color": rx.color("gray", 6), "--mermaid-controls-bg": rx.color("gray", 3)},
        ),
        floating(
            rx.hstack(
                rx.badge(
                    rx.icon("shapes", size=12),
                    rx.cond(EditorState.diagram_type != "", EditorState.diagram_type, "…"),
                    variant="soft",
                    color_scheme="pink",
                    size="2",
                ),
                rx.cond(
                    EditorState.pan_zoom,
                    rx.badge(EditorState.zoom_label, variant="outline", color_scheme="gray", size="2"),
                ),
                spacing="2",
                padding="2px 4px",
            ),
            top="12px",
            left="12px",
        ),
        floating(
            rx.hstack(
                toggle_icon(
                    "pen-tool", EditorState.hand_drawn, EditorState.toggle_hand_drawn, "Hand-drawn look"
                ),
                toggle_icon("grid-3x3", EditorState.grid, EditorState.toggle_grid, "Grid"),
                toggle_icon(
                    "move",
                    EditorState.pan_zoom,
                    EditorState.set_pan_zoom(~EditorState.pan_zoom),
                    "Pan & zoom",
                ),
                spacing="1",
            ),
            bottom="16px",
            left="16px",
        ),
        floating(
            rx.hstack(
                rx.text(f"v{MERMAID_VERSION}", size="2", color_scheme="gray", padding_x="8px"),
                rx.popover.root(
                    rx.popover.trigger(
                        rx.box(
                            rx.tooltip(
                                rx.icon_button(rx.icon("shield-check", size=18), variant="ghost", size="2"),
                                content="Security level",
                            )
                        ),
                    ),
                    rx.popover.content(
                        rx.vstack(
                            rx.text("securityLevel", weight="bold", size="2"),
                            rx.radio_group(
                                SECURITY_LEVELS,
                                value=EditorState.security_level,
                                on_change=EditorState.set_security_level,
                                direction="column",
                            ),
                            rx.text(
                                "'loose' enables click callbacks and HTML labels.",
                                size="1",
                                color_scheme="gray",
                            ),
                            spacing="2",
                        ),
                    ),
                ),
                rx.tooltip(
                    rx.icon_button(
                        rx.color_mode_cond(rx.icon("moon", size=18), rx.icon("sun", size=18)),
                        on_click=rx.toggle_color_mode,
                        variant="ghost",
                        size="2",
                    ),
                    content="Toggle theme",
                ),
                spacing="1",
                align="center",
            ),
            bottom="16px",
            right="16px",
        ),
        position="relative",
        flex="1",
        height=["70vh", "70vh", "100%"],
        min_height="420px",
        margin=["0 12px 12px", "0 16px 16px", "0 24px 0 0"],
        border=BORDER,
        border_radius="14px",
        overflow="hidden",
        background=rx.color("gray", 1),
    )


def editor_page() -> rx.Component:
    return rx.vstack(
        rx.box(
            navbar(history_popover(), share_dialog(), save_menu()),
            width="100%",
        ),
        rx.flex(
            left_panel(),
            canvas(),
            direction=rx.breakpoints(initial="column", md="row"),
            spacing="5",
            width="100%",
            flex="1",
            min_height="0",
            padding_y=["0", "0", "20px"],
        ),
        spacing="0",
        height=["auto", "auto", "100vh"],
        width="100%",
        background=rx.color("gray", 1),
    )
