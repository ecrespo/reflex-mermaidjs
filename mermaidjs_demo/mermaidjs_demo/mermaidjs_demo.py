"""reflex-mermaidjs demo: a mermaid.live-style editor built with Reflex."""

import reflex as rx

from .api import api_page
from .editor import editor_page
from .features import features_page
from .gallery import gallery_page

# The Radix theme is configured via `rx.plugins.RadixThemesPlugin(theme=...)`
# in `rxconfig.py` (App(theme=...) is deprecated since Reflex 0.9.0).
app = rx.App(
    stylesheets=["https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap"],
)
app.add_page(editor_page, route="/", title="Mermaid × Reflex Live Editor")
app.add_page(gallery_page, route="/gallery", title="Gallery · reflex-mermaidjs")
app.add_page(features_page, route="/features", title="Features · reflex-mermaidjs")
app.add_page(api_page, route="/api", title="API · reflex-mermaidjs")
