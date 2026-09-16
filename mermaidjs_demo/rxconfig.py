import reflex as rx

config = rx.Config(
    app_name="mermaidjs_demo",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(accent_color="pink", gray_color="slate", radius="large"),
        ),
    ],
)
