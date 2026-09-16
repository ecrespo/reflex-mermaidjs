# Security Policy

## Supported versions

The latest released version on PyPI receives security fixes.

## Reporting a vulnerability

Report privately via [GitHub Security Advisories][advisories] — please do not
open a public issue for an unfixed vulnerability. Expect an initial response
within 7 days.

[advisories]: https://github.com/ecrespo/reflex-mermaidjs/security/advisories/new

## Threat model for this component

`reflex-mermaidjs` renders diagram source into SVG **in the browser** and mounts
the result with `dangerouslySetInnerHTML`. That mount is safe only because
mermaid sanitises its own output first, so the `security_level` prop is the
control that matters:

| `security_level` | Behaviour |
| --- | --- |
| *(unset)* | Falls through to mermaid's own default, `strict`. **Recommended.** |
| `strict` | HTML labels and click handlers are disabled; tags are escaped. |
| `antiscript` | HTML allowed, `<script>` stripped. |
| `loose` | HTML labels and `click` directives execute. **Unsafe for untrusted input.** |
| `sandbox` | Renders inside an iframe; the strongest isolation, but pan/zoom and events are limited. |

Practical guidance:

- Leave `security_level` unset when the diagram source can come from anyone but
  you. The default is the safe one.
- Only set `security_level="loose"` for diagram source you author yourself.
  Combined with `html_labels=True` it lets diagram text inject arbitrary markup
  into your page.
- Use `security_level="sandbox"` when you must accept untrusted source *and*
  want HTML labels.
- `theme_css` is injected into the diagram's stylesheet; treat it as trusted
  input and never bind it directly to user-supplied data.

## Automated checks

Every push and pull request runs the `Security` workflow: gitleaks (secrets),
bandit and semgrep (SAST over both the Python package and the bundled JSX
renderer), pip-audit (known CVEs in the locked dependency set), and GitHub's
dependency review. It also re-runs weekly so newly disclosed CVEs surface
without needing a push.
