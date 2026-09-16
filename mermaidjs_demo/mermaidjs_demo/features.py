"""Features tour: themes, looks, layouts, events, Python actions, markdown, icons..."""

from __future__ import annotations

import reflex as rx
from reflex_mermaidjs import (
    LOOKS,
    THEMES,
    export_png,
    export_svg,
    fit_view,
    get_svg,
    markdown_with_mermaid,
    mermaid,
    reset_view,
    set_zoom,
    zoom_in,
    zoom_out,
)

from .ui import card, page_shell, section_title

APPEARANCE = rx.color_mode_cond("light", "dark")

SMALL_FLOW = """flowchart LR
    A[Idea] --> B{Worth it?}
    B -->|Yes| C[Build]
    B -->|No| D[Drop]
    C --> E((Ship))"""

LAYOUT_FLOW = """flowchart TD
    A[Client] --> B[API Gateway]
    B --> C[Auth]
    B --> D[Orders]
    B --> E[Catalog]
    D --> F[(Orders DB)]
    E --> G[(Catalog DB)]
    D --> H[Payments]
    H --> I[Bank]
    C --> J[(Users DB)]"""

MINDMAP = """mindmap
  root((reflex-mermaidjs))
    Diagrams
      Flowchart
      Sequence
      Gantt
    Features
      Pan and zoom
      Export
      Events
    Integrations
      Markdown
      mermaid.live"""

CLICK_FLOW = """flowchart LR
    A[Python backend] -->|events| B[Reflex state]
    B --> C{on_node_click}
    C --> D[Toast]
    C --> E[Log]
    click A callback "Calls window.callback → on_node_click"
    click B callback "Also routed to Python"
    click E href "https://reflex.dev" "Plain links still work" _blank"""

ICONS_ARCH = """architecture-beta
    group api(logos:aws-lambda)[API]

    service db(logos:postgresql)[Database] in api
    service disk1(logos:aws-s3)[Storage] in api
    service disk2(logos:cloudflare)[CDN] in api
    service server(logos:python)[Reflex] in api

    db:L -- R:server
    disk1:T -- B:server
    disk2:T -- B:db"""

ICON_SHAPES = """flowchart LR
    py@{ icon: "logos:python", form: "square", label: "Python", pos: "b", h: 60 }
    rx@{ icon: "mdi:react", form: "circle", label: "React", pos: "b", h: 60 }
    mm@{ icon: "logos:mermaid", form: "rounded", label: "Mermaid", pos: "b", h: 60 }
    fa[fa:fa-car Font Awesome] --> py --> rx --> mm"""

MATH = """flowchart LR
    A["$$x^2$$"] -->|"$$\\sqrt{x+3}$$"| B("$$\\frac{1}{2}$$")
    A -->|"$$\\overbrace{a+b+c}^{\\text{note}}$$"| C("$$\\pi r^2$$")
    B --> D("$$x = \\begin{cases} a &\\text{if } b \\\\ c &\\text{if } d \\end{cases}$$")
    C --> E("$$\\int_0^\\infty e^{-x}\\,dx$$")"""

ZENUML = """zenuml
    title Order Service
    @Actor Client
    @Boundary OrderController
    @EC2 <<BFF>> OrderService
    group BusinessService {
      @Lambda PurchaseService
      @AzureFunction InvoiceService
    }
    @Starter(Client)
    OrderController.post(payload) {
      OrderService.create(payload) {
        order = new Order(payload)
        if(order != null) {
          par {
            PurchaseService.createPO(order)
            InvoiceService.createInvoice(order)
          }
        }
      }
    }"""

MARKDOWN = """# Release notes

Mermaid code fences inside `rx.markdown` become live diagrams:

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant R as Reflex
    participant M as mermaid
    U->>R: types markdown
    R->>M: render ```mermaid blocks
    M-->>U: SVG diagram
```

Other languages keep syntax highlighting:

```python
from reflex_mermaidjs import markdown_with_mermaid
markdown_with_mermaid(State.text)
```
"""

BROKEN = """flowchart TD
    A[Start] --> B{Is it valid?
    B -->|Yes| C[OK]"""


class FeaturesState(rx.State):
    """State for the features page."""

    events: list[str] = []
    zoom: float = 1.0
    svg_length: int = 0

    primary: str = "#ff3670"
    secondary: str = "#ffe3ea"
    line: str = "#6e56cf"

    frontend: int = 45
    backend: int = 35
    devops: int = 20

    markdown_text: str = MARKDOWN
    broken_code: str = BROKEN
    last_error: str = ""

    @rx.var
    def theme_variables(self) -> dict:
        return {
            "primaryColor": self.secondary,
            "primaryBorderColor": self.primary,
            "primaryTextColor": "#1a1a1a",
            "lineColor": self.line,
            "secondaryColor": "#e8f5e9",
            "tertiaryColor": "#fff8e1",
            "fontFamily": "Georgia, serif",
        }

    @rx.var
    def pie_code(self) -> str:
        return (
            "pie showData\n    title Sprint effort\n"
            f'    "Frontend" : {self.frontend}\n'
            f'    "Backend" : {self.backend}\n'
            f'    "DevOps" : {self.devops}'
        )

    @rx.var
    def xy_code(self) -> str:
        values = [self.frontend, self.backend, self.devops]
        return (
            'xychart-beta\n    title "Effort by area"\n'
            "    x-axis [Frontend, Backend, DevOps]\n"
            f'    y-axis "Hours" 0 --> {max(100, max(values))}\n'
            f"    bar [{', '.join(map(str, values))}]\n"
            f"    line [{', '.join(map(str, values))}]"
        )

    def _log(self, text: str):
        self.events = [text, *self.events][:8]

    @rx.event
    def node_clicked(self, event: dict):
        source = f"callback={event.get('callback')}" if event.get("callback") else "node_click"
        self._log(f"click · {event.get('node_id')} · {source}")

    @rx.event
    def zoom_changed(self, event: dict):
        self.zoom = float(event.get("zoom", 1))

    @rx.event
    def got_svg(self, svg: str | None):
        self.svg_length = len(svg or "")
        return rx.toast.info(f"Received {self.svg_length:,} characters of SVG in Python")

    @rx.event
    def set_primary(self, v: str):
        self.primary = v

    @rx.event
    def set_secondary(self, v: str):
        self.secondary = v

    @rx.event
    def set_line(self, v: str):
        self.line = v

    @rx.event
    def set_frontend(self, v: list[int | float]):
        self.frontend = int(v[0])

    @rx.event
    def set_backend(self, v: list[int | float]):
        self.backend = int(v[0])

    @rx.event
    def set_devops(self, v: list[int | float]):
        self.devops = int(v[0])

    @rx.event
    def set_markdown_text(self, v: str):
        self.markdown_text = v

    @rx.event
    def set_broken_code(self, v: str):
        self.broken_code = v

    @rx.event
    def on_error(self, event: dict):
        self.last_error = event.get("message", "")

    @rx.event
    def on_render(self, _event: dict):
        self.last_error = ""


def feature(title: str, subtitle: str, *children: rx.Component, anchor: str) -> rx.Component:
    return rx.box(
        section_title(title, subtitle), *children, id=anchor, margin_bottom="48px", scroll_margin_top="24px"
    )


def label(text: str) -> rx.Component:
    return rx.text(
        text,
        size="1",
        weight="bold",
        color_scheme="gray",
        font_family="ui-monospace, monospace",
        margin_bottom="6px",
    )


def themes_section() -> rx.Component:
    return feature(
        "Themes",
        "theme= accepts every built-in theme. Leave it unset and pass appearance='dark' to get mermaid.live's automatic dark variants.",
        rx.grid(
            *[card(label(f'theme="{t}"'), mermaid(SMALL_FLOW, theme=t)) for t in THEMES],
            columns=rx.breakpoints(initial="1", sm="2", lg="4"),
            spacing="3",
        ),
        anchor="themes",
    )


def looks_section() -> rx.Component:
    return feature(
        "Looks",
        "classic, handDrawn (rough.js) and neo.",
        rx.grid(
            *[
                card(
                    label(f'look="{look}"'),
                    mermaid(SMALL_FLOW, look=look, appearance=APPEARANCE, hand_drawn_seed=7),
                )
                for look in LOOKS
            ],
            columns=rx.breakpoints(initial="1", md="3"),
            spacing="3",
        ),
        anchor="looks",
    )


def layouts_section() -> rx.Component:
    return feature(
        "Layouts",
        "ELK is bundled with mermaid 12 and is now the default for flowcharts; tidy-tree is registered by the component.",
        rx.grid(
            card(
                label('layout="dagre"'),
                mermaid(LAYOUT_FLOW, layout="dagre", appearance=APPEARANCE, pan_zoom=True, height="320px"),
            ),
            card(
                label('layout="elk"'),
                mermaid(LAYOUT_FLOW, layout="elk", appearance=APPEARANCE, pan_zoom=True, height="320px"),
            ),
            card(
                label('layout="elk.stress"'),
                mermaid(
                    LAYOUT_FLOW, layout="elk.stress", appearance=APPEARANCE, pan_zoom=True, height="320px"
                ),
            ),
            card(
                label("mindmap · default (cose-bilkent)"),
                mermaid(MINDMAP, appearance=APPEARANCE, pan_zoom=True, height="320px"),
            ),
            card(
                label('mindmap · layout="tidy-tree"'),
                mermaid(MINDMAP, layout="tidy-tree", appearance=APPEARANCE, pan_zoom=True, height="320px"),
            ),
            columns=rx.breakpoints(initial="1", md="2", lg="3"),
            spacing="3",
        ),
        anchor="layouts",
    )


def color_input(text: str, value, on_change) -> rx.Component:
    return rx.hstack(
        rx.el.input(
            type="color",
            value=value,
            on_change=on_change.debounce(120),
            style={"width": "36px", "height": "28px", "border": "none", "background": "transparent"},
        ),
        rx.text(text, size="2"),
        align="center",
    )


def theme_variables_section() -> rx.Component:
    return feature(
        "Theme variables from state",
        "theme='base' + theme_variables bound to Reflex state vars.",
        rx.flex(
            card(
                rx.vstack(
                    color_input("primaryBorderColor", FeaturesState.primary, FeaturesState.set_primary),
                    color_input("primaryColor", FeaturesState.secondary, FeaturesState.set_secondary),
                    color_input("lineColor", FeaturesState.line, FeaturesState.set_line),
                    spacing="2",
                ),
                min_width="220px",
            ),
            card(
                mermaid(
                    LAYOUT_FLOW, theme="base", theme_variables=FeaturesState.theme_variables, layout="dagre"
                ),
                flex="1",
                background="white",
            ),
            gap="12px",
            direction=rx.breakpoints(initial="column", md="row"),
        ),
        anchor="theme-variables",
    )


def slider(text: str, value, on_change) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(text, size="2"), rx.spacer(), rx.text(value, size="2", weight="bold"), width="100%"
        ),
        rx.slider(default_value=[value], min=0, max=100, on_value_commit=on_change, width="100%"),
        width="100%",
        spacing="1",
    )


def data_section() -> rx.Component:
    return feature(
        "Data-driven diagrams",
        "The chart text is a computed var: move a slider and the pie and XY chart re-render.",
        rx.flex(
            card(
                rx.vstack(
                    slider("Frontend", FeaturesState.frontend, FeaturesState.set_frontend),
                    slider("Backend", FeaturesState.backend, FeaturesState.set_backend),
                    slider("DevOps", FeaturesState.devops, FeaturesState.set_devops),
                    rx.code_block(FeaturesState.pie_code, language="mermaid", font_size="12px", width="100%"),
                    spacing="4",
                    width="100%",
                ),
                min_width="260px",
            ),
            card(mermaid(FeaturesState.pie_code, appearance=APPEARANCE), flex="1"),
            card(mermaid(FeaturesState.xy_code, appearance=APPEARANCE), flex="1"),
            gap="12px",
            direction=rx.breakpoints(initial="column", lg="row"),
        ),
        anchor="data",
    )


def events_section() -> rx.Component:
    return feature(
        "Events & Python actions",
        "click directives (security_level='loose' + click_callbacks), generic node clicks, zoom events, and imperative helpers (zoom_in, fit_view, export_png, get_svg...).",
        rx.flex(
            card(
                mermaid(
                    CLICK_FLOW,
                    id="events-diagram",
                    security_level="loose",
                    click_callbacks=["callback"],
                    node_click=True,
                    pan_zoom=True,
                    grid=True,
                    appearance=APPEARANCE,
                    on_node_click=FeaturesState.node_clicked,
                    on_zoom_change=FeaturesState.zoom_changed,
                    height="340px",
                ),
                rx.flex(
                    rx.button(
                        rx.icon("zoom-in", size=14),
                        "zoom_in",
                        size="1",
                        variant="soft",
                        on_click=zoom_in("events-diagram"),
                    ),
                    rx.button(
                        rx.icon("zoom-out", size=14),
                        "zoom_out",
                        size="1",
                        variant="soft",
                        on_click=zoom_out("events-diagram"),
                    ),
                    rx.button(
                        "set_zoom(2)", size="1", variant="soft", on_click=set_zoom("events-diagram", 2)
                    ),
                    rx.button(
                        rx.icon("scan", size=14),
                        "fit_view",
                        size="1",
                        variant="soft",
                        on_click=fit_view("events-diagram"),
                    ),
                    rx.button("reset_view", size="1", variant="soft", on_click=reset_view("events-diagram")),
                    rx.button(
                        rx.icon("image", size=14),
                        "export_png",
                        size="1",
                        variant="soft",
                        on_click=export_png("events-diagram", "events.png"),
                    ),
                    rx.button(
                        rx.icon("file-code", size=14),
                        "export_svg",
                        size="1",
                        variant="soft",
                        on_click=export_svg("events-diagram", "events.svg"),
                    ),
                    rx.button(
                        rx.icon("braces", size=14),
                        "get_svg → state",
                        size="1",
                        variant="soft",
                        on_click=get_svg("events-diagram", FeaturesState.got_svg),
                    ),
                    wrap="wrap",
                    gap="6px",
                    margin_top="10px",
                ),
                flex="2",
            ),
            card(
                rx.hstack(
                    rx.text("Event log", weight="bold"),
                    rx.spacer(),
                    rx.badge("zoom ", FeaturesState.zoom, variant="soft"),
                    width="100%",
                ),
                rx.cond(
                    FeaturesState.events.length() == 0,
                    rx.text("Click a node in the diagram…", size="2", color_scheme="gray"),
                ),
                rx.vstack(
                    rx.foreach(FeaturesState.events, lambda e: rx.code(e, size="1", width="100%")),
                    spacing="1",
                    margin_top="8px",
                    width="100%",
                ),
                flex="1",
                min_width="260px",
            ),
            gap="12px",
            direction=rx.breakpoints(initial="column", md="row"),
        ),
        anchor="events",
    )


def markdown_section() -> rx.Component:
    return feature(
        "Markdown integration",
        "markdown_with_mermaid() / mermaid_component_map() render ```mermaid fences inside rx.markdown.",
        rx.grid(
            card(
                rx.text_area(
                    value=FeaturesState.markdown_text,
                    on_change=FeaturesState.set_markdown_text.debounce(300),
                    rows="22",
                    width="100%",
                    font_family="ui-monospace, monospace",
                    font_size="12px",
                )
            ),
            card(
                markdown_with_mermaid(FeaturesState.markdown_text, mermaid_props={"appearance": APPEARANCE})
            ),
            columns=rx.breakpoints(initial="1", md="2"),
            spacing="3",
        ),
        anchor="markdown",
    )


def icons_section() -> rx.Component:
    return feature(
        "Icons, math and plugins",
        "Iconify packs (logos, mdi) load lazily; Font Awesome fa: icons; KaTeX math; the ZenUML external diagram.",
        rx.grid(
            card(label("architecture-beta + logos icons"), mermaid(ICONS_ARCH, appearance=APPEARANCE)),
            card(label("icon shapes + fa:fa-car"), mermaid(ICON_SHAPES, appearance=APPEARANCE)),
            card(label("KaTeX math"), mermaid(MATH, appearance=APPEARANCE, layout="dagre")),
            card(label("zenuml (plugin)"), mermaid(ZENUML), background="white"),
            columns=rx.breakpoints(initial="1", md="2"),
            spacing="3",
        ),
        anchor="icons",
    )


def errors_section() -> rx.Component:
    return feature(
        "Error handling",
        "error_mode='inline' shows the parser message, 'keep-last' keeps the previous SVG, 'none' hides it. on_error sends details to Python.",
        rx.grid(
            card(
                label("edit me"),
                rx.text_area(
                    value=FeaturesState.broken_code,
                    on_change=FeaturesState.set_broken_code.debounce(300),
                    rows="6",
                    width="100%",
                    font_family="ui-monospace, monospace",
                ),
                rx.cond(
                    FeaturesState.last_error != "",
                    rx.callout(
                        FeaturesState.last_error, icon="bug", color_scheme="red", size="1", margin_top="8px"
                    ),
                    rx.callout(
                        "Renders fine — on_render cleared the error.",
                        icon="check",
                        color_scheme="green",
                        size="1",
                        margin_top="8px",
                    ),
                ),
            ),
            card(
                label('error_mode="inline"'),
                mermaid(
                    FeaturesState.broken_code,
                    appearance=APPEARANCE,
                    on_error=FeaturesState.on_error,
                    on_render=FeaturesState.on_render,
                ),
            ),
            card(
                label('error_mode="keep-last"'),
                mermaid(FeaturesState.broken_code, error_mode="keep-last", appearance=APPEARANCE),
            ),
            columns=rx.breakpoints(initial="1", md="3"),
            spacing="3",
        ),
        anchor="errors",
    )


TOC = [
    ("Themes", "themes"),
    ("Looks", "looks"),
    ("Layouts", "layouts"),
    ("Theme variables", "theme-variables"),
    ("Data-driven", "data"),
    ("Events & actions", "events"),
    ("Markdown", "markdown"),
    ("Icons & plugins", "icons"),
    ("Errors", "errors"),
]


def features_page() -> rx.Component:
    return page_shell(
        rx.vstack(
            rx.heading("reflex-mermaidjs features", size="8"),
            rx.text(
                "A tour of everything the component can do. Every diagram on this page is a mermaid(...) call.",
                color_scheme="gray",
            ),
            rx.flex(
                *[rx.link(rx.badge(t, variant="surface", size="2"), href=f"#{a}") for t, a in TOC],
                wrap="wrap",
                gap="6px",
            ),
            spacing="3",
            margin_bottom="36px",
        ),
        themes_section(),
        looks_section(),
        layouts_section(),
        theme_variables_section(),
        data_section(),
        events_section(),
        markdown_section(),
        icons_section(),
        errors_section(),
    )
