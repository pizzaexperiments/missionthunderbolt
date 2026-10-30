# Android NDK component notice evidence — issue #23

The optional `docs/android-ndk-attribution.json` manifest records the sixteen
runtime archives measured across four Android ABIs with the Linux-host
NDK 27.2.12479018 / LLVM 18.0.3 installation. All archive and upstream notice
SHA256 values were checked against the installed files. No archive bytes are
included in this document or manifest.

The manifest identifies libc++, libc++abi, compiler-rt builtins and libunwind by
exact NDK-relative archive path. For the first three, the composite
`NOTICE.toolchain` explicitly names legacy NCSA/MIT terms alongside LLVM
Apache 2.0 with LLVM Exceptions statements and a third-party caveat. The
manifest records the relevant line ranges as evidence, not an archive-wide
license expression. The installed notice does not explicitly name libunwind;
its component identity comes from the archive path, and its license attribution
remains unresolved. Nearby sections include other projects such as OpenMP;
their licenses must not be assigned to a runtime merely by section order.

Every archive retains SPDX `licenseDeclared` and `licenseConcluded` as
`NOASSERTION`. Resolving source/member-specific licensing and exceptions is
still required before distribution. Notice preservation and matching hashes do
not establish reproducible builds, legal clearance or a complete desktop SBOM.

After collecting current Android dependency evidence, add these options to the
local release preparation command in RELEASE_PREPARATION.md:

```sh
python3 scripts/prepare_release.py --version research-review \
  --artifact android/app/build/outputs/apk/release/app-release-unsigned.apk \
  --artifact android/app/build/outputs/bundle/release/app-release.aab \
  --dependency-evidence dist/android-dependencies.json \
  --attribution-manifest docs/android-ndk-attribution.json \
  --ndk "$ANDROID_HOME/ndk/27.2.12479018" \
  --output dist/release-review-attribution
```

The tracked source tree must be clean, as with other release review commands.
With this option, preparation rejects unknown archives, changed archive bytes,
NDK/LLVM version mismatches, notice hash mismatches and unsupported license
claims. It checks actual installed archive and notice bytes, copies the manifest
into the review directory, and preserves both complete, unmodified upstream
notices under `licenses/NOTICE` and `licenses/NOTICE.toolchain`. SPDX package
comments carry the matched component's notice evidence. These complete notices
also contain material for tools or components that may not be shipped; their
inclusion does not claim all listed licenses apply to the app.

A subset of the manifest's supported ABIs is allowed; every measured archive
must have exact coverage. Different host NDK distributions, NDK upgrades or new
runtime components require a new evidence review. Without these optional
arguments, the existing inventory mode remains available and reports its
component attribution as `unreviewed`. Neither mode publishes an artifact.
All GitHub Actions remain paused; this command runs locally.

## Local verification — 2026-10-30

At implementation commit `2e2f384`, `sh scripts/test_local.sh` passed **65 Python
tests plus all native smoke checks**, including nine authored attribution tests.
The focused release/dependency/attribution suite passed 15 tests. Rejections cover
stale versions/hashes, unknown archives, missing evidence and unsupported license
claims; rejected preparation leaves no partial review directory. Both optional
picture decoders were available for the full suite; no tests skipped or failed.

A real-input check collected fresh dependency evidence for the existing local
unsigned APK/AAB across four ABIs, then prepared a private review directory with
sixteen archive packages and both byte-identical upstream notices. The SPDX 2.3
JSON schema validation passed. A first attempt using an older saved report was
rejected because artifact hashes differed; fresh collection resolved that input
mismatch without weakening checks. Artifact SHA256 values:

- `app-release-unsigned.apk`: `7a2acfe3226a45b5c3b81641ca78e5275b56a4303e58b83d856d71ad6d1e4bde`
- `app-release.aab`: `ee2fc75213c49a8e7b36d5dadd656b7e41f7e6220188431e1d4e48ef8d9bd0a3`

These are existing build inputs, not new builds or proof that they were compiled
from the attribution-tool commit. Review metadata remains `review-required`,
`published: false`, with archive licenses unresolved. No signing, device test,
Actions execution, tag, merge or publication was performed.
