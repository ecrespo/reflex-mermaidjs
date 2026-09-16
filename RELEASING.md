# Releasing

Releases are fully automated by `.github/workflows/release.yml`. Pushing a
`v*.*.*` tag builds, gates, publishes to PyPI and cuts a GitHub release.
No API token is stored anywhere — PyPI authenticates the workflow over OIDC.

## One-time setup

### 1. Register the Trusted Publisher on PyPI

`reflex-mermaidjs` is not on PyPI yet, so this is a **pending** publisher.
Go to <https://pypi.org/manage/account/publishing/> and fill in:

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

Once the first release uploads, the pending publisher is converted into a normal
one automatically; nothing further to do.

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

# 3. Commit, tag and push.
git commit -am "release: v$(uv version --short)"
git tag "v$(uv version --short)"
git push && git push --tags
```

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

## After the first PyPI release

Register the component in the Reflex gallery (optional, one-time):

```bash
uv run reflex login
uv run reflex component share
```

It asks for the published package name (`reflex-mermaidjs`), and optionally a
preview image and a demo URL.

## Notes

- PyPI never lets a version be re-uploaded, and a yanked version still occupies
  the number. Every release needs a fresh version.
- A version can be yanked but not deleted, and the project name is claimed
  permanently. Treat the publish step as irreversible.
