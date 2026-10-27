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

## RNG initialization, timed sound and map accessibility increment

The private initializer oracle passed **37 initializers, 2,368 continued draws
and 12 low-memory accessor cases**; **2,405 complete C++/68000 state comparisons**
matched. The normal test script and sanitizer/SDL suites passed (45 Python,
7 ASan/UBSan, 8 SDL). Python statement coverage is **86%**, above the 80% gate.
The sound catalog returned expected exit 2: 137 single-buffer conversions and
one explicitly sample-only preview with retained timed commands; no malformed
resources. Complete timed playback is still unimplemented.

Android debug/test APK builds, debug lint and unsigned release APK/AAB builds
passed. The current **12 Android instrumentation tests** and subsequent lifecycle
process-death/three-background-cycle smoke passed on API 23 x86_64, normal font,
portrait, target SDK 35. The framework accessibility-tree readiness failure and
its tested harness correction are recorded in ANDROID_RUNTIME.md. This is not
physical TalkBack usability, API 35 runtime or original-game verification.

Updated accessibility-enabled debug demo: `dist/mission-thunderbolt-research-debug.apk`,
SHA256 `c591ca1bf008af08d086ab48f7d96073457baa4d1f2e9ff049970789035123fe`.
The earlier WAIT-only APK hash above describes the earlier checkpoint.

The optional Atheris 3.1.0 synthetic parser campaign completed 1,722,666 executions
in 121 seconds, with no failure artifacts and 71 MB peak RSS. Reproduction and
limits are recorded in QUALITY.md; this is not original-game differential coverage.

## Grid-helper and selector increment — 2026-10-27

The original-instruction/native comparisons passed 120 pointer-builder cases
(152,760 cell addresses), all 65,536 coordinate byte pairs, 2,048 candidate-gate
probes and 105 selector/RNG cases. Selector outcomes were 29 direct, 36 neighbor
and 40 stopped before the unresolved fallback. Source fingerprints, synthetic
allocator/direction inputs, exact commands and limits are recorded in
[GRID_RESEARCH.md](GRID_RESEARCH.md). A real Ghidra synthetic fixture also verified
the new exact-A5 filter: two direct references accepted, alias/indexed references
excluded. Original output remains private.

`sh scripts/test_local.sh` passed 45 Python tests and the native regressions.
CMake/CTest passed **9/9 ASan/UBSan** and **10/10 SDL** checks. The parser Python
source is unchanged; its last measured statement coverage remains 86%. These new
research headers are exercised by standalone tests and are not connected to the
active demo engine. Android/desktop host application logic was not changed, and
no new Android/device verification is claimed for this increment. The existing
APK, signing and physical-device limitations above remain applicable.

## GitHub connection and closeout — 2026-10-27

The authenticated API returned HTTP 200 for this repository, and creating draft
PR #26 plus issue evidence comments/closures succeeded. Issues #4, #24 and #25
were confirmed closed as completed after refreshing their live bodies/comments.
The environment's older policy snapshot did not reflect the working API route.
Existing credentials were reused. No code or test behavior changed for closeout;
previous local verification remains the evidence. No Actions run or merge occurred.
