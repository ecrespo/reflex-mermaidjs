"""Shared layout pieces: logo, navigation drawer and page shell."""

from __future__ import annotations

import reflex as rx
from reflex_mermaidjs import MERMAID_VERSION

ACCENT = "#ff3670"
REPO_URL = "https://github.com/ecrespo/reflex-mermaidjs"

NAV_ITEMS = [
    ("Live Editor", "/", "pencil-ruler"),
    ("Gallery", "/gallery", "layout-grid"),
    ("Features", "/features", "sparkles"),
    ("API reference", "/api", "book-open"),
]


def logo() -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.center(
                rx.icon("waypoints", size=18, color="white"),
                background=ACCENT,
                border_radius="6px",
                width="28px",
                height="28px",
            ),
            rx.text("Mermaid", color=ACCENT, weight="medium", size="4"),
            rx.text("× Reflex Live Editor", color=ACCENT, size="4", display=["none", "none", "inline"]),
            align="center",
            spacing="2",
        ),
        href="/",
        underline="none",
    )


def nav_drawer() -> rx.Component:
    return rx.drawer.root(
        rx.drawer.trigger(rx.icon_button(rx.icon("menu"), variant="ghost", size="3", aria_label="Menu")),
        rx.drawer.overlay(z_index="40"),
        rx.drawer.portal(
            rx.drawer.content(
                rx.vstack(
                    rx.hstack(
                        logo(),
                        rx.spacer(),
                        rx.drawer.close(rx.icon_button(rx.icon("x"), variant="ghost")),
                        width="100%",
                    ),
                    rx.divider(),
                    *[
                        rx.drawer.close(
                            rx.link(
                                rx.hstack(
                                    rx.icon(icon, size=18), rx.text(label), spacing="3", align="center"
                                ),
                                href=href,
                                underline="none",
                                color=rx.color("gray", 12),
                                padding="8px",
                                border_radius="8px",
                                width="100%",
                                _hover={"background": rx.color("gray", 3)},
                            )
                        )
                        for label, href, icon in NAV_ITEMS
                    ],
                    rx.spacer(),
                    rx.text(f"mermaid v{MERMAID_VERSION}", size="1", color_scheme="gray"),
                    rx.link("Source on GitHub", href=REPO_URL, is_external=True, size="2"),
                    spacing="2",
                    height="100%",
                    width="100%",
                    padding="16px",
                ),
                width="280px",
                height="100%",
                background=rx.color("gray", 2),
                top="0",
                left="0",
                position="fixed",
                z_index="50",
            )
        ),
        direction="left",
    )


def navbar(*right: rx.Component) -> rx.Component:
    return rx.hstack(
        nav_drawer(),
        logo(),
        rx.spacer(),
        *right,
        rx.tooltip(
            rx.link(
                rx.icon_button(rx.icon("code-xml"), variant="ghost", size="3"),
                href=REPO_URL,
                is_external=True,
            ),
            content="Source code",
        ),
        rx.tooltip(
            rx.icon_button(
                rx.color_mode_cond(rx.icon("moon"), rx.icon("sun")),
                on_click=rx.toggle_color_mode,
                variant="ghost",
                size="3",
            ),
            content="Toggle dark mode",
        ),
        align="center",
        spacing="3",
        padding_x="20px",
        height="64px",
        width="100%",
        border_bottom=f"1px solid {rx.color('gray', 4)}",
        background=rx.color("gray", 1),
    )


def page_shell(*children: rx.Component, **props) -> rx.Component:
    return rx.box(
        navbar(),
        rx.box(
            *children,
            padding=["16px", "24px", "32px"],
            max_width="1400px",
            margin="0 auto",
            width="100%",
            **props,
        ),
        min_height="100vh",
        background=rx.color("gray", 1),
    )


def section_title(title: str, subtitle: str = "") -> rx.Component:
    return rx.vstack(
        rx.heading(title, size="6"),
        rx.cond(subtitle != "", rx.text(subtitle, color_scheme="gray", size="2")),
        spacing="1",
        margin_bottom="12px",
    )


def card(*children: rx.Component, **props) -> rx.Component:
    style = {
        "border": f"1px solid {rx.color('gray', 4)}",
        "border_radius": "14px",
        "background": rx.color("gray", 2),
        "padding": "16px",
        **props,
    }
    return rx.box(*children, **style)
