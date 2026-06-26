# Releasing fungeom

The version is **derived from git tags** ([hatch-vcs](https://github.com/ofek/hatch-vcs)): a
`vX.Y.Z` tag *is* the version — there is nothing to bump in `pyproject.toml`. Pushing the tag runs
[`.github/workflows/release.yml`](.github/workflows/release.yml), which builds the sdist + wheel and
publishes them to PyPI via **Trusted Publishing** (OIDC — no API token is stored anywhere).

## One-time setup (PyPI Trusted Publishing)

This must be done once before the first release, by someone with PyPI access:

1. Sign in at <https://pypi.org>. (For a first publish of a brand-new project, use the
   **pending publisher** flow: <https://pypi.org/manage/account/publishing/>.)
2. Add a GitHub Actions trusted publisher with **exactly** these values:
   - **PyPI Project Name:** `fungeom`
   - **Owner:** `ryanrudes`
   - **Repository name:** `fungeom`
   - **Workflow name:** `release.yml`
   - **Environment name:** `pypi`
3. (Recommended) In the GitHub repo, create an **Environment** named `pypi`
   (Settings → Environments) and add protection rules — e.g. require a reviewer, or restrict it to
   `v*` tags — so a publish can't run unattended.

To rehearse without touching real PyPI, repeat the above on <https://test.pypi.org> and temporarily
point the publish step at TestPyPI (`with: repository-url: https://test.pypi.org/legacy/`).

## Cutting a release

1. Make sure `main` is green and update the `## [Unreleased]` section of
   [`CHANGELOG.md`](CHANGELOG.md) (rename it to the new version; via a normal PR, since `main` is
   protected).
2. Tag the merge commit and push the tag:

   ```bash
   git checkout main && git pull
   git tag v0.1.0       # SemVer; must match the v*.*.* pattern
   git push origin v0.1.0
   ```

3. The **Release** workflow builds, validates (`twine check`), and publishes to PyPI. Watch it:

   ```bash
   gh run watch
   ```

4. Verify: `pip install fungeom==0.1.0` (or check <https://pypi.org/project/fungeom/>).

## Notes

- **Never** publish by hand from a laptop — the workflow is the only path, so every release is built
  from a clean checkout of a tagged commit and is reproducible.
- CI builds and `twine check`s the package on every push/PR (the `build` job), so packaging breakage
  surfaces long before release.
- A version like `0.1.dev3+g<sha>` from an untagged checkout is expected; only a clean tag yields a
  release version.
