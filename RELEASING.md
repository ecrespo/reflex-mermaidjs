# Releasing

Releases are fully automated by `.github/workflows/release.yml`. Pushing a
`v*.*.*` tag builds, gates, publishes to PyPI and cuts a GitHub release.
No API token is stored anywhere — PyPI authenticates the workflow over OIDC.

## One-time setup

### 1. Register the Trusted Publisher on PyPI

Already done: `reflex-mermaidjs` has been on PyPI since v0.1.0 and its
Trusted Publisher is active. The values below are kept for reference (e.g. if
the workflow file or environment is ever renamed). Go to
<https://pypi.org/manage/account/publishing/> and fill in:

| Field | Value |
| --- | --- |
| PyPI Project Name | `reflex-mermaidjs` |
| Owner | `ecrespo` |
| Repository name | `reflex-mermaidjs` |
| Workflow name | `release.yml` |
| Environment name | `pypi` |

The environment name is not optional here — `release.yml` runs its publish job
in the `pypi` environment, and PyPI rejects the OIDC token if the claim does not
match what is registered.

For a brand-new project this is registered as a *pending* publisher, which PyPI
converts into a normal one when the first release uploads.

### 2. Create the `pypi` environment on GitHub

Settings → Environments → **New environment** → name it `pypi`.

Adding a *required reviewer* there is recommended: it turns every publish into
something a human approves in the Actions UI, which is the only practical undo
for an upload that cannot be deleted.

## Cutting a release

```bash
# 1. Bump the version — pyproject.toml is the single source of truth.
uv version --bump patch        # or: minor | major | X.Y.Z

# 2. Verify locally with the same gate CI runs.
uv sync --all-groups
uv run ruff check . && uv run ruff format --check .
uv run pytest
uv run bandit -c pyproject.toml -r . -ll
uv build && uvx twine check --strict dist/*

# 3. Commit on a branch and open a PR — `main` is protected.
git switch -c release/v$(uv version --short)
git commit -am "release: v$(uv version --short)"
git push -u origin HEAD
gh pr create --base main --fill

# 4. Once CI is green and the PR is merged, tag the merge commit on main.
git switch main && git pull --ff-only
git tag "v$(uv version --short)"
git push origin "v$(uv version --short)"
```

Record the release in [CHANGELOG.md](CHANGELOG.md) as part of step 1.

The workflow then:

1. refuses to continue if the tag does not match `pyproject.toml`;
2. re-runs lint, tests, bandit and the metadata check;
3. builds the sdist + wheel;
4. publishes to PyPI with `uv publish --trusted-publishing always`;
5. creates the GitHub release with the artifacts attached and generated notes.

### Rehearsing without publishing

Run the workflow manually from the Actions tab with **dry_run** left checked.
It performs every step up to and including the build and metadata check, then
stops before the publish and release jobs.

## Type stubs

`custom_components/reflex_mermaidjs/mermaidjs.pyi` is committed and shipped as
is. Regenerate it whenever the component's props change:

```bash
uv run python -m reflex_base.utils.pyi_generator custom_components/reflex_mermaidjs
```

This replaces `reflex component build`, which Reflex 0.10 removed together
with the rest of the `reflex component` CLI.

## Reflex gallery

`reflex component share` was removed in Reflex 0.10 and there is no CLI
replacement. The gallery tracks the package name rather than a version, so an
already-registered package needs nothing per release; for a new listing, see
the current Reflex documentation.

## Notes

- PyPI never lets a version be re-uploaded, and a yanked version still occupies
  the number. Every release needs a fresh version.
- A version can be yanked but not deleted, and the project name is claimed
  permanently. Treat the publish step as irreversible.
