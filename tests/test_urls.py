import json
import zlib

import pytest
from reflex_mermaidjs import (
    build_state,
    deserialize_state,
    kroki_url,
    mermaid_ink_url,
    mermaid_live_url,
    pako_decode,
    pako_encode,
    serialize_state,
)

CODE = "flowchart TD\n    A[Christmas] -->|Get money| B(Go shopping)\n    B --> C{Let me think}"


def test_pako_roundtrip_unicode():
    text = "graph LR\n  A[Café ☕] --> B[日本語]"
    encoded = pako_encode(text)
    assert "=" not in encoded and "+" not in encoded and "/" not in encoded
    assert pako_decode(encoded) == text


def test_pako_is_zlib_compatible():
    encoded = pako_encode("hello")
    import base64

    raw = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    assert zlib.decompress(raw) == b"hello"


def test_state_roundtrip():
    state = build_state(CODE, {"theme": "forest"}, rough=True)
    serialized = serialize_state(state)
    assert serialized.startswith("pako:")
    assert deserialize_state(serialized) == state
    assert json.loads(state["mermaid"]) == {"theme": "forest"}


def test_base64_state_roundtrip():
    state = build_state(CODE)
    assert deserialize_state(serialize_state(state, "base64")) == state


def test_deserialize_full_url():
    url = mermaid_live_url(CODE, {"look": "handDrawn"})
    assert url.startswith("https://mermaid.live/edit#pako:")
    state = deserialize_state(url)
    assert state["code"] == CODE
    assert json.loads(state["mermaid"]) == {"look": "handDrawn"}


def test_view_mode():
    assert mermaid_live_url(CODE, mode="view").startswith("https://mermaid.live/view#pako:")


def test_unknown_serde():
    with pytest.raises(ValueError):
        serialize_state({}, "gzip")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        deserialize_state("gzip:abc")


def test_ink_urls():
    svg = mermaid_ink_url(CODE)
    assert svg.startswith("https://mermaid.ink/svg/pako:") and "?" not in svg
    png = mermaid_ink_url(CODE, fmt="img", image_type="png", bg_color="!white", width=800)
    assert png.startswith("https://mermaid.ink/img/pako:")
    assert png.endswith("?type=png&bgColor=!white&width=800")
    state = deserialize_state(png.split("/img/")[1].split("?")[0])
    assert state["code"] == CODE


def test_kroki_url():
    url = kroki_url(CODE, "png")
    assert url.startswith("https://kroki.io/mermaid/png/")
    assert pako_decode(url.rsplit("/", 1)[1]) == CODE
