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
