# Release preparation — issue #23

The maintainer selected **MIT** for newly written project code. LICENSE and
THIRD_PARTY_NOTICES.md do not relicense historical assets or dependencies. Public
packages remain synthetic-only unless separate rights evidence is reviewed.

## Local review metadata

After committing reviewed source and producing the intended artifacts:

```sh
python3 scripts/prepare_release.py --version research-0.1 \
  --artifact android/app/build/outputs/apk/debug/app-debug.apk \
  --output dist/release-review \
  --apksigner "$ANDROID_HOME/build-tools/35.0.0/apksigner"
```

This requires a clean tracked source tree and refuses existing output folders,
missing/duplicate artifacts and obvious private/unsafe archive paths. It creates
SHA256SUMS, review JSON and an SPDX 2.3 **artifact inventory**, with project license
and source checkout metadata. It does not copy/publish artifacts by itself.
An APK signature is verified only when apksigner is supplied. A valid debug
signature is not a release signing approval. A source checkout hash alone does
not attest that a binary was built from it.

This inventory is **not a complete dependency SBOM**: inspect packaged runtimes,
NDK libc++/LLVM notices, Gradle/runtime dependencies and desktop vcpkg package
metadata, add exact component licenses/versions and preserve notices before
public distribution. A path guard cannot recognize renamed proprietary content.
Review source, assets, license provenance, test reports and actual package contents.

## Tagged signed Android review workflow

The manual-only `release-preparation.yml` checks an existing tag, builds
`assembleRelease` and `bundleRelease`, signs APK/AAB and verifies both. It uses a
GitHub environment named `release-preparation`; maintainers should configure its
review controls and secure signing bindings **in GitHub**, not chat or Git:

- `ANDROID_KEYSTORE_BASE64` — encoded keystore (encoding is not encryption).
- `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`.

The workflow reads passwords through environment references rather than shell
arguments containing literal secret values; the temporary keystore has restricted
permissions and is removed after signing. It uploads a review artifact only and
has no release-publishing step. Keep the original signing key backed up privately;
never substitute a debug key and label it a production release.

No signing key/bindings were supplied or inspected in this task. The workflow
has not run, no tag was created, and no signed release was published. Unsigned
release APK/AAB build validation is separate from signing and device acceptance.

Desktop review packages are prepared by desktop.yml; Windows/macOS native checks
and macOS signing/notarization remain pending (DESKTOP_DEVELOPMENT.md). Maintain
an accurate changelog, source/tag correspondence, checksums and a complete notices/
SBOM review before a maintainer chooses to publish anything. The Android target was raised to API 35 after release lint rejected API 28;
store-policy eligibility still requires a separate current-policy review.


## Current validation checkpoint

Local `gradle --no-daemon assembleRelease bundleRelease` passed release lint and
produced unsigned APK/AAB after the target-35 fix. The review-metadata tool's
synthetic tests passed, including private-path and dirty-source rejection; its
SPDX document was validated with jsonschema 4.25.1 against the official SPDX 2.3
JSON schema. The workflow repeats that schema validation and preserves Android
NDK/toolchain notices. Desktop jobs accept an optional existing reviewed tag as
well as their normal selected workflow ref. None of these remote jobs ran here.
