# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-10-24

### Changed

- Require `reflex>=0.10.0` (previously `>=0.9.11`); the demo app's
  `requirements.txt` follows.
- Build backend requires `setuptools>=78.1.1`.
- Lockfile refreshed against Reflex 0.10.0; the demo's frontend lock now
  resolves React 19.3, React Router 8.4 and Vite 8.3.
- Ruff targets `py311`.

### Removed

- **Python 3.10 support.** Reflex 0.10 requires Python 3.11+, so
  `requires-python` is now `>=3.11`, the 3.10 classifier is gone and CI tests
  3.11 – 3.13.

## [0.1.0] - 2026-09-15

### Added

- First release: mermaid 12.0.0 component with typed config props, dark
  appearance, pan & zoom toolbar, events, Python actions (zoom, fit, export,
  copy, get SVG), Iconify / Font Awesome icons, KaTeX math, `rx.markdown`
  integration, share-URL helpers and 36 sample diagram types.

[0.2.0]: https://github.com/ecrespo/reflex-mermaidjs/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/ecrespo/reflex-mermaidjs/releases/tag/v0.1.0
