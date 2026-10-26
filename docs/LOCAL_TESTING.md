# Local validation and resource research

This repository contains a **synthetic demo**, not recovered original gameplay.

With Python 3, C++17 compiler and POSIX shell run:
```sh
sh scripts/test_local.sh
./dist/mt_desktop_demo
```
The script runs the current synthetic Python suite, private-input index guard,
core/API/save/mutation C++ tests and a terminal-host smoke check. Root CMake/CTest
also exercises a real C client; see [quality gates](QUALITY.md) for sanitizer and
coverage commands.

To audit game resources you legitimately possess, put extracted `.rsrc` forks locally under `local-generated/resource_forks/` (ignored by Git), then:
```sh
python3 scripts/audit_resources.py local-generated/resource_forks --output local-generated/resource_manifest.csv
```
The report contains type/ID/size/PICT dimensions/SHA256 metadata only. It **does not decode PICT pixels** and does not disassemble CODE.

**APK status:** local debug and unsigned release APK/AAB builds passed; the
synthetic debug app installed/launched and passed API 23 emulator checks. See
[Android development](ANDROID_DEVELOPMENT.md) and [runtime evidence](ANDROID_RUNTIME.md)
for exact versions, counts and limitations. CI remains manual-only to conserve credits.

Never publish original game archives, code segments, art, audio, or derivatives without confirming redistribution permission.

## Manual/RNG increment — 2026-10-26

`sh scripts/test_local.sh` passed 41 Python tests and native core/API/save/mutation,
manual-WAIT and research-RNG regressions. With the activated SDK CMake toolchain,
`cmake --build dist/sanitizers --parallel 4` plus CTest passed **7/7** ASan/UBSan
tests; the SDL build/CTest passed **8/8**, including queued WAIT input. An initial
shell lacked CMake on PATH; activating the documented toolchain resolved that
setup failure before these results.

The WAIT debug/test APK build passed. Android instrumentation passed **8 tests**
on API 23 x86_64, font scale 1.0, portrait, target SDK 35. The subsequent lifecycle
smoke preserved turns across process death and three background cycles with a
clean app crash buffer. Earlier 1.3× font/landscape results cover the prior seven-
test suite; they are not results for the new eighth test. Physical ARM64, API 35
runtime and native Windows/macOS remain unverified. See [manual rules](MANUAL_RULES.md)
and [isolated RNG evidence](RNG_RESEARCH.md) for scope and unresolved fidelity.

The current WAIT-enabled debug APK is `dist/mission-thunderbolt-research-debug.apk`,
SHA256 `0a43671dbd1b0a3a3e1bdb7ecc3490c87e40eb0feccfe5be058e32d30d9df48f`.
It is a debug-signed synthetic research demo, not a release build.
