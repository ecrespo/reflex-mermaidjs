import reflex as rx
from reflex_mermaidjs import (
    DIAGRAM_KEYWORDS,
    LAYOUTS,
    MERMAID_VERSION,
    THEMES,
    Mermaid,
    actions,
    get_default_example,
    get_diagram_examples,
    markdown_with_mermaid,
    mermaid,
    mermaid_component_map,
)


class DemoState(rx.State):
    code: str = "graph TD; A-->B"

    @rx.event
    def rendered(self, event: dict):
        pass

    @rx.event
    def clicked(self, event: dict):
        pass

    @rx.event
    def got_svg(self, svg: str):
        pass


def test_library_points_to_shared_jsx():
    assert Mermaid.library.startswith("$/public/external/reflex_mermaidjs/")
    assert Mermaid.library.endswith("mermaid_diagram.jsx")
    assert Mermaid.tag == "MermaidDiagram"


def test_lib_dependencies_pin_mermaid():
    deps = Mermaid.create("graph TD; A-->B").lib_dependencies
    assert f"mermaid@{MERMAID_VERSION}" in deps
    assert any(d.startswith("@mermaid-js/layout-tidy-tree@") for d in deps)
    assert any(d.startswith("@mermaid-js/mermaid-zenuml@") for d in deps)


def test_positional_chart_and_props_render():
    comp = mermaid(
        DemoState.code,
        theme="forest",
        look="handDrawn",
        layout="elk",
        security_level="loose",
        pan_zoom=True,
        click_callbacks=["callback"],
        on_render=DemoState.rendered,
        on_node_click=DemoState.clicked,
    )
    rendered = str(comp)
    assert "MermaidDiagram" in rendered
    for js_prop in (
        "chart:",
        "theme:",
        "look:",
        "layout:",
        "securityLevel:",
        "panZoom:",
        "clickCallbacks:",
        "onRender:",
        "onNodeClick:",
    ):
        assert js_prop in rendered, js_prop
    # pan_zoom without an explicit height gets a default one.
    assert "480px" in rendered


def test_static_string_chart():
    rendered = str(mermaid("sequenceDiagram\n  A->>B: hi", id="seq"))
    assert "sequenceDiagram" in rendered


def test_examples_cover_all_diagram_types():
    examples = get_diagram_examples()
    ids = {d["id"] for d in examples}
    assert len(examples) >= 36
    for expected in (
        "flowchart-v2",
        "sequence",
        "classDiagram",
        "er",
        "gantt",
        "zenuml",
        "agentflow",
        "swimlane",
        "venn",
        "wardley",
    ):
        assert expected in ids
    for diagram in examples:
        assert diagram["examples"], diagram["id"]
        assert all(e["code"].strip() for e in diagram["examples"])
    assert get_default_example("flowchart-v2").startswith("flowchart TD")


def test_constants():
    assert "redux-dark-color" in THEMES
    assert "tidy-tree" in LAYOUTS and "elk" in LAYOUTS
    assert DIAGRAM_KEYWORDS["sequence"] == "sequenceDiagram"


def test_actions_return_call_script():
    for spec in (
        actions.zoom_in("d"),
        actions.zoom_out("d"),
        actions.set_zoom("d", 2),
        actions.fit_view("d"),
        actions.reset_view("d"),
        actions.export_svg("d", "x.svg"),
        actions.export_png("d", "x.png", 3, "transparent"),
        actions.copy_svg("d"),
        actions.fullscreen("d"),
    ):
        assert isinstance(spec, rx.event.EventSpec)
    script = str(actions.export_png("my-diagram", "out.png", 3, "transparent").args)
    assert "__reflexMermaid" in script and "my-diagram" in script and "exportPng" in script
    assert isinstance(actions.get_svg("d", DemoState.got_svg), rx.event.EventSpec)


def test_markdown_integration_compiles():
    cmap = mermaid_component_map(theme="dark")
    assert "pre" in cmap
    md = markdown_with_mermaid("# Hi\n\n```mermaid\ngraph TD; A-->B\n```")
    pre_fn = str(md.children[0].format_component_map()["pre"])
    assert "MermaidDiagram" in pre_fn
    assert "mermaid" in pre_fn and "_language" in pre_fn
