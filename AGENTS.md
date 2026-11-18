# qvac-conda
Conda packaging for QVAC.

`prebuilt/` repackages official SDK binary wheels and builds its pure Python
dependencies from PyPI source distributions. Future recipes that compile QVAC
from source will live in a separate directory.

The `tetherto-qvac-sdk` recipe starts at [SDK v0.23.0](https://github.com/tetherto/qvac/releases/tag/sdk-v0.23.0)
and includes the bundled worker and Bare runtime. It supports Python 3.10–3.14 on
Linux x86-64 and ARM64 (glibc >=2.35), Apple Silicon (macOS >=13), and Windows
x86-64. The Python-only `bare-rpc`, `bare-stow-host`, and `compact-encoding`
dependencies are also packaged, alongside the platform-specific `bare-sidecar`
wheels that provide the Bare runtime.

After publication, install with:

```sh
pixi workspace channel add --prepend https://prefix.dev/gbionics/qvac-prebuilt
pixi add tetherto-qvac-sdk
# Or:
conda install -c https://prefix.dev/gbionics/qvac-prebuilt -c conda-forge tetherto-qvac-sdk
```

Build locally with [rattler-build](https://github.com/prefix-dev/rattler-build)
(CI uses v0.68.0):

```sh
rattler-build build --recipe prebuilt/compact-encoding -m prebuilt/variants.yaml -c conda-forge
rattler-build build --recipe prebuilt/bare-rpc -m prebuilt/variants.yaml -c conda-forge
rattler-build build --recipe prebuilt/bare-stow-host -m prebuilt/variants.yaml -c conda-forge
rattler-build build --recipe prebuilt/bare-sidecar -m prebuilt/variants.yaml -c conda-forge
rattler-build build --recipe prebuilt/tetherto-qvac-sdk -m prebuilt/variants.yaml -c conda-forge
```

The local `output/` channel is automatically searched for these dependencies.
All recipes live directly under `prebuilt/`. Pass `-m prebuilt/variants.yaml`
to load the shared Python minimum. Pure Python recipes
follow the [conda-forge noarch conventions](https://conda-forge.org/docs/maintainer/example_recipes/pure-python/)
and test the minimum and latest Python.
Pure Python recipes build the sdists with hatchling and use their bundled licenses
and notices. The SDK fetches the matching Apache license and QVAC notice from
`packages/inference` at the SDK release tag, with pinned checksums; its stowed
worker wheel no longer contains loose license files. `bare-sidecar` extracts
its bundled license and notice from the platform wheel.
The SDK builds once per platform with Python 3.10, using
`build.python.version_independent: true` and a runtime dependency on `python >=3.10`.
The wheel's Python client uses no CPython C API, so no `python-abi3` dependency
is needed. The SDK package stays platform-specific because it contains native
worker addons; the Bare runtime lives in the platform-specific `bare-sidecar`
package. The same package is tested on Python 3.10–3.14,
with the Bare smoke tests running on Python 3.10. CI builds four SDK and four
`bare-sidecar` packages per release, one of each per platform.
Each build tests Python imports, dependency metadata (`pip check`), and execution
of the bundled Bare runtime. These checks do not download models or exercise GPU
inference. Upstream binaries retain their loader paths and macOS signatures.
On Linux, the build also runs `check-glibc` from `cf-nvidia-tools` against every
installed ELF file, including native addons, and the sidecar build checks Bare.
The `c_stdlib_version` environment variable comes from `minimum_glibc`, the same
value used for each recipe's `__glibc` runtime constraint (2.35 for the SDK, 2.34
for `bare-sidecar`). A binary requiring newer glibc fails the build.

`.github/workflows/prebuilt.yml` builds on pull requests, pushes to `main`, and
manual dispatch. After all platform builds pass, runs on `main` publish the
packages to [`gbionics/qvac-prebuilt`](https://prefix.dev/channels/@gbionics/qvac-prebuilt).
Publishing uses prefix.dev trusted publishing with GitHub OIDC: repository
`gbionics/qvac-conda`, workflow `prebuilt.yml`, environment `production`, matching
the channel's repository access configuration. No API key is required; existing
package files are skipped on reruns. Runs on other branches build and test only.

`.github/workflows/update-prebuilt.yml` checks upstream every night at 02:23 UTC
and can also be run manually. It selects the highest stable `sdk-vX.Y.Z` release,
updates all four wheel filenames and SHA-256 hashes, derives minimum OS versions
from the wheel tags, and resets the build number. A missing or ambiguous platform
wheel fails the update instead of creating an incomplete recipe. Older releases
without API checksums are downloaded and hashed. Dependency and license changes
still require review of the update PR.

Updates use one reusable PR branch, `automation/update-prebuilt-sdk`. In GitHub's
repository Actions settings, enable **Allow GitHub Actions to create and approve
pull requests**. The updater uses `GITHUB_TOKEN` and explicitly dispatches the
build workflow on the PR branch, since token-created PRs do not start PR workflows.
The updater and scheduled jobs become available once merged into the default branch.

To check the updater locally without modifying the recipe:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/update_prebuilt.py --dry-run
```

For packaging changes at the same upstream version, increment `build_number` in
the SDK recipe (or `build.number` for a dependency) before publishing again.
Repository code is BSD-3-Clause; the repackaged distributions carry their upstream
Apache-2.0 licenses and notices.
