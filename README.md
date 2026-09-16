# reflex-mermaidjs

[mermaid-js](https://mermaid.js.org) diagrams for [Reflex](https://reflex.dev): flowcharts, sequence, class, state, ER, gantt, mindmap, architecture, C4, sankey, kanban, venn, wardley, railroad and 30+ other diagram types, generated from text the way markdown is.

- Wraps **mermaid 12.0.0** (ELK layout bundled), plus the **tidy-tree** layout and **ZenUML** plugins
- Every mermaid option as a typed prop: `theme`, `look` (`classic` / `handDrawn` / `neo`), `layout`, `security_level`, `theme_variables`, raw `config`...
- `appearance="dark"` automatic dark themes (same behaviour as mermaid.live)
- **Pan & zoom** (wheel, drag, double-click to fit) with a floating toolbar and optional dotted grid
- Events: `on_render`, `on_error`, `on_node_click`, `on_zoom_change`
- Python actions: `zoom_in`, `zoom_out`, `set_zoom`, `fit_view`, `reset_view`, `fullscreen`, `export_png`, `export_svg`, `copy_svg`, `get_svg`
- Icons: Iconify `logos` and `mdi` bundled, any other Iconify pack by name, Font Awesome `fa:` icons
- KaTeX math (`$$...$$`) in labels
- `rx.markdown` integration: ```` ```mermaid ```` fences become diagrams
- Share helpers in pure Python: `mermaid_live_url`, `deserialize_state` (mermaid.live `pako:` links), `mermaid_ink_url`, `kroki_url`
- 36 diagram types of sample diagrams (`get_diagram_examples()`), the same set mermaid.live offers

## Installation

```bash
pip install reflex-mermaidjs
# or
uv add reflex-mermaidjs
```

Requires `reflex>=0.9.11`. npm dependencies (mermaid, plugins, icons) are installed automatically by Reflex.

## Quick start

```python
import reflex as rx
from reflex_mermaidjs import mermaid


def index() -> rx.Component:
    return mermaid(
        """flowchart TD
    A[Christmas] -->|Get money| B(Go shopping)
    B --> C{Let me think}
    C -->|One| D[Laptop]
    C -->|Two| E[iPhone]
    C -->|Three| F[fa:fa-car Car]""",
        theme="forest",
    )


app = rx.App()
app.add_page(index)
```

The diagram text can be passed positionally or as `chart=`, and can be a state var — the diagram re-renders when it changes.

## Live editing with state, pan & zoom and events

```python
import reflex as rx
from reflex_mermaidjs import mermaid, export_png, fit_view


class State(rx.State):
    code: str = "sequenceDiagram\n    Alice->>Bob: Hi Bob\n    Bob-->>Alice: Hi Alice"
    diagram_type: str = ""
    error: str = ""

    @rx.event
    def set_code(self, value: str):
        self.code = value

    @rx.event
    def rendered(self, event: dict):
        self.diagram_type = event["diagram_type"]
        self.error = ""

    @rx.event
    def failed(self, event: dict):
        self.error = event["message"]

    @rx.event
    def clicked(self, event: dict):
        return rx.toast.info(f"Clicked {event['node_id']}")


def index() -> rx.Component:
    return rx.hstack(
        rx.text_area(value=State.code, on_change=State.set_code.debounce(250), width="40%", rows="20"),
        rx.vstack(
            mermaid(
                State.code,
                id="diagram",
                appearance=rx.color_mode_cond("light", "dark"),
                pan_zoom=True,
                grid=True,
                node_click=True,
                error_mode="keep-last",
                on_render=State.rendered,
                on_error=State.failed,
                on_node_click=State.clicked,
                height="600px",
                width="100%",
            ),
            rx.hstack(
                rx.button("Fit", on_click=fit_view("diagram")),
                rx.button("PNG", on_click=export_png("diagram", "diagram.png")),
                rx.text(State.diagram_type),
            ),
            width="60%",
        ),
    )
```

## Props

| Prop | Type | Description |
| --- | --- | --- |
| `chart` | `str` | Diagram definition (front matter and `%%{init}%%` directives are supported) |
| `config` | `dict` | Raw [MermaidConfig](https://mermaid.js.org/config/schema-docs/config.html) passed to `mermaid.initialize` |
| `theme` | `default`, `base`, `dark`, `forest`, `neutral`, `neo`, `neo-dark`, `redux`, `redux-dark`, `redux-color`, `redux-dark-color`, `null` | Theme |
| `look` | `classic`, `handDrawn`, `neo` | Visual look |
| `layout` | `str` | `dagre`, `elk`, `elk.stress`, `elk.force`, `elk.mrtree`, `elk.radial`, `elk.box`, `elk.rectpacking`, `tidy-tree`... |
| `security_level` | `strict`, `loose`, `antiscript`, `sandbox` | `loose` enables `click` callbacks and HTML labels |
| `theme_variables` / `theme_css` | `dict` / `str` | Theme customisation (most useful with `theme="base"`) |
| `font_family`, `font_size`, `hand_drawn_seed`, `dark_mode`, `html_labels`, `wrap`, `max_text_size`, `max_edges`, `deterministic_ids`, `log_level` | | Same as the mermaid options |
| `appearance` | `light`, `dark` | With no explicit theme, `dark` uses the dark variant of each diagram type's default theme |
| `tidy_tree` | `bool` | Register the tidy-tree layout (default `True`) |
| `zenuml` | `bool` | Register ZenUML eagerly (it is auto-registered when the text starts with `zenuml`) |
| `font_awesome` | `bool` | Load Font Awesome CSS for `fa:` icons (default `True`) |
| `icon_packs` | `list[str \| dict]` | Iconify packs. `logos` and `mdi` are bundled; other names load from jsDelivr; or `{"name": ..., "url": ...}` |
| `pan_zoom` | `bool` | Wheel zoom + drag pan. The component fills its box, so give it a height (defaults to 480px) |
| `show_controls`, `controls_position` | `bool`, `top-right`... | Floating toolbar (fit, zoom out, zoom in, 100%, fullscreen) |
| `min_zoom`, `max_zoom`, `zoom_step`, `max_fit_zoom` | `float` | Zoom limits |
| `fit_on_render` | `bool \| "auto"` | `auto` fits on first render and when the diagram type/size changes a lot |
| `grid` | `bool` | Dotted background grid (color via the `--mermaid-grid-color` CSS variable) |
| `center` | `bool` | Center the SVG in static mode |
| `debounce` | `int` | Debounce re-renders in ms |
| `error_mode` | `inline`, `keep-last`, `none` | How parse errors are shown |
| `click_callbacks` | `list[str]` | Callback names used in `click node callback` directives, routed to `on_node_click` |
| `node_click` | `bool` | Emit `on_node_click` for any node click |

### Events

| Event | Payload |
| --- | --- |
| `on_render` | `{svg, diagram_type, render_id, render_ms}` |
| `on_error` | `{message, line, expected}` |
| `on_node_click` | `{node_id, callback, label, args}` |
| `on_zoom_change` | `{zoom, x, y}` (debounced) |

## Python actions

Any diagram with an `id` can be driven from event handlers or triggers. They return `rx.call_script` events:

```python
from reflex_mermaidjs import zoom_in, zoom_out, set_zoom, fit_view, reset_view, fullscreen
from reflex_mermaidjs import export_png, export_svg, copy_svg, get_svg, get_png_data_url

rx.button("PNG", on_click=export_png("diagram", "diagram.png", scale=2, background="transparent"))
rx.button("Send SVG to Python", on_click=get_svg("diagram", State.receive_svg))
```

## Markdown

```python
from reflex_mermaidjs import markdown_with_mermaid, mermaid_component_map

markdown_with_mermaid(State.text, mermaid_props={"theme": "neutral"})
# or merge with your own map
rx.markdown(State.text, component_map={**mermaid_component_map(), "h1": my_h1})
```

Non-mermaid code fences keep the regular `rx.code_block` highlighting.

## Sharing helpers

```python
from reflex_mermaidjs import mermaid_live_url, mermaid_ink_url, kroki_url, deserialize_state

mermaid_live_url(code, {"theme": "dark"})  # https://mermaid.live/edit#pako:...
mermaid_ink_url(code, fmt="img", image_type="png")  # server-rendered image
kroki_url(code, "svg")
state = deserialize_state("https://mermaid.live/edit#pako:eNp...")  # {"code": ..., "mermaid": ...}
```

## Icons

```python
mermaid("""architecture-beta
    group api(logos:aws-lambda)[API]
    service db(logos:postgresql)[Database] in api
    service server(logos:python)[Server] in api
    db:L -- R:server""")

mermaid(
    chart,
    icon_packs=["logos", "mdi", "fa7-brands", {"name": "custom", "url": "https://example.com/icons.json"}],
)
```

## Demo app

The `mermaidjs_demo/` app is a mermaid.live-style editor built with this component:

- **Live editor** — code editor with line numbers, config tab (theme/look/layout/security selectors + JSON), all sample diagrams, history, share dialog (mermaid.live / mermaid.ink / kroki links, import a mermaid.live link, Python and Markdown snippets), PNG/SVG export, hand-drawn/grid/pan-zoom toggles, dark mode
- **Gallery** — every diagram type rendered live
- **Features** — themes, looks, layouts, theme variables from state, data-driven charts, events and actions, markdown, icons, math, ZenUML, error handling
- **API** — props table generated from the source

```bash
uv venv && uv pip install -e ".[dev]"
cd mermaidjs_demo
uv run reflex run
```

## Development

```bash
uv pip install -e ".[dev]"
uv run pytest
uv run reflex component build   # generates .pyi stubs and builds dist/
```

## License

MIT © Ernesto Crespo
