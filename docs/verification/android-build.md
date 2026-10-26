# Android build evidence — issue #1

Initial Linux x86_64 validation on 2026-10-26, before later feature commits.
Synthetic demo only. The initial artifact hash/target below are historical; see
the final checkpoint at the end for the current build.

- Java: Temurin 17.0.17+10; Gradle 8.7; Android plugin 8.6.1.
- Platform 35; build-tools 35.0.0; NDK 27.2.12479018; CMake 3.22.1.
- `sh scripts/test_local.sh`: four Python parser tests, core/API tests and terminal host smoke passed.
- `cd android && gradle --no-daemon --console=plain assembleDebug`: passed without a cloud-specific init script.
- APK: `android/app/build/outputs/apk/debug/app-debug.apk`, 1634723 bytes.
- SHA256: `d8ebdd5c13fbc81933e72cd0f25be6cb22bc98166d611624eacd1e7f9490a09f` (local debug signing; not a reproducible-release digest).
- Package `org.missionthunderbolt.prototype`, version `0.1-research` / code 1; min API 23, target API 28, compile API 35.
- Packaged native ABIs: arm64-v8a, armeabi-v7a, x86, x86_64.
- `apksigner verify`: passed. Build success does not establish installation or gameplay correctness.

## Changes and remaining acceptance criteria

The workflow remains **manual-only** to conserve Actions credits, per AGENTS.md.
Command-line tools are pinned to 19.0 with Google's published archive checksum;
NDK, CMake and build-tools are now selected in the application build configuration,
not merely installed and silently replaced by plugin defaults. Manual jobs run the
native checks and upload the APK plus SHA256 after signature and package checks.

The historical failed CI run is [40402366349](https://github.com/pizzaexperiments/missionthunderbolt/actions/runs/40402366349).
Its detailed logs were unavailable without GitHub authentication. No new CI run
was triggered and no green CI run or uploaded artifact is claimed. Those issue #1
acceptance criteria remain pending; GitHub API access is currently blocked by
environment policy. Device/emulator results are recorded separately when exercised.

For #2, a fresh export of tracked source (`git archive HEAD`, without Gradle,
CMake or APK outputs) also passed `gradle --no-daemon --console=plain assembleDebug`
on Linux x86_64, with 41 tasks executed. Existing downloaded dependency caches were
reused. This verifies the source build from clean project directories, not
Windows/macOS, a cold dependency cache, or device execution.

## Current feature checkpoint

The current debug APK targets API 35, is 4335329 bytes, and has
SHA256 `e7220b1441970ec92af6acec2076c7e87ca435bd6f5bc47cdc6e58e0b23cd43a`. A local review copy is
`dist/mission-thunderbolt-research-debug.apk`. Native ELF machine headers confirm
all four listed ABIs. No original asset directory is packaged. Debug-signature
verification passes. Unsigned `assembleRelease bundleRelease` also passes release
lint after the target-35 fix. These are local artifacts, not an Actions upload or
a signed public release. See [runtime evidence](../ANDROID_RUNTIME.md) for measured
API 23 tests and the failed API 35 environment checks.
