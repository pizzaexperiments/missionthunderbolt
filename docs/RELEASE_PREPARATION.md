# Release preparation — issue #23

GitHub Actions is currently [paused](../.github/ACTIONS_PAUSED.md), including
manual dispatch. Use local commands and post results in the PR.

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

## Android native dependency evidence

Build release inputs with `gradle --no-daemon assembleRelease bundleRelease
exportReleaseRuntimeDependencies` from `android/`. CMake emits private lld maps
for each ABI. The Gradle report includes resolved modules **and artifacts**, so
local-file dependencies cannot disappear from the check. Then from the repo root:

```sh
python3 scripts/android_dependency_evidence.py \
  --artifact android/app/build/outputs/apk/release/app-release-unsigned.apk \
  --artifact android/app/build/outputs/bundle/release/app-release.aab \
  --ndk "$ANDROID_HOME/ndk/27.2.12479018" \
  --runtime-report android/app/build/reports/release-runtime-dependencies.json \
  --build-root android/app/.cxx/RelWithDebInfo \
  --output dist/android-dependencies.json
python3 scripts/prepare_release.py --version research-review \
  --artifact android/app/build/outputs/apk/release/app-release-unsigned.apk \
  --artifact android/app/build/outputs/bundle/release/app-release.aab \
  --dependency-evidence dist/android-dependencies.json \
  --output dist/release-review
```

The collector matches packaged ELF build IDs and dynamic dependencies to the
linked build outputs, hashes every listed contributing NDK archive and both
NDK notices, and records per-member/artifact hashes. New Java runtime modules or
artifacts, non-NDK static archives, unknown native libraries, duplicate/stale ABI
maps, missing build IDs and mismatched packages fail collection. Delete stale
project build outputs or supply explicit `--build-dir` arguments if multiple
CMake configurations remain; the tool does not silently select one. Paths with
whitespace in linker maps are not supported by this initial parser.

Release preparation rejects dependency evidence for different artifact hashes,
copies the evidence into the review directory, and adds SPDX archive packages
with `STATIC_LINK` relationships. The namespace includes dependency evidence.
Archive licenses remain `NOASSERTION`: a composite NDK notice is not sufficient
to infer individual package licenses automatically. This improves the inventory;
it does not yet complete #23's transitive license/notices review or desktop SBOM.
OS libraries libc/libdl/libm are recorded as platform requirements, not bundled
packages. Build-tool dependencies are outside this runtime inventory.

The manual signing workflow now collects evidence **after signing**, so inventory
hashes describe the signed review artifacts. That workflow remains unrun.
Local unsigned APK/AAB collection passed on all four ABIs, identifying four
runtime archives per ABI (libc++, libc++abi, libunwind, compiler-rt), with no Java
runtime dependencies. Build-ID checks are useful correspondence evidence, not
a cryptographic attestation of a trustworthy or reproducible build.
