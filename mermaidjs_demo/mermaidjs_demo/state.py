"""State for the mermaid live editor demo."""

from __future__ import annotations

import json
from datetime import datetime

import reflex as rx
from reflex_mermaidjs import (
    deserialize_state,
    get_diagram_examples,
    kroki_url,
    mermaid_ink_url,
    mermaid_live_url,
)

EXAMPLES = get_diagram_examples()
DEFAULT_CODE = next(e["code"] for e in EXAMPLES[0]["examples"] if e.get("isDefault"))
DIAGRAM_ID = "editor-diagram"


class EditorState(rx.State):
    """Everything the live editor needs."""

    code: str = DEFAULT_CODE
    rendered_code: str = DEFAULT_CODE
    config_text: str = "{\n}"
    applied_config: dict = {}
    config_error: str = ""

    theme: str = "auto"
    look: str = "auto"
    layout: str = "auto"
    security_level: str = "strict"

    auto_sync: bool = True
    pan_zoom: bool = True
    grid: bool = True
    node_click: bool = True

    left_tab: str = "code"
    samples_open: bool = True
    actions_open: bool = False

    diagram_type: str = ""
    render_ms: int = 0
    error: str = ""
    zoom: float = 1.0

    history: list[dict[str, str]] = []

    import_url: str = ""
    import_error: str = ""

    # ------------------------------------------------------------ computed vars
    @rx.var
    def line_numbers(self) -> list[int]:
        return list(range(1, self.code.count("\n") + 2))

    @rx.var
    def code_rows(self) -> int:
        return self.code.count("\n") + 2

    @rx.var
    def config_rows(self) -> int:
        return max(self.config_text.count("\n") + 2, 12)

    @rx.var
    def config_line_numbers(self) -> list[int]:
        return list(range(1, self.config_text.count("\n") + 2))

    @rx.var
    def mermaid_config(self) -> dict:
        config = dict(self.applied_config)
        if self.theme != "auto":
            config["theme"] = self.theme
        if self.look != "auto":
            config["look"] = self.look
        if self.layout != "auto":
            config["layout"] = self.layout
        config["securityLevel"] = self.security_level
        return config

    @rx.var
    def hand_drawn(self) -> bool:
        return self.look == "handDrawn"

    @rx.var
    def is_dirty(self) -> bool:
        return self.code != self.rendered_code

    @rx.var
    def live_url(self) -> str:
        return mermaid_live_url(self.code, self.mermaid_config, grid=self.grid, pan_zoom=self.pan_zoom)

    @rx.var
    def ink_svg_url(self) -> str:
        return mermaid_ink_url(self.code, self.mermaid_config, fmt="svg")

    @rx.var
    def ink_png_url(self) -> str:
        return mermaid_ink_url(self.code, self.mermaid_config, fmt="img", image_type="png")

    @rx.var
    def kroki_svg_url(self) -> str:
        return kroki_url(self.code)

    @rx.var
    def markdown_snippet(self) -> str:
        return f"```mermaid\n{self.code}\n```"

    @rx.var
    def python_snippet(self) -> str:
        config = json.dumps(self.mermaid_config)
        return (
            "from reflex_mermaidjs import mermaid\n\n"
            f'mermaid(\n    {json.dumps(self.code)},\n    config={config},\n    pan_zoom=True,\n    height="480px",\n)'
        )

    @rx.var
    def zoom_label(self) -> str:
        return f"{round(self.zoom * 100)}%"

    # ------------------------------------------------------------------ events
    @rx.event
    def set_code(self, value: str):
        self.code = value
        if self.auto_sync:
            self.rendered_code = value

    @rx.event
    def sync(self):
        self.rendered_code = self.code
        self._apply_config()

    @rx.event
    def set_config_text(self, value: str):
        self.config_text = value
        if self.auto_sync:
            self._apply_config()

    @rx.event
    def apply_config(self):
        self._apply_config()

    def _apply_config(self):
        text = self.config_text.strip() or "{}"
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            self.config_error = f"Invalid JSON: {exc.msg} (line {exc.lineno}, column {exc.colno})"
            return
        if not isinstance(parsed, dict):
            self.config_error = "The configuration must be a JSON object."
            return
        self.config_error = ""
        self.applied_config = parsed

    @rx.event
    def set_auto_sync(self, value: bool):
        self.auto_sync = value
        if value:
            self.rendered_code = self.code
            self._apply_config()

    @rx.event
    def set_theme(self, value: str):
        self.theme = value

    @rx.event
    def set_look(self, value: str):
        self.look = value

    @rx.event
    def set_layout(self, value: str):
        self.layout = value

    @rx.event
    def set_security_level(self, value: str):
        self.security_level = value

    @rx.event
    def toggle_hand_drawn(self):
        self.look = "classic" if self.look == "handDrawn" else "handDrawn"

    @rx.event
    def toggle_grid(self):
        self.grid = not self.grid

    @rx.event
    def set_pan_zoom(self, value: bool):
        self.pan_zoom = value

    @rx.event
    def set_node_click(self, value: bool):
        self.node_click = value

    @rx.event
    def set_left_tab(self, value: str):
        self.left_tab = value

    @rx.event
    def toggle_samples(self):
        self.samples_open = not self.samples_open

    @rx.event
    def toggle_actions(self):
        self.actions_open = not self.actions_open

    @rx.event
    def set_import_url(self, value: str):
        self.import_url = value

    def _load(self, code: str, config: dict | None = None, note: str = ""):
        self.code = code
        self.rendered_code = code
        if config is not None:
            self.applied_config = config
            self.config_text = json.dumps(config, indent=2) if config else "{\n}"
            self.config_error = ""
        self.error = ""
        if note:
            self._push_history(note)

    @rx.event
    def load_example(self, diagram_index: int, example_index: int = -1):
        self._load_example(diagram_index, example_index)

    def _load_example(self, diagram_index: int, example_index: int = -1):
        diagram = EXAMPLES[diagram_index]
        examples = diagram["examples"]
        if example_index < 0:
            example = next((e for e in examples if e.get("isDefault")), examples[0])
        else:
            example = examples[example_index]
        self._load(example["code"], note=f"{diagram['name']}: {example['title']}")

    @rx.event
    def open_in_editor(self, diagram_index: int, example_index: int = -1):
        self._load_example(diagram_index, example_index)
        return rx.redirect("/")

    @rx.event
    def load_code(self, code: str, note: str = "Loaded snippet"):
        self._load(code, note=note)
        return rx.redirect("/")

    # --------------------------------------------------------------- rendering
    @rx.event
    def on_render(self, event: dict):
        self.diagram_type = event.get("diagram_type", "")
        self.render_ms = int(event.get("render_ms", 0))
        self.error = ""

    @rx.event
    def on_error(self, event: dict):
        self.error = event.get("message", "")
        self.diagram_type = ""

    @rx.event
    def on_node_click(self, event: dict):
        label = event.get("label") or ""
        node = event.get("node_id") or "?"
        return rx.toast.info(f"Clicked node “{node}”", description=label[:80] or None, duration=2500)

    @rx.event
    def on_zoom(self, event: dict):
        self.zoom = float(event.get("zoom", 1))

    # ----------------------------------------------------------------- history
    def _push_history(self, note: str):
        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "note": note,
            "code": self.code,
            "config": json.dumps(self.applied_config),
        }
        self.history = [entry, *[h for h in self.history if h["code"] != self.code]][:25]

    @rx.event
    def save_to_history(self):
        first_line = self.code.strip().splitlines()[0] if self.code.strip() else "empty"
        self._push_history(f"Saved · {first_line[:40]}")
        return rx.toast.success("Saved to history")

    @rx.event
    def restore(self, index: int):
        entry = self.history[index]
        self._load(entry["code"], json.loads(entry["config"] or "{}"))

    @rx.event
    def clear_history(self):
        self.history = []

    # ------------------------------------------------------------------- share
    @rx.event
    def import_from_url(self):
        url = self.import_url.strip()
        if not url:
            self.import_error = "Paste a mermaid.live link first."
            return
        try:
            state = deserialize_state(url)
            config = json.loads(state.get("mermaid") or "{}")
        except Exception as exc:  # noqa: BLE001 - surface any decoding problem to the user
            self.import_error = f"Could not decode the link: {exc}"
            return
        self.import_error = ""
        self.import_url = ""
        self._load(state.get("code", ""), config, note="Imported from mermaid.live")
        return rx.toast.success("Diagram imported")

    @rx.event
    def reset_editor(self):
        self.theme = self.look = self.layout = "auto"
        self.security_level = "strict"
        self._load(DEFAULT_CODE, {}, note="Reset")
